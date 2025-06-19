// Импорт Leaflet
import L from 'leaflet';

// Импорт CSS стилей Leaflet
import 'leaflet/dist/leaflet.css';

// Исправляем иконки Leaflet (проблема с webpack/vite)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-icon-2x.png',
  iconUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-icon.png',
  shadowUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-shadow.png'
});

/**
 * Сервис для работы с Leaflet картой
 * Управляет картой, маркерами, слоями и взаимодействием с пользователем
 */

// Конфигурация карты
const MAP_CONFIG = {
  DEFAULT_CENTER: [49.9935, 36.2304], // Харьков
  DEFAULT_ZOOM: 12,
  TILE_LAYER_URL: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  TILE_LAYER_OPTIONS: {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  },
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 500
};

/**
 * Класс для управления Leaflet картой
 */
class MapService {
  constructor(containerId = 'map') {
    this.containerId = containerId;
    this.map = null;
    this.tempMarkers = [];
    this.workMarkers = [];
    this.highlightedStreet = null;
    this.selectedSegmentLayer = null;
    this.selectedSegmentPopup = null;

    // Callback функции для событий
    this.onMapClickCallback = null;
    this.onMapReadyCallback = null;
    this.lastClickedPoint = null;
  }

  /**
   * Инициализация карты
   */
  async initMap(retryCount = 0, initialCenter = null, initialZoom = null) {
    try {
      const mapElement = document.getElementById(this.containerId);
      if (!mapElement) {
        if (retryCount < MAP_CONFIG.RETRY_ATTEMPTS) {
          await this.delay(MAP_CONFIG.RETRY_DELAY);
          return this.initMap(retryCount + 1);
        }
        throw new Error(`Контейнер карты с ID "${this.containerId}" не найден`);
      }

      if (typeof L === 'undefined') {
        throw new Error('Leaflet не загружен');
      }

      // Если карта уже существует, удаляем её
      if (this.map) {
        this.destroyMap();
      }

      // Создаем карту с правильными начальными координатами и плавным зумом
      const center = initialCenter || MAP_CONFIG.DEFAULT_CENTER;
      const zoom = initialZoom || MAP_CONFIG.DEFAULT_ZOOM;

      this.map = L.map(this.containerId, {
        // Включаем анимации для пользовательских действий
        zoomAnimation: true, // Плавный зум колесиком мыши
        fadeAnimation: true, // Плавное появление тайлов
        markerZoomAnimation: true, // Анимация маркеров при зуме
        zoomAnimationThreshold: 4, // Анимация для изменений зума до 4 уровней
        // Настройки плавности зума
        wheelPxPerZoomLevel: 60, // Чувствительность колесика (по умолчанию 60)
        wheelDebounceTime: 40 // Задержка между событиями колесика (по умолчанию 40)
      }).setView(center, zoom, {
        animate: false, // Без анимации ТОЛЬКО при начальной установке
        duration: 0 // Мгновенная начальная установка
      });

      // Добавляем слой тайлов
      L.tileLayer(MAP_CONFIG.TILE_LAYER_URL, MAP_CONFIG.TILE_LAYER_OPTIONS).addTo(
        this.map
      );

      // Добавляем обработчик кликов
      this.map.on('click', e => {
        // Сохраняем последний клик для getCurrentPoint
        this.lastClickedPoint = { lat: e.latlng.lat, lng: e.latlng.lng };

        if (this.onMapClickCallback) {
          this.onMapClickCallback(e);
        }
      });

      // Вызываем callback если есть
      if (this.onMapReadyCallback) {
        this.onMapReadyCallback();
      }

      return this.map;
    } catch (error) {
      console.error('Ошибка инициализации карты:', error);

      if (retryCount < MAP_CONFIG.RETRY_ATTEMPTS) {
        await this.delay(MAP_CONFIG.RETRY_DELAY * (retryCount + 1));
        return this.initMap(retryCount + 1, initialCenter, initialZoom);
      }

      throw error;
    }
  }

  /**
   * Уничтожение карты
   */
  destroyMap() {
    if (this.map) {
      this.clearAllMarkers();
      this.clearHighlightedStreet();
      this.clearSelectedSegment();
      this.map.remove();
      this.map = null;
    }
  }

