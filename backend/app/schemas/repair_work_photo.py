"""
Схемы для фотографий ремонтных работ
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RepairWorkPhotoBase(BaseModel):
    """Базовая схема фотографии"""
    
    description: Optional[str] = None
    sort_order: int = 0


class RepairWorkPhotoCreate(RepairWorkPhotoBase):
    """Схема для создания фотографии"""
    
    repair_work_id: int
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class RepairWorkPhotoUpdate(BaseModel):
    """Схема для обновления фотографии"""
    
    description: Optional[str] = None
    sort_order: Optional[int] = None


class RepairWorkPhoto(RepairWorkPhotoBase):
    """Схема фотографии для ответа"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    repair_work_id: int
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RepairWorkPhotoList(BaseModel):
    """Схема для списка фотографий"""
    
    photos: list[RepairWorkPhoto]
    total: int 