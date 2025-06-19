"""
Модель ремонтной работы
"""

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .work_type import WorkType


class WorkStatus(str, enum.Enum):
    """Статус ремонтной работы"""

    PLANNED = "planned"  # Запланировано
    IN_PROGRESS = "in_progress"  # В процессе
    COMPLETED = "completed"  # Завершено
    CANCELLED = "cancelled"  # Отменено
    DELAYED = "delayed"  # Отложено


class RepairWork(Base):
    """
    Модель ремонтной работы
    """

    __tablename__ = "repair_works"

    id = Column(Integer, primary_key=True, index=True)

    # Локация (может быть одна точка или участок)
    location = Column(String(500), index=True, nullable=True)
    start_location = Column(String(500), index=True, nullable=True)
    end_location = Column(String(500), index=True, nullable=True)

    # Координаты для карты
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    start_latitude = Column(Float, nullable=True)
    start_longitude = Column(Float, nullable=True)
    end_latitude = Column(Float, nullable=True)
    end_longitude = Column(Float, nullable=True)

    # Геометрия сегмента улицы (для точного отображения)
    street_segment_geojson = Column(
        Text, nullable=True
    )  # GeoJSON геометрии выбранного сегмента
    street_name = Column(String(255), nullable=True)  # Название улицы
    street_osm_type = Column(String(20), nullable=True)  # 'way' или 'relation'
    street_osm_id = Column(String(50), nullable=True)  # OSM ID улицы

    # Информация о работе
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # Дополнительные заметки

    # Временные рамки
    start_datetime = Column(DateTime(timezone=True), index=True, nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=True)
    planned_duration_hours = Column(
        Integer, nullable=True
    )  # Планируемая продолжительность в часах

    # Статус работы
    status = Column(
        Enum(WorkStatus), default=WorkStatus.PLANNED, nullable=False, index=True
    )

    # Связь с типом работ
    work_type_id = Column(
        Integer, ForeignKey("work_types.id"), nullable=True, index=True
    )
    work_type: Mapped[Optional["WorkType"]] = relationship(
        "WorkType", back_populates="repair_works"
    )

    # Метаданные
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<RepairWork(id={self.id}, status='{self.status}', start='{self.start_datetime}')>"

    def __str__(self):
        location = self.location or f"{self.start_location} - {self.end_location}"
        return f"Ремонт {location} ({self.status})"

    @property
    def is_point_work(self) -> bool:
        """Проверка, является ли работа точечной (не участком)"""
        return bool(self.location and not (self.start_location and self.end_location))

    @property
    def is_segment_work(self) -> bool:
        """Проверка, является ли работа на участке"""
        return bool(self.start_location and self.end_location)

    @property
    def display_location(self) -> str:
        """Отображаемая локация"""
        if self.is_point_work:
            return self.location
        elif self.is_segment_work:
            return f"{self.start_location} - {self.end_location}"
        return "Не указана"

    @property
    def has_coordinates(self) -> bool:
        """Проверка наличия координат"""
        if self.is_point_work:
            return bool(self.latitude and self.longitude)
        elif self.is_segment_work:
            return bool(
                self.start_latitude
                and self.start_longitude
                and self.end_latitude
                and self.end_longitude
            )
        return False
