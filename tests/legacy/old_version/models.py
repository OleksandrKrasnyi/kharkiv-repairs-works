from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class WorkType(Base):
    __tablename__ = "work_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#667eea")  # HEX цвет для отображения на карте

    # Связь с ремонтными работами
    repair_works = relationship("RepairWork", back_populates="work_type")

    def __repr__(self):
        return f"<WorkType(id={self.id}, name='{self.name}')>"


class RepairWork(Base):
    __tablename__ = "repair_works"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255), index=True, nullable=True)
    start_location = Column(String(255), index=True, nullable=True)
    end_location = Column(String(255), index=True, nullable=True)
    description = Column(Text, nullable=True)
    start_datetime = Column(DateTime, index=True, nullable=False)
    end_datetime = Column(DateTime, nullable=True)

    # Связь с типом работ
    work_type_id = Column(Integer, ForeignKey("work_types.id"), nullable=True)
    work_type = relationship("WorkType", back_populates="repair_works")

    def __repr__(self):
        return f"<RepairWork(id={self.id}, description='{self.description}', start_datetime='{self.start_datetime}')>"
