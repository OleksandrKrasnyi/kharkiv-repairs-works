"""
Pydantic схемы для ремонтных работ
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .work_type import WorkTypeResponse


class WorkStatus(str, Enum):
    """Статус ремонтной работы"""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class RepairWorkBase(BaseModel):
    """Базовая схема для ремонтной работы"""

    # Локация
    location: str | None = Field(None, max_length=500, description="Точечная локация")
    start_location: str | None = Field(
        None, max_length=500, description="Начальная точка участка"
    )
    end_location: str | None = Field(
        None, max_length=500, description="Конечная точка участка"
    )

    # Координаты
    latitude: float | None = Field(None, ge=-90, le=90, description="Широта точки")
    longitude: float | None = Field(None, ge=-180, le=180, description="Долгота точки")
    start_latitude: float | None = Field(
        None, ge=-90, le=90, description="Широта начальной точки"
    )
    start_longitude: float | None = Field(
        None, ge=-180, le=180, description="Долгота начальной точки"
    )
    end_latitude: float | None = Field(
        None, ge=-90, le=90, description="Широта конечной точки"
    )
    end_longitude: float | None = Field(
        None, ge=-180, le=180, description="Долгота конечной точки"
    )

    # Информация
    description: str | None = Field(
        None, max_length=2000, description="Описание работы"
    )
    notes: str | None = Field(
        None, max_length=1000, description="Дополнительные заметки"
    )

    # Время
    start_datetime: datetime = Field(..., description="Дата и время начала работы")
    end_datetime: datetime | None = Field(
        None, description="Дата и время окончания работы"
    )
    planned_duration_hours: int | None = Field(
        None, ge=1, le=8760, description="Планируемая продолжительность в часах"
    )

    # Статус и тип
    status: WorkStatus = Field(WorkStatus.PLANNED, description="Статус работы")
    work_type_id: int | None = Field(None, description="ID типа работы")

    # Геометрия сегмента улицы
    street_segment_geojson: str | None = Field(
        None, description="GeoJSON геометрии выбранного сегмента улицы"
    )
    street_name: str | None = Field(None, max_length=255, description="Название улицы")
    street_osm_type: str | None = Field(
        None, max_length=20, description="Тип OSM объекта (way/relation)"
    )
    street_osm_id: str | None = Field(None, max_length=50, description="OSM ID улицы")

    @model_validator(mode="before")
    @classmethod
    def validate_location_data(cls, data: Any) -> Any:
        """Валидация данных о локации"""
        if isinstance(data, dict):
            location = data.get("location")
            start_location = data.get("start_location")
            end_location = data.get("end_location")
        else:
            # Для случаев когда data это объект модели
            return data

        # Должна быть указана либо location, либо start_location + end_location
        if not location and not (start_location and end_location):
            raise ValueError(
                "Необходимо указать либо location, либо start_location и end_location"
            )

        if location and (start_location or end_location):
            raise ValueError(
                "Нельзя одновременно указывать location и start_location/end_location"
            )

        return data

    @model_validator(mode="before")
    @classmethod
    def validate_coordinates(cls, data: Any) -> Any:
        """Валидация координат"""
        if isinstance(data, dict):
            location = data.get("location")
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            start_lat = data.get("start_latitude")
            start_lon = data.get("start_longitude")
            end_lat = data.get("end_latitude")
            end_lon = data.get("end_longitude")
        else:
            return data

        # Для точечной работы
        if location:
            if (latitude is None) != (longitude is None):
                raise ValueError(
                    "Для точечной работы нужно указать либо обе координаты, либо ни одной"
                )

        # Для участка
        else:
            # Проверяем парность координат
            if bool(start_lat) != bool(start_lon) or bool(end_lat) != bool(end_lon):
                raise ValueError(
                    "Координаты должны быть указаны парами (широта + долгота)"
                )

        return data

    @field_validator("end_datetime")
    @classmethod
    def validate_end_datetime(cls, v: datetime | None, info: Any) -> datetime | None:
        """Валидация времени окончания"""
        if v and hasattr(info, "data") and "start_datetime" in info.data:
            if v <= info.data["start_datetime"]:
                raise ValueError(
                    "Час завершення повинен бути пізніше часу початку роботи"
                )
        return v


class RepairWorkCreate(RepairWorkBase):
    """Схема для создания ремонтной работы"""

    pass


class RepairWorkUpdate(BaseModel):
    """Схема для обновления ремонтной работы"""

    location: str | None = Field(None, max_length=500)
    start_location: str | None = Field(None, max_length=500)
    end_location: str | None = Field(None, max_length=500)

    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    start_latitude: float | None = Field(None, ge=-90, le=90)
    start_longitude: float | None = Field(None, ge=-180, le=180)
    end_latitude: float | None = Field(None, ge=-90, le=90)
    end_longitude: float | None = Field(None, ge=-180, le=180)

    description: str | None = Field(None, max_length=2000)
    notes: str | None = Field(None, max_length=1000)

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    planned_duration_hours: int | None = Field(None, ge=1, le=8760)

    status: WorkStatus | None = None
    work_type_id: int | None = None

    # Геометрия сегмента улицы
    street_segment_geojson: str | None = None
    street_name: str | None = Field(None, max_length=255)
    street_osm_type: str | None = Field(None, max_length=20)
    street_osm_id: str | None = Field(None, max_length=50)


class RepairWorkResponse(RepairWorkBase):
    """Схема для ответа с ремонтной работой"""

    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RepairWorkDetailed(RepairWorkResponse):
    """Детальная схема ремонтной работы с типом работы"""

    work_type: WorkTypeResponse | None = None

    model_config = ConfigDict(from_attributes=True)
