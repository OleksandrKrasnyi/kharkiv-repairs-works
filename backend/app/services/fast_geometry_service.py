"""
Быстрый сервис для получения геометрии улиц из локального JSON файла
"""

import json
from pathlib import Path

import structlog
from fuzzywuzzy import fuzz, process

from ..schemas.street import StreetGeometry

logger = structlog.get_logger(__name__)


class FastGeometryService:
    """Сервис для быстрого получения геометрии улиц из локального кэша"""

    def __init__(self):
        self.streets_data: dict[str, list[dict]] = {}
        self.loaded = False

    def _load_streets_data(self):
        """Загружает данные улиц из полного JSON файла"""
        if self.loaded:
            return

        try:
            # Путь к полному JSON файлу
            json_path = (
                Path(__file__).parent.parent.parent.parent
                / "frontend"
                / "static"
                / "data"
                / "kharkiv_streets_full.json"
            )

            if not json_path.exists():
                logger.error("Streets full data file not found", path=str(json_path))
                return

            with open(json_path, encoding="utf-8") as f:
                full_data = json.load(f)

            # Преобразуем в упрощенный формат для поиска на лету
            self.streets_data = {}
            for street_key, segments_list in full_data.items():
                if segments_list and len(segments_list) > 0:
                    # Берем название из первого сегмента
                    original_name = segments_list[0].get("name", street_key)
                    self.streets_data[street_key] = {
                        "name": original_name,
                        "segments_count": len(segments_list),
                    }

            logger.info(
                "Streets data loaded successfully",
                streets_count=len(self.streets_data),
                source="full_file_optimized",
            )
            self.loaded = True

        except Exception as e:
            logger.error("Failed to load streets data", error=str(e))

    def find_street_geometry(
        self, street_name: str, fuzzy_threshold: int = 70, street_key: str = None
    ) -> StreetGeometry | None:
        """
        Находит геометрию улицы по названию с fuzzy matching

        Args:
            street_name: Название улицы для поиска
            fuzzy_threshold: Минимальный порог схожести для fuzzy matching

        Returns:
            StreetGeometry или None если не найдена
        """
        self._load_streets_data()

        if not self.streets_data:
            logger.warning("Streets data not available")
            return None

        logger.info(
            "Searching for street geometry",
            street_name=street_name,
            street_key=street_key,
            available_streets_count=len(self.streets_data),
        )

        # Если передан ключ, используем его напрямую
        if street_key and street_key in self.streets_data:
            logger.info("Direct key match found", street_key=street_key)
            return self._create_street_geometry_from_new_format(
                street_key, self.streets_data[street_key]
            )

        # Нормализуем название для поиска
        normalized_street_name = street_name.lower().strip()

        logger.info(
            "Normalized street name",
            original=street_name,
            normalized=normalized_street_name,
        )

        # Сначала пытаемся точное совпадение по нормализованному названию
        if normalized_street_name in self.streets_data:
            logger.info("Exact match found", street_name=street_name)
            return self._create_street_geometry_from_new_format(
                normalized_street_name, self.streets_data[normalized_street_name]
            )

        # Показываем несколько похожих названий для отладки
        street_names = list(self.streets_data.keys())
        similar_names = [name for name in street_names if "ландау" in name.lower()]
        logger.info(
            "Similar street names with 'ландау'", similar_names=similar_names[:10]
        )

        # Если точного совпадения нет, используем fuzzy matching
        matches = process.extract(
            normalized_street_name, street_names, limit=3, scorer=fuzz.ratio
        )
        logger.info("Top fuzzy matches", matches=matches)

        if matches and matches[0][1] >= fuzzy_threshold:
            best_match = matches[0][0]
            logger.info(
                "Fuzzy match found",
                street_name=street_name,
                matched_name=best_match,
                score=matches[0][1],
            )
            return self._create_street_geometry_from_new_format(
                best_match, self.streets_data[best_match]
            )

        logger.warning(
            "No street match found",
            street_name=street_name,
            threshold=fuzzy_threshold,
            best_match_score=matches[0][1] if matches else 0,
        )
        return None

    def _create_street_geometry_from_new_format(
        self, street_name: str, street_data: dict
    ) -> StreetGeometry:
        """
        Создает объект StreetGeometry из полного файла
        Возвращает все сегменты улицы как отдельные линии

        Args:
            street_name: Название улицы (нормализованный ключ)
            street_data: Данные улицы {name, segments_count}

        Returns:
            StreetGeometry объект с массивом сегментов
        """
        # Получаем все сегменты улицы из кэшированных данных
        all_segments = self._get_all_street_segments_cached(street_name)

        if not all_segments:
            logger.warning("No segments found for street", street_name=street_name)
            return None

        original_name = street_data.get("name", street_name)

        logger.info(
            "Created street geometry",
            street_name=original_name,
            segments_count=len(all_segments),
            total_points=sum(len(seg) for seg in all_segments),
        )

        # Создаем объект с сегментами
        geometry = StreetGeometry(
            name=original_name,
            coordinates=[],  # Пустой для множественных сегментов
            osm_type="way",
            osm_id=0,
        )

        # Добавляем поле segments
        geometry.segments = all_segments

        return geometry

    def _get_all_street_segments_cached(
        self, street_name: str
    ) -> list[list[list[float]]]:
        """
        Получает все сегменты улицы из кэшированных данных

        Args:
            street_name: Название улицы (нормализованный ключ)

        Returns:
            Список сегментов, где каждый сегмент - это список координат [[lon, lat], ...]
        """
        try:
            # Загружаем полные данные в память при первом обращении
            if not hasattr(self, "_full_data"):
                self._load_full_data()

            # Пробуем найти улицу по нормализованному ключу
            if street_name in self._full_data:
                segments_data = self._full_data[street_name]
                segments = []

                for segment_info in segments_data:
                    coordinates = segment_info.get("coordinates", [])
                    if coordinates:
                        segments.append(coordinates)

                return segments
            else:
                logger.warning(
                    "Street not found in cached full data", street_name=street_name
                )
                return []

        except Exception as e:
            logger.error(
                "Failed to get segments from cache",
                street_name=street_name,
                error=str(e),
            )
            return []

    def _load_full_data(self):
        """Загружает полные данные в память для быстрого доступа"""
        try:
            full_json_path = (
                Path(__file__).parent.parent.parent.parent
                / "frontend"
                / "static"
                / "data"
                / "kharkiv_streets_full.json"
            )

            if not full_json_path.exists():
                logger.error(
                    "Full streets data file not found", path=str(full_json_path)
                )
                self._full_data = {}
                return

            with open(full_json_path, encoding="utf-8") as f:
                self._full_data = json.load(f)

            logger.info(
                "Full data loaded into memory", total_streets=len(self._full_data)
            )

        except Exception as e:
            logger.error("Failed to load full data", error=str(e))
            self._full_data = {}

    def _create_street_geometry(
        self, street_name: str, points_data: list[dict]
    ) -> StreetGeometry:
        """
        Создает объект StreetGeometry из данных точек (старый формат)

        Args:
            street_name: Название улицы
            points_data: Список точек с координатами

        Returns:
            StreetGeometry объект
        """
        # Преобразуем точки в координаты для полилинии
        coordinates = []
        for point in points_data:
            if "lat" in point and "lon" in point:
                coordinates.append([float(point["lat"]), float(point["lon"])])

        logger.info(
            "Created street geometry",
            street_name=street_name,
            points_count=len(coordinates),
        )

        return StreetGeometry(
            name=street_name,
            coordinates=coordinates,
            osm_type="way",  # Устанавливаем по умолчанию
            osm_id=0,  # Устанавливаем по умолчанию, так как у нас нет ID
        )

    def get_available_streets_count(self) -> int:
        """Возвращает количество доступных улиц в кэше"""
        self._load_streets_data()
        return len(self.streets_data)

    def search_streets_by_prefix(self, prefix: str, limit: int = 10) -> list[dict]:
        """
        Поиск улиц по префиксу для автокомплита

        Args:
            prefix: Префикс для поиска
            limit: Максимальное количество результатов

        Returns:
            Список словарей с данными улиц: [{"name": "...", "key": "..."}]
        """
        self._load_streets_data()

        if not self.streets_data:
            return []

        prefix_lower = prefix.lower()
        matches = []
        seen_names = set()  # Для избежания дубликатов

        for street_key, street_data in self.streets_data.items():
            if prefix_lower in street_key:
                # Возвращаем оригинальное название из данных, а не ключ
                original_name = street_data.get("name", street_key)

                # Добавляем только если еще не видели это название
                if original_name not in seen_names:
                    matches.append(
                        {
                            "name": original_name,
                            "key": street_key,  # Сохраняем ключ для поиска геометрии
                        }
                    )
                    seen_names.add(original_name)

        # Сортируем по длине названия (более короткие названия сначала)
        matches.sort(key=lambda x: len(x["name"]))
        return matches[:limit]