  /**
   * Проверка готовности карты
   */
  isMapReady() {
    const isReady = this.map !== null;
    if (isReady) {
      const container = this.map.getContainer();
      return container && container.offsetWidth > 0 && container.offsetHeight > 0;
    }
    return false;
  }

  /**
   * Обновление размера карты
   */
  invalidateSize() {
    if (this.map) {
      this.map.invalidateSize();
    }
  }

  /**
   * Установка callback для клика по карте
   */
  setMapClickCallback(callback) {
    this.onMapClickCallback = callback;
  }

  /**
   * Установка callback для готовности карты
   */
  setMapReadyCallback(callback) {
    this.onMapReadyCallback = callback;
  }

  // ===== МАРКЕРЫ РАБОТ =====

  /**
   * Добавление всех работ на карту
   */
  async addAllWorksToMap(repairWorks) {
    console.log(
      `📍 MapService: Загрузка ${repairWorks?.length || 0} работ на карту...`
    );

    // Retry логика для ожидания готовности карты
    if (!(await this.waitForMapReady())) {
      console.warn(
        '⚠️ MapService: Карта не готова после ожидания, пропускаем загрузку работ'
      );
      return;
    }

    // Get current work IDs on map
    const currentWorkIds = this.workMarkers.map(wm => wm.id);
    const newWorkIds = repairWorks.map(work =>
      typeof work.id === 'string' ? parseInt(work.id, 10) : work.id
    );

    // Remove markers for works that are no longer in the list
    const workIdsToRemove = currentWorkIds.filter(id => !newWorkIds.includes(id));
    if (workIdsToRemove.length > 0) {
      workIdsToRemove.forEach(workId => {
        this.removeWorkFromMap(workId);
      });
    }

    // Add markers for new works
    repairWorks.forEach(work => {
      this.addWorkToMap(work);
    });
  }

  /**
   * Ожидание готовности карты с retry
   */
  async waitForMapReady(maxAttempts = 10) {
    for (let i = 0; i < maxAttempts; i++) {
      if (this.isMapReady()) {
        console.log('MapService: Карта готова к загрузке работ');
        return true;
      }

      console.log(
        `MapService: Ожидание готовности карты (попытка ${i + 1}/${maxAttempts})...`
      );
      await this.delay(100);

      // Принудительно обновляем размер карты
      if (this.map) {
        this.map.invalidateSize();
      }
    }

    return false;
  }

  /**
   * Добавление отдельной работы на карту
   */
  addWorkToMap(work) {
    if (!this.isMapReady()) {
      return;
    }

    // Ensure ID is normalized for consistent comparison
    const workId = typeof work.id === 'string' ? parseInt(work.id, 10) : work.id;

    // Check if marker already exists
    const existingMarkerIndex = this.workMarkers.findIndex(wm => wm.id === workId);
    if (existingMarkerIndex !== -1) {
      return;
    }

    const popupContent = this.createPopupContent(work);
    let marker;

    // Определяем тип работы по наличию данных
    const isPointWork =
      work.location || (work.latitude != null && work.longitude != null);

    if (isPointWork) {
      marker = this.createPointMarker(work, popupContent);
    } else {
      marker = this.createRouteMarker(work, popupContent);
    }

    if (marker) {
      this.workMarkers.push({
        id: workId,
        marker: marker
      });
    }
  }

