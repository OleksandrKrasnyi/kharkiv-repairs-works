"""
Конфигурация базы данных с поддержкой SQLite, MySQL и PostgreSQL
"""

from collections.abc import Generator

import structlog
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Настройка движка в зависимости от типа БД
if settings.database_type == "sqlite":
    # SQLite специфичные настройки
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug,  # Логировать SQL запросы в debug режиме
    )
elif settings.database_type == "mysql":
    # MySQL настройки
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        pool_recycle=300,  # Переиспользование соединений каждые 5 минут
        echo=settings.debug,
        pool_size=20,  # Размер пула соединений
        max_overflow=0,  # Максимальное количество дополнительных соединений
    )
elif settings.database_type == "postgresql":
    # PostgreSQL настройки
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug,
        pool_size=20,
        max_overflow=0,
    )
else:
    raise ValueError(f"Unsupported database type: {settings.database_type}")

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии базы данных
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    Создание всех таблиц в базе данных
    """
    logger.info("Creating database tables", database_type=settings.database_type)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection() -> bool:
    """
    Проверка соединения с базой данных
    """
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info(
            "Database connection successful", database_type=settings.database_type
        )
        return True
    except Exception as e:
        logger.error(
            "Database connection failed",
            error=str(e),
            database_type=settings.database_type,
        )
        return False
