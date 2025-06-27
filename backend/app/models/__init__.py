"""
Модели базы данных
"""

from .repair_work import RepairWork, WorkStatus
from .repair_work_photo import RepairWorkPhoto
from .work_type import WorkType

__all__ = ["WorkType", "RepairWork", "WorkStatus", "RepairWorkPhoto"]
