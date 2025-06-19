"""
Утилиты и вспомогательные функции
"""

from .exceptions import (
    BaseAPIException,
    BusinessLogicError,
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)

__all__ = [
    "BaseAPIException",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "BusinessLogicError",
    "ValidationError",
]
