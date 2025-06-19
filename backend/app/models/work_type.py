"""
Модель типа работ
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .repair_work import RepairWork


class WorkType(Base):
    """
    Модель типа ремонтных работ
    """

    __tablename__ = "work_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#667eea", nullable=False)  # HEX цвет
    is_active = Column(Boolean, default=True, nullable=False)

    # Метаданные
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Связи
    repair_works: Mapped[list["RepairWork"]] = relationship(
        "RepairWork", back_populates="work_type", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<WorkType(id={self.id}, name='{self.name}', active={self.is_active})>"

    def __str__(self):
        return self.name

    @property
    def repair_works_count(self) -> int:
        """Количество связанных ремонтных работ"""
        return len(self.repair_works) if self.repair_works else 0
