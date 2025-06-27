"""
Главный модуль FastAPI приложения
"""

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import check_db_connection, create_tables
from .routers import repair_works, repair_work_photos, streets, work_types
from .utils.exceptions import BaseAPIException

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application"""
    # Startup
    logger.info("Starting application", environment=settings.environment)

    # Проверяем соединение с БД
    if not check_db_connection():
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")

    # Создаем таблицы
    create_tables()

    # Создание необходимых директорий
    os.makedirs("frontend/static/css", exist_ok=True)
    os.makedirs("frontend/static/js", exist_ok=True)

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Создание приложения
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API для управления ремонтными работами в Харькове",
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Обработчики ошибок
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Обработчик кастомных исключений API"""
    logger.error(
        "API Exception",
        exception_type=type(exc).__name__,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "type": type(exc).__name__,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик общих исключений"""
    logger.error(
        "Unhandled Exception",
        exception_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Внутренняя ошибка сервера",
            "details": {} if settings.is_production else {"exception": str(exc)},
            "type": "InternalServerError",
        },
    )


# Подключение роутеров
app.include_router(work_types.router, prefix="/api/v1/work-types", tags=["Work Types"])

app.include_router(
    repair_works.router, prefix="/api/v1/repair-works", tags=["Repair Works"]
)

app.include_router(repair_work_photos.router, tags=["Repair Work Photos"])

app.include_router(streets.router, prefix="/api/v1/streets", tags=["Streets"])


# Статические файлы (только если директории существуют)
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

if os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")


# Health check (ВАЖНО: должен быть ПЕРЕД fallback роутом)
@app.get("/health", tags=["System"])
async def health_check():
    """Проверка состояния системы"""
    db_status = check_db_connection()

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "environment": settings.environment,
        "version": settings.app_version,
    }


# Главная страница (только в продакшене)
@app.get("/", include_in_schema=False)
async def read_root():
    """Главная страница приложения"""
    if settings.is_production and os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    else:
        return {
            "message": "Kharkiv Repairs API",
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs" if settings.is_development else "disabled",
            "health": "/health"
        }


# SPA fallback - возвращаем index.html для всех неизвестных путей
# ВАЖНО: Должен быть ПОСЛЕДНИМ среди GET роутов!
@app.get("/{path:path}", include_in_schema=False)
async def spa_fallback(path: str):
    """Fallback для Vue Router - возвращает index.html для клиентских роутов"""
    # Проверяем, что путь не начинается с /api/, /static/, /assets/, /health, /docs, /redoc
    if not (
        path.startswith("api/") or
        path.startswith("static/") or 
        path.startswith("assets/") or
        path in ["health", "docs", "redoc", "openapi.json"]
    ):
        # Возвращаем index.html только в продакшене
        if settings.is_production and os.path.exists("frontend/dist/index.html"):
            return FileResponse("frontend/dist/index.html")
    
    # Для остальных путей возвращаем 404
    return JSONResponse(
        status_code=404,
        content={"error": True, "message": "Not found"}
    )


# Информация о системе (только в dev режиме)
if settings.is_development:

    @app.get("/info", tags=["System"])
    async def system_info():
        """Информация о системе (только для разработки)"""
        return {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
            "database_type": settings.database_type,
            "python_version": "3.11+",
        }
