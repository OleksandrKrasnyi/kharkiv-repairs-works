"""
Роутер для поиска улиц и работы с геолокацией
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..schemas.street import (
    ReverseGeocodeResult,
    StreetGeometry,
    StreetSearchQuery,
    StreetSearchResult,
)
from ..services.fast_geometry_service import FastGeometryService
from ..services.street_service import StreetService

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Тестовый endpoint для проверки работы API"""
    return {"status": "OK", "message": "Streets API is working"}


@router.get("/search", response_model=list[StreetSearchResult])
async def search_streets(
    q: str = Query(..., min_length=2, max_length=200, description="Поисковый запрос"),
    city: str = Query("Харків", description="Город для поиска"),
    country: str = Query("Україна", description="Страна для поиска"),
    limit: int = Query(
        10, ge=1, le=50, description="Максимальное количество результатов"
    ),
):
    """
    Поиск улиц через Nominatim API

    - **q**: поисковый запрос (минимум 2 символа)
    - **city**: город для поиска (по умолчанию Харків)
    - **country**: страна для поиска (по умолчанию Україна)
    - **limit**: максимальное количество результатов (от 1 до 50)

    Возвращает список найденных улиц, отсортированных по релевантности.
    """
    logger.info("Searching streets", query=q, city=city, limit=limit)

    # Создаем объект запроса
    search_query = StreetSearchQuery(query=q, city=city, country=country, limit=limit)

    # Выполняем поиск через Nominatim
    service = StreetService()
    results = await service.search_streets(search_query)

    logger.info("Street search completed", results_count=len(results))
    return results


@router.get("/geometry/{osm_type}/{osm_id}", response_model=StreetGeometry | None)
async def get_street_geometry(
    osm_type: str, osm_id: int, service: StreetService = Depends()
) -> StreetGeometry | None:
    """
    Получить геометрию улицы для подсветки на карте

    Args:
        osm_type: Тип объекта OSM (way, node, relation)
        osm_id: ID объекта в OSM
        service: Сервис для работы с улицами

    Returns:
        Геометрия улицы или None если не найдена
    """
    logger.info("Getting street geometry", osm_type=osm_type, osm_id=osm_id)

    geometry = await service.get_street_geometry(osm_type, osm_id)

    logger.info("Street geometry completed", has_geometry=geometry is not None)
    return geometry


@router.get("/reverse", response_model=ReverseGeocodeResult | None)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90, description="Широта"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота"),
    service: StreetService = Depends(),
) -> ReverseGeocodeResult | None:
    """
    Обратное геокодирование - получить адрес по координатам

    Args:
        lat: Широта
        lon: Долгота
        service: Сервис для работы с улицами

    Returns:
        Информация об адресе или None если не найдена
    """
    logger.info("Reverse geocoding", lat=lat, lon=lon)

    result = await service.reverse_geocode(lat, lon)

    logger.info("Reverse geocoding completed", found=result is not None)
    return result


@router.get("/segments", response_model=list[StreetSearchResult])
async def get_all_street_segments(
    q: str = Query(..., min_length=2, max_length=200, description="Название улицы"),
    city: str = Query("Харків", description="Город для поиска"),
    country: str = Query("Україна", description="Страна для поиска"),
):
    """
    Получить все сегменты улицы без удаления дубликатов
    Используется для подсветки всей улицы на карте

    - **q**: название улицы (минимум 2 символа)
    - **city**: город для поиска (по умолчанию Харків)
    - **country**: страна для поиска (по умолчанию Україна)

    Возвращает список всех сегментов улицы для подсветки на карте.
    """
    logger.info("Getting all street segments", query=q, city=city)

    # Создаем объект запроса
    search_query = StreetSearchQuery(query=q, city=city, country=country, limit=50)

    # Выполняем поиск всех сегментов через Nominatim
    service = StreetService()
    results = await service.get_all_street_segments(search_query)

    logger.info("Street segments search completed", results_count=len(results))
    return results


