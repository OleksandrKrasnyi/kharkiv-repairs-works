"""
Pydantic схемы для валидации и сериализации данных
"""

from .repair_work import (
    RepairWorkBase,
    RepairWorkCreate,
    RepairWorkDetailed,
    RepairWorkResponse,
    RepairWorkUpdate,
    WorkStatus,
)
from .street import LocationData, StreetSearchResult
from .work_type import (
    WorkTypeBase,
    WorkTypeCreate,
    WorkTypeResponse,
    WorkTypeUpdate,
    WorkTypeWithStats,
)

__all__ = [
    # Work Types
    "WorkTypeBase",
    "WorkTypeCreate",
    "WorkTypeUpdate",
    "WorkTypeResponse",
    "WorkTypeWithStats",
    # Repair Works
    "RepairWorkBase",
    "RepairWorkCreate",
    "RepairWorkUpdate",
    "RepairWorkResponse",
    "RepairWorkDetailed",
    "WorkStatus",
    # Streets
    "StreetSearchResult",
    "LocationData",
]
