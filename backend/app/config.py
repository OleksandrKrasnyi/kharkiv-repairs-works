"""
Конфигурация приложения с поддержкой разных сред и БД
"""

import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения"""

    # Основные настройки
    app_name: str = "Kharkiv Repairs System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(
        default="development",
        description="Environment: development, production, testing",
    )

    # Настройки сервера
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # База данных
    database_url: str | None = None
    database_type: str = Field(
        default="sqlite", description="Database type: sqlite, mysql, postgresql"
    )

    # SQLite настройки
    sqlite_database_path: str = "db/app.db"

    # MySQL настройки
    mysql_user: str | None = None
    mysql_password: str | None = None
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "kharkiv_repairs"

    # PostgreSQL настройки
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "kharkiv_repairs"

    # Внешние API
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    nominatim_timeout: int = 10

    # Безопасность
    secret_key: str = Field(
        default="your-secret-key-here", description="Secret key for JWT tokens"
    )
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "https://*.railway.app",
        "https://*.up.railway.app",
        "*",  # Для Railway деплоя - разрешаем все домены
    ]

    # Логирование
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Sentry (опционально)
    sentry_dsn: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str | None, info) -> str:
        """Собираем URL базы данных в зависимости от типа"""
        if v:
            return v

        # В Pydantic v2 нужно получить данные через info.data
        values = info.data if info else {}
        db_type = values.get("database_type", "sqlite")

        if db_type == "sqlite":
            sqlite_path = values.get("sqlite_database_path", "db/app.db")
            # Создаем директорию если её нет
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            return f"sqlite:///{sqlite_path}"

        elif db_type == "mysql":
            user = values.get("mysql_user")
            password = values.get("mysql_password")
            host = values.get("mysql_host", "localhost")
            port = values.get("mysql_port", 3306)
            database = values.get("mysql_database", "kharkiv_repairs")

            if not user or not password:
                raise ValueError("MySQL user and password must be provided")

            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

        elif db_type == "postgresql":
            user = values.get("postgres_user")
            password = values.get("postgres_password")
            host = values.get("postgres_host", "localhost")
            port = values.get("postgres_port", 5432)
            database = values.get("postgres_database", "kharkiv_repairs")

            if not user or not password:
                raise ValueError("PostgreSQL user and password must be provided")

            return f"postgresql://{user}:{password}@{host}:{port}/{database}"

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Валидация окружения"""
        allowed = ["development", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


# Глобальная переменная с настройками
settings = Settings()


def get_settings() -> Settings:
    """Получить настройки приложения"""
    return settings
