"""
Сервис для работы с улицами и геокодированием
"""

from collections import deque
from urllib.parse import urlencode

import aiohttp
import structlog
from fuzzywuzzy import fuzz
from shapely.geometry import LineString, Point

from ..config import get_settings
from ..schemas.street import (
    ReverseGeocodeResult,
    StreetGeometry,
    StreetSearchQuery,
    StreetSearchResult,
)
from ..utils.exceptions import ExternalServiceError

logger = structlog.get_logger(__name__)
settings = get_settings()

# Максимальное расстояние для привязки точки к улице (метры)
MAX_SNAP_DISTANCE_M: float = 120.0


class StreetService:
    """Сервис для работы с улицами и геокодированием"""

    def __init__(self):
        self.base_url = settings.nominatim_base_url
        self.timeout = settings.nominatim_timeout

    async def search_streets(
        self, query: StreetSearchQuery
    ) -> list[StreetSearchResult]:
        """
        Поиск улиц через Nominatim API

        Args:
            query: Параметры поиска

        Returns:
            Список найденных улиц

        Raises:
            ExternalServiceError: При ошибке обращения к Nominatim
        """
        logger.info("Searching streets", query=query.query, city=query.city)

        # Формируем поисковый запрос
        search_query = f"{query.query}, {query.city}, {query.country}"

        params = {
            "q": search_query,
            "format": "json",
            "limit": query.limit,
            "addressdetails": 1,
            "countrycodes": "ua",  # Ограничиваем поиск Украиной
            "accept-language": "uk,ru,en",
        }

        url = f"{self.base_url}/search?{urlencode(params)}"
        logger.info("Sending request to Nominatim", url=url, search_query=search_query)

        # Добавляем заголовки для Nominatim
        headers = {
            "User-Agent": "Kharkiv Repairs System/1.0.0 (repair works management)",
            "Accept": "application/json",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(
                            "Nominatim API error", status=response.status, url=url
                        )
                        raise ExternalServiceError(
                            f"Ошибка поиска улиц: HTTP {response.status}"
                        )

                    data = await response.json()

            logger.info("Retrieved results from Nominatim", count=len(data))

            # Преобразуем и сортируем результаты
            results = []
            for item in data:
                try:
                    result = StreetSearchResult(
                        display_name=item["display_name"],
                        lat=float(item["lat"]),
                        lon=float(item["lon"]),
                        importance=float(item.get("importance", 0)),
                        boundingbox=[float(x) for x in item["boundingbox"]],
                        place_id=item.get("place_id"),
                        osm_type=item.get("osm_type"),
                        osm_id=item.get("osm_id"),
                    )
                    results.append(result)
                except (ValueError, KeyError) as e:
                    logger.warning(
                        "Failed to parse search result", error=str(e), item=item
                    )
                    continue

            # Убираем дубликаты и сортируем по релевантности
            results = self._remove_duplicates(results)
            results = self._sort_by_relevance(results, query.query)

            logger.info("Processed search results", count=len(results))
            return results

        except TimeoutError:
            logger.error("Nominatim API timeout", timeout=self.timeout)
            raise ExternalServiceError("Время ожидания поиска улиц истекло") from None
        except aiohttp.ClientError as e:
            logger.error("Nominatim API client error", error=str(e))
            raise ExternalServiceError(
                f"Ошибка соединения с сервисом поиска: {str(e)}"
            ) from e
        except Exception as e:
            logger.error("Unexpected error in street search", error=str(e))
            raise ExternalServiceError(
                f"Неожиданная ошибка при поиске улиц: {str(e)}"
            ) from e

    def _sort_by_relevance(
        self, results: list[StreetSearchResult], query: str
    ) -> list[StreetSearchResult]:
        """
        Сортировка результатов по релевантности

        Args:
            results: Список результатов поиска
            query: Поисковый запрос

        Returns:
            Отсортированный список результатов
        """

        def calculate_relevance(result: StreetSearchResult) -> float:
            """Вычисляем релевантность результата"""
            # Используем fuzzy matching для определения релевантности
            display_name = result.display_name.lower()
            query_lower = query.lower()

            # Различные метрики схожести
            ratio = fuzz.ratio(query_lower, display_name)
            partial_ratio = fuzz.partial_ratio(query_lower, display_name)
            token_sort_ratio = fuzz.token_sort_ratio(query_lower, display_name)
            token_set_ratio = fuzz.token_set_ratio(query_lower, display_name)

            # Вычисляем общий скор
            fuzzy_score = max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)

            # Комбинируем с важностью от Nominatim
            importance_score = result.importance * 100

            # Бонус за точное совпадение в начале
            starts_with_bonus = 20 if display_name.startswith(query_lower) else 0

            # Бонус за содержание ключевых слов
            street_keywords = ["вул", "вулиця", "проспект", "бульвар", "площа"]
            keyword_bonus = (
                10 if any(keyword in display_name for keyword in street_keywords) else 0
            )

            total_score = (
                fuzzy_score * 0.6
                + importance_score * 0.3
                + starts_with_bonus * 0.05
                + keyword_bonus * 0.05
            )

            return total_score

        # Сортируем по убыванию релевантности
        return sorted(results, key=calculate_relevance, reverse=True)

    def _remove_duplicates(
        self, results: list[StreetSearchResult]
    ) -> list[StreetSearchResult]:
        """
        Удаление дубликатов улиц - группируем по основному названию улицы

        Args:
            results: Список результатов поиска

        Returns:
            Список уникальных результатов
        """
        seen_streets = {}
        unique_results = []

        for result in results:
            # Извлекаем основное название улицы (до первой запятой)
            street_name = result.display_name.split(",")[0].strip().lower()

            # Если такая улица уже есть, выбираем более важный результат
            if street_name in seen_streets:
                existing = seen_streets[street_name]
                # Выбираем результат с большей важностью
                if result.importance > existing.importance:
                    # Заменяем существующий результат
                    for i, res in enumerate(unique_results):
                        if res == existing:
                            unique_results[i] = result
                            seen_streets[street_name] = result
                            break
            else:
                seen_streets[street_name] = result
                unique_results.append(result)

        logger.info(
            "Removed duplicates",
            original_count=len(results),
            unique_count=len(unique_results),
        )

        return unique_results

    async def get_street_geometry(
        self, osm_type: str, osm_id: int
    ) -> StreetGeometry | None:
        """
        Получить геометрию улицы через Overpass API для подсветки на карте

        Args:
            osm_type: Тип объекта OSM (way, node, relation)
            osm_id: ID объекта в OSM

        Returns:
            Геометрия улицы или None если не найдена
        """
        logger.info("Getting street geometry", osm_type=osm_type, osm_id=osm_id)

        # Формируем Overpass запрос для получения геометрии
        overpass_query = f"""
        [out:json][timeout:25];
        {osm_type}({osm_id});
        (._;>;);
        out geom;
        """

        overpass_url = "https://overpass-api.de/api/interpreter"

        headers = {
            "User-Agent": "Kharkiv Repairs System/1.0.0 (repair works management)",
            "Content-Type": "text/plain",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    overpass_url, data=overpass_query, headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error("Overpass API error", status=response.status)
                        return None

                    data = await response.json()

            # Обрабатываем ответ
            elements = data.get("elements", [])
            way_element = None
            nodes = {}

            # Находим way и его nodes
            for element in elements:
                if element.get("type") == "way" and element.get("id") == osm_id:
                    way_element = element
                elif element.get("type") == "node":
                    nodes[element["id"]] = element

            if not way_element or "nodes" not in way_element:
                logger.warning("Way element not found or has no nodes")
                return None

            # Формируем координаты
            coordinates = []
            for node_id in way_element["nodes"]:
                if node_id in nodes:
                    node = nodes[node_id]
                    if "lat" in node and "lon" in node:
                        coordinates.append([node["lat"], node["lon"]])

            if not coordinates:
                logger.warning("No valid coordinates found")
                return None

            # Получаем название улицы
            tags = way_element.get("tags", {})
            name = tags.get(
                "name", tags.get("name:uk", tags.get("name:ru", "Неизвестная улица"))
            )

            geometry = StreetGeometry(
                coordinates=coordinates, name=name, osm_type=osm_type, osm_id=osm_id
            )

            logger.info(
                "Street geometry retrieved", name=name, points_count=len(coordinates)
            )
            return geometry

        except Exception as e:
            logger.error("Failed to get street geometry", error=str(e))
            return None

    async def reverse_geocode(
        self, lat: float, lon: float
    ) -> ReverseGeocodeResult | None:
        """
        Обратное геокодирование - получить адрес по координатам

        Args:
            lat: Широта
            lon: Долгота

        Returns:
            Информация об адресе или None если не найдена
        """
        logger.info("Reverse geocoding", lat=lat, lon=lon)

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "uk,ru,en",
            "zoom": 18,  # Максимальная детализация для получения номера дома
        }

        url = f"{self.base_url}/reverse?{urlencode(params)}"

        headers = {
            "User-Agent": "Kharkiv Repairs System/1.0.0 (repair works management)",
            "Accept": "application/json",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(
                            "Nominatim reverse geocoding error", status=response.status
                        )
                        return None

                    data = await response.json()

            # Обрабатываем ответ
            address = data.get("address", {})
            display_name = data.get("display_name", "")

            result = ReverseGeocodeResult(
                display_name=display_name,
                house_number=address.get("house_number"),
                road=address.get("road"),
                suburb=address.get("suburb"),
                city=address.get("city")
                or address.get("town")
                or address.get("village"),
                postcode=address.get("postcode"),
            )

            logger.info(
                "Reverse geocoding completed",
                road=result.road,
                house_number=result.house_number,
            )
            return result

        except Exception as e:
            logger.error("Failed reverse geocoding", error=str(e))
            return None

    async def get_all_street_segments(
        self, query: StreetSearchQuery
    ) -> list[StreetSearchResult]:
        """
        Поиск всех сегментов улицы без удаления дубликатов
        Используется для получения полной геометрии улицы на карте

        Args:
            query: Параметры поиска

        Returns:
            Список всех найденных сегментов улицы

        Raises:
            ExternalServiceError: При ошибке обращения к Nominatim
        """
        logger.info("Searching all street segments", query=query.query, city=query.city)

        # Формируем несколько вариантов поисковых запросов для более полного охвата
        search_variants = [
            f"{query.query}, {query.city}, {query.country}",
            f"{query.query}, {query.city}",
            f"{query.query}",
        ]

        all_results = []

        for search_query in search_variants:
            params = {
                "q": search_query,
                "format": "json",
                "limit": 100,  # Увеличиваем лимит для получения большего количества сегментов
                "addressdetails": 1,
                "countrycodes": "ua",  # Ограничиваем поиск Украиной
                "accept-language": "uk,ru,en",
                "dedupe": 0,  # Отключаем дедупликацию на стороне Nominatim
            }

            url = f"{self.base_url}/search?{urlencode(params)}"
            logger.info(
                "Sending request to Nominatim for all segments",
                url=url,
                search_query=search_query,
            )

            # Добавляем заголовки для Nominatim
            headers = {
                "User-Agent": "Kharkiv Repairs System/1.0.0 (repair works management)",
                "Accept": "application/json",
            }

            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            logger.warning(
                                "Nominatim API error",
                                status=response.status,
                                url=url,
                                search_query=search_query,
                            )
                            continue

                        data = await response.json()

                logger.info(
                    "Retrieved segments from Nominatim",
                    count=len(data),
                    search_query=search_query,
                )

                # Преобразуем результаты БЕЗ удаления дубликатов
                for item in data:
                    try:
                        result = StreetSearchResult(
                            display_name=item["display_name"],
                            lat=float(item["lat"]),
                            lon=float(item["lon"]),
                            importance=float(item.get("importance", 0)),
                            boundingbox=[float(x) for x in item["boundingbox"]],
                            place_id=item.get("place_id"),
                            osm_type=item.get("osm_type"),
                            osm_id=item.get("osm_id"),
                        )
                        all_results.append(result)
                    except (ValueError, KeyError) as e:
                        logger.warning(
                            "Failed to parse segment result", error=str(e), item=item
                        )
                        continue

            except Exception as e:
                logger.warning(
                    "Failed to get segments for query",
                    error=str(e),
                    search_query=search_query,
                )
                continue

        # Удаляем дубликаты по OSM ID
        seen_osm_ids = set()
        unique_results = []

        for result in all_results:
            if result.osm_id and result.osm_type:
                osm_key = f"{result.osm_type}:{result.osm_id}"
                if osm_key not in seen_osm_ids:
                    seen_osm_ids.add(osm_key)
                    unique_results.append(result)

        # Фильтруем результаты более гибко
        query_lower = query.query.lower()

        # Создаем список ключевых слов для поиска
        query_keywords = []
        if "проспект" in query_lower:
            query_keywords.extend(["проспект", "просп"])
        if "вулиця" in query_lower or "вул" in query_lower:
            query_keywords.extend(["вулиця", "вул"])
        if "бульвар" in query_lower:
            query_keywords.extend(["бульвар", "бул"])
        if "площа" in query_lower:
            query_keywords.extend(["площа", "пл"])

        # Добавляем основное название без типа улицы
        main_name_parts = (
            query_lower.replace("проспект", "")
            .replace("вулиця", "")
            .replace("вул.", "")
            .replace("бульвар", "")
            .replace("площа", "")
            .strip()
            .split()
        )

        filtered_results = []

        for result in unique_results:
            street_name = result.display_name.split(",")[0].strip().lower()

            # Проверяем различные варианты совпадения
            match_found = False

            # 1. Прямое вхождение запроса
            if query_lower in street_name:
                match_found = True

            # 2. Проверяем по основным частям названия
            elif main_name_parts:
                for part in main_name_parts:
                    if len(part) > 2 and part in street_name:
                        match_found = True
                        break

            # 3. Проверяем варианты типов улиц
            elif query_keywords:
                for keyword in query_keywords:
                    if keyword in street_name:
                        # Если нашли тип улицы, проверяем основное название
                        for part in main_name_parts:
                            if len(part) > 2 and part in street_name:
                                match_found = True
                                break
                        if match_found:
                            break

            if match_found:
                filtered_results.append(result)

        # Сортируем по релевантности, но НЕ удаляем дубликаты
        sorted_results = self._sort_by_relevance(filtered_results, query.query)

        logger.info(
            "Found street segments",
            total_found=len(all_results),
            unique_count=len(unique_results),
            filtered_count=len(filtered_results),
            final_count=len(sorted_results),
        )

        return sorted_results

    async def calculate_street_segment(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        street_osm_type: str,
        street_osm_id: str,
        street_name: str,
    ) -> dict:
        """
        Вычисляет сегмент улицы между двумя точками

        Args:
            start_lat, start_lon: Координаты начальной точки
            end_lat, end_lon: Координаты конечной точки
            street_osm_type: Тип OSM объекта (way/relation)
            street_osm_id: ID улицы в OSM
            street_name: Название улицы

        Returns:
            Словарь с данными сегмента улицы
        """
        logger.info(
            "Calculating street segment",
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            street_osm_type=street_osm_type,
            street_osm_id=street_osm_id,
            street_name=street_name,
        )

        try:
            # Получаем полную геометрию улицы
            street_geometry = await self.get_street_geometry(
                street_osm_type, int(street_osm_id)
            )
            if not street_geometry:
                raise ExternalServiceError("Не удалось получить геометрию улицы")

            # Преобразуем coordinates в массив точек
            if (
                isinstance(street_geometry.coordinates, list)
                and len(street_geometry.coordinates) > 0
            ):
                # Для MultiLineString берем первую линию, для LineString - всю
                if isinstance(street_geometry.coordinates[0][0], list):
                    # MultiLineString
                    street_coords = street_geometry.coordinates[0]
                else:
                    # LineString
                    street_coords = street_geometry.coordinates
            else:
                raise ExternalServiceError("Некорректная геометрия улицы")

            # Находим ближайшие точки на улице
            try:
                start_point = self._find_closest_point_on_line(
                    start_lat, start_lon, street_coords
                )
                end_point = self._find_closest_point_on_line(
                    end_lat, end_lon, street_coords
                )
            except ValueError as e:
                raise ExternalServiceError(
                    "Точка занадто далеко від обраної вулиці"
                ) from e

            # --- НОВЫЙ ТОЧНЫЙ АЛГОРИТМ С SHAPELY ---
            try:
                from shapely.geometry import LineString, Point
                from shapely.ops import substring as shp_substring

                line = LineString([(c[0], c[1]) for c in street_coords])
                p1 = Point(start_point["lon"], start_point["lat"])
                p2 = Point(end_point["lon"], end_point["lat"])

                d1 = line.project(p1)
                d2 = line.project(p2)
                if d1 > d2:
                    d1, d2 = d2, d1

                subline = shp_substring(line, d1, d2)
                segment_coords = [[lon, lat] for lon, lat in subline.coords]
            except Exception as shapely_err:
                logger.warning(
                    "Shapely precise substring failed, fallback to index slicing",
                    error=str(shapely_err),
                )

                # Вычисляем сегмент между точками (старый способ)
                segment_coords = self._extract_segment_between_points(
                    street_coords, start_point, end_point
                )

                # Гарантируем точные координаты концов
                if segment_coords:
                    segment_coords[0] = [start_point["lon"], start_point["lat"]]
                    segment_coords[-1] = [end_point["lon"], end_point["lat"]]

            # Вычисляем расстояние сегмента
            distance_meters = self._calculate_segment_distance(segment_coords)

            # Создаем GeoJSON сегмента
            segment_geojson = {
                "type": "Feature",
                "properties": {
                    "name": street_name,
                    "osm_type": street_osm_type,
                    "osm_id": street_osm_id,
                    "segment_length_meters": distance_meters,
                },
                "geometry": {"type": "LineString", "coordinates": segment_coords},
            }

            logger.info(
                "Street segment calculated successfully",
                distance_meters=distance_meters,
                segment_points=len(segment_coords),
            )

            return {
                "segment_geojson": segment_geojson,
                "start_point": {"lat": start_point["lat"], "lon": start_point["lon"]},
                "end_point": {"lat": end_point["lat"], "lon": end_point["lon"]},
                "distance_meters": distance_meters,
                "street_name": street_name,
            }

        except Exception as e:
            logger.error("Error calculating street segment", error=str(e))
            raise ExternalServiceError(
                f"Ошибка вычисления сегмента улицы: {str(e)}"
            ) from e

    def _find_closest_point_on_line(
        self,
        lat: float,
        lon: float,
        line_coords: list,
        max_dist_m: float = MAX_SNAP_DISTANCE_M,
    ) -> dict:
        """
        Находит ближайшую точку на линии к заданным координатам с помощью Shapely

        Args:
            lat, lon: Целевые координаты
            line_coords: Координаты линии [[lon, lat], ...]
            max_dist_m: Максимальное расстояние для привязки точки к улице (метры)

        Returns:
            Словарь с ближайшей точкой, индексом ближайшей вершины и расстоянием
        """
        try:
            # Создаём геометрию линии и точки (Shapely использует (x, y) = (lon, lat))
            line = LineString([(c[0], c[1]) for c in line_coords])
            point = Point(lon, lat)

            # Проектируем точку на линию
            projected_distance = line.project(point)
            nearest_point: Point = line.interpolate(projected_distance)
            nearest_lat = nearest_point.y
            nearest_lon = nearest_point.x

            # Вычисляем расстояние в метрах (по Хаверсину)
            distance_meters = self._haversine_distance(
                lat, lon, nearest_lat, nearest_lon
            )

            # Проверяем радиус привязки
            if distance_meters > max_dist_m:
                raise ValueError("Point too far from street segment")

            # Находим индекс ближайшей вершины (нужно для существующих алгоритмов)
            min_idx = 0
            min_vertex_distance = float("inf")
            for idx, coord in enumerate(line_coords):
                d = self._haversine_distance(
                    nearest_lat, nearest_lon, coord[1], coord[0]
                )
                if d < min_vertex_distance:
                    min_vertex_distance = d
                    min_idx = idx

            return {
                "lat": nearest_lat,
                "lon": nearest_lon,
                "index": min_idx,
                "distance_meters": distance_meters,
            }
        except Exception as e:
            # Fallback на старый алгоритм при ошибке
            logger.warning("Fallback to simple nearest-vertex algorithm", error=str(e))
            return self._find_closest_point_on_line_simple(lat, lon, line_coords)

    # ===== BACKWARD COMPATIBLE SIMPLE METHOD (используется в fallback) =====
    def _find_closest_point_on_line_simple(
        self, lat: float, lon: float, line_coords: list
    ) -> dict:
        """Предыдущая реализация перебора вершинок (оставлена для надёжности)"""
        min_distance = float("inf")
        closest_point = None
        closest_index = 0

        for i, coord in enumerate(line_coords):
            point_lon, point_lat = coord[0], coord[1]
            distance = self._haversine_distance(lat, lon, point_lat, point_lon)

            if distance < min_distance:
                min_distance = distance
                closest_point = {"lat": point_lat, "lon": point_lon}
                closest_index = i

        return {
            "lat": closest_point["lat"],
            "lon": closest_point["lon"],
            "index": closest_index,
            "distance_meters": min_distance,
        }

    def _extract_segment_between_points(
        self, line_coords: list, start_point: dict, end_point: dict
    ) -> list:
        """
        Извлекает сегмент линии между двумя точками, гарантируя, что
        первая и последняя координаты строго совпадают со «снэпнутыми»
        точками start_point / end_point.
        """
        start_index = start_point["index"]
        end_index = end_point["index"]

        # Гарантируем правильное направление
        if start_index > end_index:
            start_index, end_index = end_index, start_index
            start_pt, end_pt = end_point, start_point
        else:
            start_pt, end_pt = start_point, end_point

        # Базовый срез
        segment_coords = line_coords[start_index : end_index + 1]

        # Вставляем точные координаты в начало/конец, если отличаются
        if segment_coords:
            if (
                abs(segment_coords[0][0] - start_pt["lon"]) > 1e-9
                or abs(segment_coords[0][1] - start_pt["lat"]) > 1e-9
            ):
                segment_coords.insert(0, [start_pt["lon"], start_pt["lat"]])
            if (
                abs(segment_coords[-1][0] - end_pt["lon"]) > 1e-9
                or abs(segment_coords[-1][1] - end_pt["lat"]) > 1e-9
            ):
                segment_coords.append([end_pt["lon"], end_pt["lat"]])

        return segment_coords

    def _calculate_segment_distance(self, coords: list) -> float:
        """
        Вычисляет длину сегмента в метрах

        Args:
            coords: Координаты сегмента [[lon, lat], ...]

        Returns:
            Длина в метрах
        """
        total_distance = 0.0

        for i in range(len(coords) - 1):
            lat1, lon1 = coords[i][1], coords[i][0]
            lat2, lon2 = coords[i + 1][1], coords[i + 1][0]

            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            total_distance += distance

        return total_distance

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Вычисляет расстояние между двумя точками по формуле Хаверсина

        Args:
            lat1, lon1: Координаты первой точки
            lat2, lon2: Координаты второй точки

        Returns:
            Расстояние в метрах
        """
        import math

        # Радиус Земли в метрах
        R = 6371000

        # Переводим в радианы
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Формула Хаверсина
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def calculate_street_segment_from_local_data(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        street_name: str,
    ) -> dict:
        """
        Вычисляет сегмент улицы между двумя точками используя локальные данные

        Args:
            start_lat, start_lon: Координаты начальной точки
            end_lat, end_lon: Координаты конечной точки
            street_name: Название улицы

        Returns:
            Словарь с данными сегмента улицы
        """
        logger.info(
            "Calculating street segment from local data",
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            street_name=street_name,
        )

        try:
            # Используем FastGeometryService для получения геометрии из локальных данных
            from .fast_geometry_service import FastGeometryService

            fast_service = FastGeometryService()

            # Получаем геометрию улицы
            street_geometry = fast_service.find_street_geometry(street_name)
            if not street_geometry:
                raise ExternalServiceError("Не удалось найти улицу в локальных данных")

            # Получаем все сегменты улицы
            street_segments = []
            if hasattr(street_geometry, "segments") and street_geometry.segments:
                # Если есть множественные сегменты - работаем с ними отдельно
                for segment in street_geometry.segments:
                    if len(segment) >= 2:
                        # Конвертируем каждый сегмент в правильный формат
                        converted_segment = self._convert_coordinates_format(segment)
                        street_segments.append(converted_segment)
            elif street_geometry.coordinates:
                # Если есть единая линия
                converted_coords = self._convert_coordinates_format(
                    street_geometry.coordinates
                )
                street_segments.append(converted_coords)

            if not street_segments:
                raise ExternalServiceError("Нет координат для улицы")

            # === ТОЧНОЕ ОТРЕЗАНИЕ ЧЕРЕЗ SHAPELY (MERGE + SUBSTRING) ===
            segment_coords = []
            try:
                from shapely.geometry import LineString, MultiLineString, Point
                from shapely.ops import linemerge
                from shapely.ops import substring as shp_substring

                # Собираем MultiLineString
                line_parts = [
                    LineString(seg) for seg in street_segments if len(seg) >= 2
                ]
                merged_line = linemerge(MultiLineString(line_parts))

                # Если получилась MultiLineString, берём ту часть, где лежат обе проекции
                if merged_line.geom_type == "MultiLineString":
                    # Находим ту, где минимальная сумма расстояний до кликов
                    best_part = None
                    best_score = float("inf")
                    for part in merged_line.geoms:
                        score = part.distance(
                            Point(start_lon, start_lat)
                        ) + part.distance(Point(end_lon, end_lat))
                        if score < best_score:
                            best_score = score
                            best_part = part
                    merged_line = best_part if best_part else merged_line.geoms[0]

                # Проекции
                proj_start = merged_line.project(Point(start_lon, start_lat))
                proj_end = merged_line.project(Point(end_lon, end_lat))
                if proj_start > proj_end:
                    proj_start, proj_end = proj_end, proj_start

                subline = shp_substring(merged_line, proj_start, proj_end)
                segment_coords = [[lon, lat] for lon, lat in subline.coords]

                # Формируем сведения о точках
                snapped_start = subline.coords[0]
                snapped_end = subline.coords[-1]
                snapped_start_point = {"lat": snapped_start[1], "lon": snapped_start[0]}
                snapped_end_point = {"lat": snapped_end[1], "lon": snapped_end[0]}

                path_data = {
                    "coordinates": segment_coords,
                    "start_point": snapped_start_point,
                    "end_point": snapped_end_point,
                    "segments_used": -1,
                }
            except Exception as shapely_local_err:
                logger.warning(
                    "Shapely merge+substring failed, fallback to topological",
                    error=str(shapely_local_err),
                )
                # Фолбэк – топологический алгоритм
                path_data = self._build_full_path_between_points(
                    start_lat,
                    start_lon,
                    end_lat,
                    end_lon,
                    street_segments,
                )
                segment_coords = path_data["coordinates"]

            # Если по какой-то причине сегмента нет – ошибка
            if not segment_coords:
                raise ExternalServiceError("Не удалось построить сегмент улицы")

            # Расстояние
            distance_meters = self._calculate_segment_distance(segment_coords)

            # ГеоJSON и возврат – ниже (оставляем существующий код, но заменяем distance_meters и segment_coords переменные)
            # Создаем GeoJSON сегмента
            segment_geojson = {
                "type": "Feature",
                "properties": {
                    "name": street_name,
                    "osm_type": "local",
                    "osm_id": "local",
                    "segment_length_meters": distance_meters,
                    "source": "local_data",
                },
                "geometry": {"type": "LineString", "coordinates": segment_coords},
            }

            logger.info(
                "Street segment calculated successfully from local data",
                distance_meters=distance_meters,
                segment_points=len(segment_coords),
                used_segments=len(street_segments),
                path_segments=path_data.get("segments_used", 1),
            )

            return {
                "segment_geojson": segment_geojson,
                "start_point": {
                    "lat": path_data["start_point"]["lat"],
                    "lon": path_data["start_point"]["lon"],
                },
                "end_point": {
                    "lat": path_data["end_point"]["lat"],
                    "lon": path_data["end_point"]["lon"],
                },
                "distance_meters": distance_meters,
                "street_name": street_name,
            }

        except Exception as e:
            logger.error(
                "Error calculating street segment from local data", error=str(e)
            )
            raise ExternalServiceError(
                f"Ошибка вычисления сегмента улицы: {str(e)}"
            ) from e

    def _convert_coordinates_format(self, coordinates: list) -> list:
        """
        Конвертирует координаты в формат [lon, lat] для GeoJSON

        Args:
            coordinates: Список координат в любом формате

        Returns:
            Список координат в формате [lon, lat]
        """
        converted_coords = []
        for coord in coordinates:
            if len(coord) == 2:
                # Координаты могут быть в формате [lat, lon] или [lon, lat]
                # Проверяем по диапазону значений для Харькова
                if 35 <= coord[0] <= 37 and 49 <= coord[1] <= 51:
                    # Формат [lon, lat]
                    converted_coords.append([coord[0], coord[1]])
                elif 35 <= coord[1] <= 37 and 49 <= coord[0] <= 51:
                    # Формат [lat, lon] - переставляем
                    converted_coords.append([coord[1], coord[0]])
                else:
                    # Если не можем определить, используем как есть
                    converted_coords.append([coord[0], coord[1]])
        return converted_coords

    def _build_full_path_between_points(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        segments: list,
    ) -> dict:
        """
        Строит полный путь между двумя точками, соединяя только топологически связанные сегменты

        Args:
            start_lat, start_lon: Координаты начальной точки
            end_lat, end_lon: Координаты конечной точки
            segments: Список сегментов улицы

        Returns:
            Словарь с координатами полного пути
        """
        # Находим сегменты и точки для начала и конца
        start_segment_info = self._find_closest_segment_and_point(
            start_lat, start_lon, segments
        )
        end_segment_info = self._find_closest_segment_and_point(
            end_lat, end_lon, segments
        )

        if not start_segment_info or not end_segment_info:
            return None

        start_segment_idx = start_segment_info["segment_index"]
        end_segment_idx = end_segment_info["segment_index"]

        # Если точки на одном сегменте
        if start_segment_idx == end_segment_idx:
            segment = segments[start_segment_idx]
            start_point = start_segment_info["point"]
            end_point = end_segment_info["point"]

            # Извлекаем участок между точками
            segment_coords = self._extract_segment_between_points(
                segment, start_point, end_point
            )

            return {
                "coordinates": segment_coords,
                "start_point": start_point,
                "end_point": end_point,
                "segments_used": 1,
            }

        # Если точки на разных сегментах - используем топологический поиск пути
        path_result = self._find_topological_path_between_segments(
            start_segment_info, end_segment_info, segments
        )

        if path_result:
            return path_result

        # Если топологический путь не найден, используем простейший подход - только начальный и конечный сегменты
        logger.warning(
            "Could not find topological path, using simple approach",
            start_segment=start_segment_idx,
            end_segment=end_segment_idx,
        )

        return self._build_simple_path_between_segments(
            start_segment_info, end_segment_info, segments
        )

    def _find_topological_path_between_segments(
        self, start_info: dict, end_info: dict, segments: list
    ) -> dict:
        """
        Находит топологически правильный путь между сегментами

        Args:
            start_info: Информация о начальном сегменте
            end_info: Информация о конечном сегменте
            segments: Список всех сегментов

        Returns:
            Словарь с координатами пути или None
        """
        start_info["segment"]
        end_info["segment"]
        start_point = start_info["point"]
        end_point = end_info["point"]

        # Адаптивные пороги расстояния для соединения сегментов (в метрах)
        # Сначала пытаемся более строгий (100 м), затем fallback (200 м)
        for max_connection_distance in (100.0, 200.0):
            # Строим граф соединений между сегментами
            segment_graph = self._build_segment_connection_graph(
                segments, max_connection_distance
            )

            # Ищем кратчайший путь в графе
            path_indices = self._find_shortest_path_in_graph(
                segment_graph,
                start_info["segment_index"],
                end_info["segment_index"],
            )

            if path_indices:
                # Строим координатный путь по найденным индексам сегментов
                return self._build_coordinate_path_from_indices(
                    path_indices, segments, start_point, end_point
                )

        # Если путь не найден даже при увеличенном пороге
        return None

    def _build_segment_connection_graph(
        self, segments: list, max_distance: float
    ) -> dict:
        """
        Строит граф соединений между сегментами

        Args:
            segments: Список сегментов
            max_distance: Максимальное расстояние для соединения (в метрах)

        Returns:
            Граф в виде словаря {segment_index: [connected_segment_indices]}
        """
        graph = {i: [] for i in range(len(segments))}

        for i in range(len(segments)):
            for j in range(i + 1, len(segments)):
                if self._are_segments_connected(segments[i], segments[j], max_distance):
                    graph[i].append(j)
                    graph[j].append(i)

        return graph

    def _are_segments_connected(
        self, segment1: list, segment2: list, max_distance: float
    ) -> bool:
        """
        Проверяет, соединены ли два сегмента (близки ли их концы)

        Args:
            segment1: Первый сегмент
            segment2: Второй сегмент
            max_distance: Максимальное расстояние для соединения

        Returns:
            True если сегменты соединены
        """
        if len(segment1) < 2 or len(segment2) < 2:
            return False

        # Проверяем все комбинации концов сегментов
        s1_start = segment1[0]
        s1_end = segment1[-1]
        s2_start = segment2[0]
        s2_end = segment2[-1]

        connections = [
            self._haversine_distance(
                s1_start[1], s1_start[0], s2_start[1], s2_start[0]
            ),
            self._haversine_distance(s1_start[1], s1_start[0], s2_end[1], s2_end[0]),
            self._haversine_distance(s1_end[1], s1_end[0], s2_start[1], s2_start[0]),
            self._haversine_distance(s1_end[1], s1_end[0], s2_end[1], s2_end[0]),
        ]

        return min(connections) <= max_distance

    def _find_shortest_path_in_graph(self, graph: dict, start: int, end: int) -> list:
        """
        Находит кратчайший путь в графе с помощью BFS

        Args:
            graph: Граф соединений
            start: Индекс начального сегмента
            end: Индекс конечного сегмента

        Returns:
            Список индексов сегментов в пути
        """
        if start == end:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()

            for neighbor in graph.get(current, []):
                if neighbor == end:
                    return path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []  # Путь не найден

    def _build_coordinate_path_from_indices(
        self, path_indices: list, segments: list, start_point: dict, end_point: dict
    ) -> dict:
        """
        Строит координатный путь по индексам сегментов

        Args:
            path_indices: Список индексов сегментов в пути
            segments: Список всех сегментов
            start_point: Начальная точка
            end_point: Конечная точка

        Returns:
            Словарь с координатами пути
        """
        if not path_indices:
            return None

        full_path = []

        for i, segment_idx in enumerate(path_indices):
            segment = segments[segment_idx]

            if i == 0:
                # Первый сегмент - от начальной точки до конца сегмента
                start_index = start_point["index"]
                segment_part = segment[start_index:]
            elif i == len(path_indices) - 1:
                # Последний сегмент - от начала до конечной точки
                end_index = end_point["index"]
                segment_part = segment[: end_index + 1]

                # Проверяем направление
                if full_path and segment_part:
                    prev_end = full_path[-1]
                    distance_to_start = self._haversine_distance(
                        prev_end[1], prev_end[0], segment_part[0][1], segment_part[0][0]
                    )
                    distance_to_end = self._haversine_distance(
                        prev_end[1],
                        prev_end[0],
                        segment_part[-1][1],
                        segment_part[-1][0],
                    )

                    if distance_to_end < distance_to_start:
                        segment_part = list(reversed(segment_part))
            else:
                # Промежуточный сегмент - весь сегмент, но в правильном направлении
                segment_part = segment

                # Определяем правильное направление
                if full_path and segment_part:
                    prev_end = full_path[-1]
                    distance_to_start = self._haversine_distance(
                        prev_end[1], prev_end[0], segment_part[0][1], segment_part[0][0]
                    )
                    distance_to_end = self._haversine_distance(
                        prev_end[1],
                        prev_end[0],
                        segment_part[-1][1],
                        segment_part[-1][0],
                    )

                    if distance_to_end < distance_to_start:
                        segment_part = list(reversed(segment_part))

            # Избегаем дублирования точек
            if (
                full_path
                and segment_part
                and self._points_are_close(full_path[-1], segment_part[0])
            ):
                segment_part = segment_part[1:]

            full_path.extend(segment_part)

        return {
            "coordinates": full_path,
            "start_point": start_point,
            "end_point": end_point,
            "segments_used": len(path_indices),
        }

    def _build_simple_path_between_segments(
        self, start_info: dict, end_info: dict, segments: list
    ) -> dict:
        """
        Строит простой путь между двумя сегментами (используется как fallback)

        Args:
            start_info: Информация о начальном сегменте
            end_info: Информация о конечном сегменте
            segments: Список сегментов

        Returns:
            Словарь с простым путем
        """
        start_segment = segments[start_info["segment_index"]]
        end_segment = segments[end_info["segment_index"]]
        start_point = start_info["point"]
        end_point = end_info["point"]

        # Берем части сегментов
        start_index = start_point["index"]
        end_index = end_point["index"]

        start_part = start_segment[start_index:]
        end_part = end_segment[: end_index + 1]

        # Проверяем, нужно ли реверсировать конечный сегмент
        if start_part and end_part:
            distance_to_start = self._haversine_distance(
                start_part[-1][1], start_part[-1][0], end_part[0][1], end_part[0][0]
            )
            distance_to_end = self._haversine_distance(
                start_part[-1][1], start_part[-1][0], end_part[-1][1], end_part[-1][0]
            )

            if distance_to_end < distance_to_start:
                end_part = list(reversed(end_part))

        # Соединяем только если расстояние меньше 300 метров
        full_path = start_part.copy()
        if start_part and end_part:
            connection_distance = self._haversine_distance(
                start_part[-1][1], start_part[-1][0], end_part[0][1], end_part[0][0]
            )

            # Соединяем только если расстояние меньше 300 метров
            if connection_distance <= 300:
                full_path.extend(end_part)
            else:
                # Иначе возвращаем только первый сегмент
                logger.warning(
                    "Segments too far apart, using only first segment",
                    connection_distance=connection_distance,
                )

        return {
            "coordinates": full_path,
            "start_point": start_point,
            "end_point": end_point,
            "segments_used": 2 if len(full_path) > len(start_part) else 1,
        }

    def _points_are_close(
        self, point1: list, point2: list, threshold: float = 5.0
    ) -> bool:
        """
        Проверяет, близки ли две точки

        Args:
            point1: Первая точка [lon, lat]
            point2: Вторая точка [lon, lat]
            threshold: Порог расстояния в метрах

        Returns:
            True если точки близки
        """
        distance = self._haversine_distance(point1[1], point1[0], point2[1], point2[0])
        return distance <= threshold

    def _find_closest_segment_and_point(
        self, lat: float, lon: float, segments: list
    ) -> dict:
        """
        Находит ближайший сегмент и точку на нем

        Args:
            lat, lon: Координаты для поиска
            segments: Список сегментов

        Returns:
            Словарь с информацией о сегменте и точке
        """
        closest_info = None
        min_distance = float("inf")

        for i, segment in enumerate(segments):
            if len(segment) < 2:
                continue

            try:
                point_info = self._find_closest_point_on_line(lat, lon, segment)
            except ValueError:
                continue  # Точка слишком далека от этого сегмента

            if point_info["distance_meters"] < min_distance:
                min_distance = point_info["distance_meters"]
                closest_info = {
                    "segment_index": i,
                    "segment": segment,
                    "point": point_info,
                    "distance": point_info["distance_meters"],
                }

        if not closest_info:
            raise ExternalServiceError("Точка занадто далеко від обраної вулиці")
        return closest_info