  /**
   * Создание точечного маркера
   */
  createPointMarker(work, popupContent) {
    const color = work.work_type ? work.work_type.color : '#667eea';
    let lat, lng;

    // Получаем координаты
    if (work.latitude != null && work.longitude != null) {
      lat = work.latitude;
      lng = work.longitude;
    } else if (work.location && typeof work.location === 'string') {
      const coords = work.location.split(',').map(coord => parseFloat(coord.trim()));
      if (coords.length === 2 && !isNaN(coords[0]) && !isNaN(coords[1])) {
        lat = coords[0];
        lng = coords[1];
      }
    }

    if (lat == null || lng == null || isNaN(lat) || isNaN(lng)) {
      return null;
    }

    return L.marker([lat, lng], {
      icon: L.divIcon({
        className: 'work-marker point',
        html: `<div style="background: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      })
    })
      .bindPopup(popupContent)
      .addTo(this.map);
  }

  /**
   * Создание маршрутного маркера или сегмента улицы
   */
  createRouteMarker(work, popupContent) {
    const color = work.work_type ? work.work_type.color : '#667eea';

    // Проверяем, есть ли GeoJSON геометрия сегмента улицы
    if (work.street_segment_geojson) {
      try {
        const segmentGeoJSON = JSON.parse(work.street_segment_geojson);

        const { coordinates } = segmentGeoJSON.geometry;
        const latlngs = coordinates.map(coord => [coord[1], coord[0]]);

        const segmentLine = L.polyline(latlngs, {
          color: color,
          weight: 6,
          opacity: 0.8,
          className: 'street-segment-work',
          lineCap: 'round',
          lineJoin: 'round'
        })
          .bindPopup(popupContent)
          .addTo(this.map);

        // Оставляем только линию сегмента для чистого отображения
        if (latlngs.length > 0) {
          // Возвращаем только линию сегмента без маркеров
          return segmentLine;
        }

        return segmentLine;
      } catch {
        // Игнорируем ошибки парсинга GeoJSON
      }
    }

    // Обычный маршрут
    return this.createSimpleRoute(work, color, popupContent);
  }

  /**
   * Создание простого маршрута
   */
  createSimpleRoute(work, color, popupContent) {
    let startLat, startLng, endLat, endLng;

    // Получаем координаты маршрута
    if (
      work.start_latitude != null &&
      work.start_longitude != null &&
      work.end_latitude != null &&
      work.end_longitude != null
    ) {
      startLat = work.start_latitude;
      startLng = work.start_longitude;
      endLat = work.end_latitude;
      endLng = work.end_longitude;
    } else if (work.start_location && work.end_location) {
      const startCoords = work.start_location
        .split(',')
        .map(coord => parseFloat(coord.trim()));
      const endCoords = work.end_location
        .split(',')
        .map(coord => parseFloat(coord.trim()));

      if (
        startCoords.length === 2 &&
        endCoords.length === 2 &&
        !isNaN(startCoords[0]) &&
        !isNaN(startCoords[1]) &&
        !isNaN(endCoords[0]) &&
        !isNaN(endCoords[1])
      ) {
        startLat = startCoords[0];
        startLng = startCoords[1];
        endLat = endCoords[0];
        endLng = endCoords[1];
      }
    }

    if (
      startLat == null ||
      startLng == null ||
      endLat == null ||
      endLng == null ||
      isNaN(startLat) ||
      isNaN(startLng) ||
      isNaN(endLat) ||
      isNaN(endLng)
    ) {
      return null;
    }

    // Создаем линию маршрута
    const routeLine = L.polyline(
      [
        [startLat, startLng],
        [endLat, endLng]
      ],
      {
        color: color,
        weight: 4,
        opacity: 0.8
      }
    )
      .bindPopup(popupContent)
      .addTo(this.map);

    // Оставляем только линию маршрута для чистого отображения

    return routeLine;
  }

  /**
   * Создание контента для popup
   */
  createPopupContent(work) {
    const workType = work.work_type ? work.work_type.name : 'Невідомий тип';
    const startDate = this.formatDateTime(work.start_datetime);
    const endDate = work.end_datetime
      ? this.formatDateTime(work.end_datetime)
      : 'триває';

    let location = 'Не вказано';
    try {
      location = this.getWorkLocation(work) || 'Не вказано';
    } catch {
      // Игнорируем ошибки получения местоположения
    }

    return `
      <div class="popup-content">
        <h4><i class="fas fa-tools"></i> ${work.description || 'Ремонтні роботи'}</h4>
        <p><strong>Тип:</strong> ${workType}</p>
        <p><strong>Період:</strong> ${startDate} - ${endDate}</p>
        <p><strong>Місце:</strong> ${location}</p>
      </div>
    `;
  }

  /**
   * Получение местоположения работы для отображения
   */
  getWorkLocation(work) {
    // Сегмент улицы
    if (work.street_name && work.street_segment_geojson) {
      return `🛣️ ${work.street_name} (сегмент)`;
    }

    // Точечная работа
    const isPointWork =
      work.location || (work.latitude != null && work.longitude != null);
    if (isPointWork) {
      if (work.latitude != null && work.longitude != null) {
        return `${work.latitude.toFixed(4)}, ${work.longitude.toFixed(4)}`;
      } else if (work.location && typeof work.location === 'string') {
        const coords = work.location.split(',').map(coord => coord.trim());
        if (coords.length === 2) {
          const lat = parseFloat(coords[0]);
          const lng = parseFloat(coords[1]);
          if (!isNaN(lat) && !isNaN(lng)) {
            return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
          }
        }
        return work.location;
      }
    }

    // Маршрутная работа
    const isSectionWork =
      work.start_location ||
      (work.start_latitude != null && work.start_longitude != null);
    if (isSectionWork) {
      if (
        work.start_latitude != null &&
        work.start_longitude != null &&
        work.end_latitude != null &&
        work.end_longitude != null
      ) {
        return `${work.start_latitude.toFixed(4)}, ${work.start_longitude.toFixed(4)} → ${work.end_latitude.toFixed(4)}, ${work.end_longitude.toFixed(4)}`;
      } else if (work.start_location && work.end_location) {
        return `${work.start_location} → ${work.end_location}`;
      }
    }

    return 'Местоположение не указано';
  }

  /**
   * Удаление работы с карты
   */
  removeWorkFromMap(workId) {
    // Normalize workId to number for consistent comparison
    const normalizedWorkId = typeof workId === 'string' ? parseInt(workId, 10) : workId;

    if (!this.isMapReady()) {
      return false;
    }

    // Try both strict and loose comparison for safety
    let workMarkerIndex = this.workMarkers.findIndex(wm => wm.id === normalizedWorkId);
    if (workMarkerIndex === -1) {
      // Try string comparison as fallback
      workMarkerIndex = this.workMarkers.findIndex(
        wm => wm.id.toString() === workId.toString()
      );
    }

    if (workMarkerIndex !== -1) {
      const workMarker = this.workMarkers[workMarkerIndex];

      if (workMarker.marker && this.map) {
        // Handle LayerGroup (for complex markers like street segments)
        if (workMarker.marker instanceof L.LayerGroup) {
          // Remove each layer individually first
          workMarker.marker.eachLayer(layer => {
            if (this.map.hasLayer(layer)) {
              this.map.removeLayer(layer);
            }
          });

          // Clear and remove the group
          workMarker.marker.clearLayers();
          if (this.map.hasLayer(workMarker.marker)) {
            this.map.removeLayer(workMarker.marker);
          }
        } else if (this.map.hasLayer(workMarker.marker)) {
          this.map.removeLayer(workMarker.marker);
        }

        // Force remove marker reference
        workMarker.marker = null;
      }

      this.workMarkers.splice(workMarkerIndex, 1);
      return true;
    }

    return false;
  }

  // ===== ВРЕМЕННЫЕ МАРКЕРЫ =====

  /**
   * Добавление временного маркера
   */
  addTempMarker(latlng, options = {}) {
    if (!this.isMapReady()) return null;

    const defaultOptions = {
      icon: L.divIcon({
        className: 'temp-marker',
        html: '<div style="background: #4CAF50; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      })
    };

    const marker = L.marker(latlng, { ...defaultOptions, ...options }).addTo(this.map);
    this.tempMarkers.push(marker);
    return marker;
  }

  /**
   * Очистка временных маркеров
   */
  clearTempMarkers() {
    this.tempMarkers.forEach(marker => {
      if (this.map && this.map.hasLayer(marker)) {
        this.map.removeLayer(marker);
      }
    });
    this.tempMarkers = [];
  }

  /**
   * Очистка маркеров работ
   */
  clearWorkMarkers() {
    this.workMarkers.forEach(workMarker => {
      if (workMarker.marker && this.map && this.map.hasLayer(workMarker.marker)) {
        this.map.removeLayer(workMarker.marker);
      }
    });
    this.workMarkers = [];
  }

  /**
   * Очистка всех маркеров
   */
  clearAllMarkers() {
    this.clearTempMarkers();
    this.clearWorkMarkers();
  }

  // ===== ПОДСВЕТКА УЛИЦ =====

  /**
   * Подсветка улицы по геометрии
   */
  highlightStreet(geometry) {
    if (!this.isMapReady()) return;

    this.clearHighlightedStreet();

    if (geometry.segments && geometry.segments.length > 0) {
      // Множественные сегменты
      const streetGroup = L.layerGroup();

      geometry.segments.forEach(segmentCoords => {
        if (segmentCoords.length >= 2) {
          const segmentLine = L.polyline(segmentCoords, {
            color: '#ff6b6b',
            weight: 5,
            opacity: 0.9,
            className: 'highlighted-street',
            smoothFactor: 1.0,
            lineCap: 'round',
            lineJoin: 'round'
          });
          streetGroup.addLayer(segmentLine);
        }
      });

      streetGroup.addTo(this.map);
      this.highlightedStreet = streetGroup;

      // Улучшенная центровка для множественных сегментов
      this.fitBoundsForSegments(geometry.segments);
    } else if (geometry.coordinates && geometry.coordinates.length > 0) {
      // Одиночная линия
      const streetLine = L.polyline(geometry.coordinates, {
        color: '#ff6b6b',
        weight: 5,
        opacity: 0.9,
        className: 'highlighted-street',
        smoothFactor: 1.0,
        lineCap: 'round',
        lineJoin: 'round'
      });

      streetLine.addTo(this.map);
      this.highlightedStreet = streetLine;

      // Подгоняем карту под улицу
      this.fitBounds(geometry.coordinates);
    }
  }

  /**
   * Очистка подсветки улицы
   */
  clearHighlightedStreet() {
    if (this.highlightedStreet && this.map) {
      if (this.highlightedStreet instanceof L.LayerGroup) {
        this.highlightedStreet.clearLayers();
      }
      this.map.removeLayer(this.highlightedStreet);
      this.highlightedStreet = null;
    }
  }

  // ===== СЕГМЕНТЫ =====

  /**
   * Отображение вычисленного сегмента
   */
  displayCalculatedSegment(calculatedSegment) {
    if (
      !calculatedSegment ||
      !calculatedSegment.segment_geojson ||
      !this.isMapReady()
    ) {
      return;
    }

    // Очищаем предыдущий сегмент
    this.clearSelectedSegment();

    const segmentCoords = calculatedSegment.segment_geojson.geometry.coordinates;
    const latLngCoords = segmentCoords.map(coord => [coord[1], coord[0]]);

    this.selectedSegmentLayer = L.polyline(latLngCoords, {
      color: '#ff6b6b',
      weight: 8,
      opacity: 0.9,
      className: 'selected-segment',
      lineCap: 'round',
      lineJoin: 'round'
    }).addTo(this.map);

    // Показываем popup с информацией о сегменте
    const center = this.getPolylineCenter(latLngCoords);
    this.selectedSegmentPopup = L.popup()
      .setLatLng(center)
      .setContent(
        `
        <div style="text-align: center;">
          <strong>🎯 Обраний сегмент</strong><br>
          <small>📏 Довжина: ${Math.round(calculatedSegment.distance_meters)} м</small><br>
          <small>🛣️ ${calculatedSegment.street_name}</small>
        </div>
      `
      )
      .openOn(this.map);
  }

  /**
   * Очистка выбранного сегмента
   */
  clearSelectedSegment() {
    if (this.selectedSegmentLayer && this.map) {
      this.map.removeLayer(this.selectedSegmentLayer);
      this.selectedSegmentLayer = null;
    }

    // Закрываем popup сегмента если он открыт
    if (this.selectedSegmentPopup && this.map) {
      this.map.closePopup(this.selectedSegmentPopup);
      this.selectedSegmentPopup = null;
    }
  }

  // ===== УТИЛИТЫ =====

  /**
   * Улучшенная подгонка карты под сегменты улицы
   */
  fitBoundsForSegments(segments, options = {}) {
    if (!this.isMapReady() || !segments || segments.length === 0) return;

    try {
      const bounds = L.latLngBounds();
      let totalPoints = 0;

      // Обрабатываем каждый сегмент отдельно
      segments.forEach(segment => {
        if (Array.isArray(segment) && segment.length >= 2) {
          segment.forEach(coord => {
            if (Array.isArray(coord) && coord.length >= 2) {
              bounds.extend([coord[0], coord[1]]);
              totalPoints++;
            }
          });
        }
      });

      if (bounds.isValid() && totalPoints > 0) {
        // Адаптивные настройки в зависимости от количества сегментов
        const enhancedOptions = {
          padding: segments.length > 10 ? [50, 50] : [30, 30],
          maxZoom: segments.length > 5 ? 15 : 16,
          animate: true,
          duration: 0.8,
          ...options
        };

        this.map.fitBounds(bounds, enhancedOptions);
      } else {
        console.warn('⚠️ MapService: Не удалось создать границы для сегментов');
      }
    } catch (error) {
      console.error('MapService: Ошибка центровки сегментов', error);
    }
  }

  /**
   * Подгонка карты под координаты
   */
  fitBounds(coordinates, options = { padding: [20, 20] }) {
    if (!this.isMapReady() || !coordinates || coordinates.length === 0) return;

    try {
      // Создаем границы и добавляем все точки
      const bounds = L.latLngBounds();

      // Проверяем формат координат и добавляем их правильно
      coordinates.forEach(coord => {
        if (Array.isArray(coord) && coord.length >= 2) {
          // Координата в формате [lat, lng] или [lng, lat]
          if (typeof coord[0] === 'number' && typeof coord[1] === 'number') {
            bounds.extend([coord[0], coord[1]]);
          }
        }
      });

      // Проверяем что границы валидны
      if (bounds.isValid()) {
        // Улучшенные настройки отступов для лучшей центровки
        const enhancedOptions = {
          padding: [30, 30], // Больше отступы
          maxZoom: 16, // Ограничиваем максимальный зум для лучшего обзора
          ...options
        };

        this.map.fitBounds(bounds, enhancedOptions);
      } else {
        console.warn('⚠️ MapService: Невалидные границы для координат', coordinates);
      }
    } catch (error) {
      console.error('MapService: Ошибка установки границ', error);
    }
  }

  /**
   * Центрирование карты
   */
  /**
   * Установка позиции и зума карты
   * @param {Array} center - Координаты центра [lat, lng]
   * @param {number} zoom - Уровень зума
   * @param {Object} options - Опции анимации
   */
  setView(center, zoom = MAP_CONFIG.DEFAULT_ZOOM, options = {}) {
    if (!this.isMapReady()) return;

    // По умолчанию используем анимацию для пользовательских действий
    const defaultOptions = {
      animate: true,
      duration: 0.25 // Быстрая анимация 250ms
    };

    this.map.setView(center, zoom, { ...defaultOptions, ...options });
  }

  /**
   * Мгновенная установка позиции без анимации (для восстановления состояния)
   */
  setViewInstant(center, zoom = MAP_CONFIG.DEFAULT_ZOOM) {
    this.setView(center, zoom, {
      animate: false,
      duration: 0
    });
  }

  /**
   * Вычисление центра полилинии
   */
  getPolylineCenter(coordinates) {
    if (coordinates.length === 0) return [0, 0];

    let totalLat = 0;
    let totalLng = 0;

    for (const coord of coordinates) {
      totalLat += coord[0];
      totalLng += coord[1];
    }

    return [totalLat / coordinates.length, totalLng / coordinates.length];
  }

  /**
   * Форматирование даты и времени
   */
  formatDateTime(dateStr) {
    if (!dateStr) return '';

    try {
      const date = new Date(dateStr);
      return date.toLocaleString('uk-UA', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  /**
   * Задержка
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Создаем единственный экземпляр сервиса
const mapService = new MapService();

mapService.getCurrentPoint = function () {
  // Возвращаем последний кликнутый маркер или центр карты
  if (this.lastClickedPoint) {
    return this.lastClickedPoint;
  }
  if (this.isMapReady()) {
    const center = this.map.getCenter();
    return { lat: center.lat, lng: center.lng };
  }
  return null;
};

export default mapService;