@router.get("/fast-geometry/{street_name}", response_model=StreetGeometry | None)
async def get_fast_street_geometry(
    street_name: str,
    fuzzy_threshold: int = Query(
        70, ge=50, le=100, description="Минимальный порог схожести для fuzzy matching"
    ),
    street_key: str = Query(None, description="Ключ улицы для прямого поиска"),
) -> StreetGeometry | None:
    """
    Быстрое получение геометрии улицы из локального JSON кэша

    Args:
        street_name: Название улицы для поиска
        fuzzy_threshold: Минимальный порог схожести для fuzzy matching (50-100)

    Returns:
        Геометрия улицы или None если не найдена
    """
    logger.info(
        "Getting fast street geometry",
        street_name=street_name,
        fuzzy_threshold=fuzzy_threshold,
        decoded_name=street_name,
    )

    service = FastGeometryService()
    geometry = service.find_street_geometry(street_name, fuzzy_threshold, street_key)

    if geometry:
        segments_count = len(geometry.segments) if geometry.segments else 0
        coordinates_count = len(geometry.coordinates) if geometry.coordinates else 0
        logger.info(
            "Fast street geometry completed - FOUND",
            street_name=street_name,
            segments_count=segments_count,
            coordinates_count=coordinates_count,
        )
    else:
        logger.warning(
            "Fast street geometry completed - NOT FOUND", street_name=street_name
        )

    return geometry


@router.get("/fast-search")
async def fast_street_search(
    q: str = Query(..., min_length=2, max_length=200, description="Поисковый запрос"),
    limit: int = Query(
        10, ge=1, le=50, description="Максимальное количество результатов"
    ),
):
    """
    Быстрый поиск улиц по префиксу из локального кэша

    Args:
        q: поисковый запрос (минимум 2 символа)
        limit: максимальное количество результатов (от 1 до 50)

    Returns:
        Список найденных улиц из локального кэша
    """
    logger.info("Fast street search", query=q, limit=limit)

    service = FastGeometryService()
    street_data_list = service.search_streets_by_prefix(q, limit)

    # Преобразуем в формат, совместимый с фронтендом
    results = []
    for street_data in street_data_list:
        results.append(
            {
                "street_name": street_data["name"],
                "street_key": street_data["key"],  # Добавляем ключ для поиска геометрии
                "source": "local_cache",
            }
        )

    logger.info("Fast street search completed", results_count=len(results))
    return results


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Получить статистику локального кэша улиц

    Returns:
        Информация о количестве улиц в кэше
    """
    service = FastGeometryService()
    streets_count = service.get_available_streets_count()

    return {
        "status": "OK",
        "total_streets": streets_count,
        "cache_loaded": streets_count > 0,
    }


class StreetSegmentRequest(BaseModel):
    """Запрос на вычисление сегмента улицы между двумя точками"""

    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    street_osm_type: str  # 'way' или 'relation'
    street_osm_id: str
    street_name: str


class StreetSegmentResponse(BaseModel):
    """Ответ с геометрией сегмента улицы"""

    segment_geojson: dict
    start_point: dict  # ближайшая точка на улице к start_lat/start_lon
    end_point: dict  # ближайшая точка на улице к end_lat/end_lon
    distance_meters: float
    street_name: str


@router.post("/segment", response_model=StreetSegmentResponse)
async def calculate_street_segment(request: StreetSegmentRequest):
    """
    Вычисляет сегмент улицы между двумя точками

    1. Получает полную геометрию улицы
    2. Находит ближайшие точки на улице к указанным координатам
    3. Вычисляет сегмент между этими точками
    4. Возвращает GeoJSON сегмента
    """
    try:
        service = StreetService()
        segment_data = await service.calculate_street_segment(
            start_lat=request.start_lat,
            start_lon=request.start_lon,
            end_lat=request.end_lat,
            end_lon=request.end_lon,
            street_osm_type=request.street_osm_type,
            street_osm_id=request.street_osm_id,
            street_name=request.street_name,
        )

        return StreetSegmentResponse(**segment_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка вычисления сегмента улицы: {str(e)}"
        ) from e


class StreetSegmentLocalRequest(BaseModel):
    """Запрос на вычисление сегмента улицы между двумя точками (локальные данные)"""

    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    street_name: str


@router.post("/segment-local", response_model=StreetSegmentResponse)
async def calculate_street_segment_local(request: StreetSegmentLocalRequest):
    """
    Вычисляет сегмент улицы между двумя точками используя локальные данные

    1. Получает полную геометрию улицы из локального JSON файла
    2. Находит ближайшие точки на улице к указанным координатам
    3. Вычисляет сегмент между этими точками
    4. Возвращает GeoJSON сегмента
    """
    try:
        service = StreetService()
        segment_data = await service.calculate_street_segment_from_local_data(
            start_lat=request.start_lat,
            start_lon=request.start_lon,
            end_lat=request.end_lat,
            end_lon=request.end_lon,
            street_name=request.street_name,
        )

        return StreetSegmentResponse(**segment_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка вычисления сегмента улицы: {str(e)}"
        ) from e
