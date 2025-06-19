"""
Кастомные исключения для API
"""

from typing import Any


class BaseAPIException(Exception):
    """Базовое исключение для API"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFoundError(BaseAPIException):
    """Сущность не найдена"""

    def __init__(
        self,
        message: str = "Сущность не найдена",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=404, details=details)


class DuplicateEntityError(BaseAPIException):
    """Дублирование сущности"""

    def __init__(
        self,
        message: str = "Сущность уже существует",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=409, details=details)


class ValidationError(BaseAPIException):
    """Ошибка валидации"""

    def __init__(
        self,
        message: str = "Ошибка валидации данных",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=422, details=details)


class BusinessLogicError(BaseAPIException):
    """Ошибка бизнес-логики"""

    def __init__(
        self,
        message: str = "Ошибка бизнес-логики",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=400, details=details)


class ExternalServiceError(BaseAPIException):
    """Ошибка внешнего сервиса"""

    def __init__(
        self,
        message: str = "Ошибка внешнего сервиса",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=503, details=details)


class AuthenticationError(BaseAPIException):
    """Ошибка аутентификации"""

    def __init__(
        self,
        message: str = "Ошибка аутентификации",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(BaseAPIException):
    """Ошибка авторизации"""

    def __init__(
        self,
        message: str = "Недостаточно прав доступа",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code=403, details=details)
