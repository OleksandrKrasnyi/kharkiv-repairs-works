"""
Pydantic схемы для работы с улицами и геолокацией
"""

from pydantic import BaseModel, Field, field_validator


class LocationData(BaseModel):
    """Данные о местоположении"""

    address: str = Field(..., description="Адрес")
    latitude: float = Field(..., ge=-90, le=90, description="Широта")
    longitude: float = Field(..., ge=-180, le=180, description="Долгота")

    class Config:
        json_schema_extra = {
            "example": {
                "address": "вул. Сумська, 1, Харків",
                "latitude": 49.9935,
                "longitude": 36.2304,
            }
        }


class StreetSearchResult(BaseModel):
    """Результат поиска улицы через Nominatim"""

    display_name: str = Field(..., description="Полное название места")
    lat: float = Field(..., description="Широта")
    lon: float = Field(..., description="Долгота")
    importance: float = Field(..., ge=0, le=1, description="Важность результата (0-1)")
    boundingbox: list[float] = Field(
        ..., description="Координаты ограничивающего прямоугольника"
    )
    place_id: int | None = Field(None, description="ID места в OpenStreetMap")
    osm_type: str | None = Field(None, description="Тип объекта в OSM")
    osm_id: int | None = Field(None, description="ID объекта в OSM")

    @field_validator("boundingbox")
    @classmethod
    def validate_boundingbox(cls, v):
        """Валидация ограничивающего прямоугольника"""
        if len(v) != 4:
            raise ValueError("Boundingbox должен содержать 4 координаты")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v):
        """Валидация отображаемого имени"""
        if not v or not v.strip():
            raise ValueError("Отображаемое имя не может быть пустым")
        return v.strip()

    class Config:
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "display_name": "Сумська вулиця, Шевченківський район, Харків, Харківська область, Україна",
                "lat": 49.9935,
                "lon": 36.2304,
                "importance": 0.8,
                "boundingbox": [49.9920, 49.9950, 36.2290, 36.2320],
                "place_id": 123456,
                "osm_type": "way",
                "osm_id": 789012,
            }
        }


class StreetSearchQuery(BaseModel):
    """Запрос для поиска улиц"""

    query: str = Field(
        ..., min_length=2, max_length=200, description="Поисковый запрос"
    )
    city: str = Field("Харків", description="Город для поиска")
    country: str = Field("Україна", description="Страна для поиска")
    limit: int = Field(
        10, ge=1, le=50, description="Максимальное количество результатов"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Валидация поискового запроса"""
        if not v or not v.strip():
            raise ValueError("Поисковый запрос не может быть пустым")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "вул. Сумська",
                "city": "Харків",
                "country": "Україна",
                "limit": 10,
            }
        }


class StreetGeometry(BaseModel):
    """Геометрия улицы для отображения на карте"""

    coordinates: list[list[float]] = Field(
        default_factory=list,
        description="Координаты точек улицы [[lat, lon], [lat, lon], ...] (для одного сегмента)",
    )
    segments: list[list[list[float]]] | None = Field(
        None,
        description="Множественные сегменты улицы [[[lat, lon], ...], [[lat, lon], ...], ...]",
    )
    name: str = Field(..., description="Название улицы")
    osm_type: str = Field(..., description="Тип объекта в OSM")
    osm_id: int = Field(..., description="ID объекта в OSM")

    class Config:
        json_schema_extra = {
            "example": {
                "coordinates": [
                    [49.9935, 36.2304],
                    [49.9940, 36.2310],
                    [49.9945, 36.2316],
                ],
                "segments": [
                    [[49.9935, 36.2304], [49.9940, 36.2310]],
                    [[49.9940, 36.2310], [49.9945, 36.2316]],
                ],
                "name": "Сумська вулиця",
                "osm_type": "way",
                "osm_id": 789012,
            }
        }


class ReverseGeocodeResult(BaseModel):
    """Результат обратного геокодирования"""

    display_name: str = Field(..., description="Полный адрес")
    house_number: str | None = Field(None, description="Номер дома")
    road: str | None = Field(None, description="Название улицы")
    suburb: str | None = Field(None, description="Район")
    city: str | None = Field(None, description="Город")
    postcode: str | None = Field(None, description="Почтовый индекс")

    class Config:
        json_schema_extra = {
            "example": {
                "display_name": "15, Сумська вулиця, Шевченківський район, Харків, Харківська область, 61000, Україна",
                "house_number": "15",
                "road": "Сумська вулиця",
                "suburb": "Шевченківський район",
                "city": "Харків",
                "postcode": "61000",
            }
        }
