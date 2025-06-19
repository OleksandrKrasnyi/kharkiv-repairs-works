"""
Pydantic схемы для типов работ
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkTypeBase(BaseModel):
    """Базовая схема для типа работ"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Название типа работ"
    )
    description: str | None = Field(
        None, max_length=1000, description="Описание типа работ"
    )
    color: str = Field("#667eea", pattern=r"^#[0-9A-Fa-f]{6}$", description="HEX цвет")
    is_active: bool = Field(True, description="Активен ли тип работ")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Цвет должен быть в формате #RRGGBB")
        return v.upper()


class WorkTypeCreate(WorkTypeBase):
    """Схема для создания типа работ"""

    pass


class WorkTypeUpdate(BaseModel):
    """Схема для обновления типа работ"""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Название не может быть пустым")
        return v.strip() if v else v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v is not None:
            if not v.startswith("#") or len(v) != 7:
                raise ValueError("Цвет должен быть в формате #RRGGBB")
            return v.upper()
        return v


class WorkTypeResponse(WorkTypeBase):
    """Схема для ответа с типом работ"""

    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkTypeWithStats(WorkTypeResponse):
    """Схема типа работ с дополнительной статистикой"""

    repair_works_count: int = Field(description="Количество связанных ремонтных работ")

    model_config = ConfigDict(from_attributes=True)
