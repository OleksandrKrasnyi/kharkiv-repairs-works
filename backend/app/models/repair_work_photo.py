"""
Модель фотографий ремонтной работы
"""

from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .repair_work import RepairWork


class RepairWorkPhoto(Base):
    """
    Модель фотографии ремонтной работы
    """

    __tablename__ = "repair_work_photos"

    id = Column(Integer, primary_key=True, index=True)

    # Связь с ремонтной работой
    repair_work_id = Column(
        Integer, ForeignKey("repair_works.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repair_work: Mapped["RepairWork"] = relationship(
        "RepairWork", back_populates="photos"
    )

    # Информация о файле
    filename = Column(String(255), nullable=False)  # Оригинальное имя файла
    file_path = Column(String(500), nullable=False)  # Путь к файлу на сервере
    file_size = Column(Integer, nullable=True)  # Размер файла в байтах
    mime_type = Column(String(100), nullable=True)  # MIME тип файла

    # Описание фотографии
    description = Column(Text, nullable=True)  # Описание фотографии
    
    # Порядок отображения
    sort_order = Column(Integer, default=0, nullable=False)

    # Метаданные
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<RepairWorkPhoto(id={self.id}, repair_work_id={self.repair_work_id}, filename='{self.filename}')>"

    def __str__(self):
        return f"Фото {self.filename} для работы #{self.repair_work_id}" 