import { ref, reactive } from 'vue';
import mapService from '../services/mapService.js';

// Глобальное состояние карты
// Сохраняется между переключениями вкладок
const mapState = reactive({
  isInitialized: false,
  center: [49.9935, 36.2304], // Харьков
  zoom: 12,
  selectedStreet: null,
  selectedStreetGeometry: null,
  highlightedStreetLayer: null
});

// Событийная система для уведомления компонентов
const eventCallbacks = {
  streetCleared: []
};

const mapInstance = ref(null);

/**
 * Composable для глобального состояния карты
 * Обеспечивает сохранение состояния между вкладками
 */
export function useMapState() {
  /**
   * Инициализация карты с восстановлением состояния
   */
  const initMapWithState = async () => {
    try {
      console.log('🗺️ MapState: Инициализация карты с сохранением состояния...');

      // Если карта уже инициализирована, но DOM контейнер изменился - пересоздаем
      const mapElement = document.getElementById('map');
      if (mapState.isInitialized && mapService.map) {
        const currentContainer = mapService.map.getContainer();

        // Если контейнер изменился или недоступен - пересоздаем карту
        if (!currentContainer || currentContainer !== mapElement) {
          console.log('MapState: DOM контейнер изменился, пересоздаем карту...');
          mapService.destroyMap();
        } else {
          console.log(
            'MapState: Карта уже инициализирована, восстанавливаем состояние...'
          );
          await restoreMapState();
          await waitForMapReady();
          return mapService.map;
        }
      }

      // Инициализируем карту сразу с правильными координатами
      const initialCenter = mapState.isInitialized ? mapState.center : null;
      const initialZoom = mapState.isInitialized ? mapState.zoom : null;

      const map = await mapService.initMap(0, initialCenter, initialZoom);
      mapInstance.value = map;

      // Ждем полной готовности карты
      await waitForMapReady();

      if (mapState.isInitialized) {
        console.log(
          `🗺️ MapState: Карта инициализирована с сохраненной позицией: ${mapState.center}, зум: ${mapState.zoom}`
        );
      }

      // Восстанавливаем выбранную улицу
      if (mapState.selectedStreet && mapState.selectedStreetGeometry) {
        console.log(`🗺️ MapState: Восстанавливаем улицу: ${mapState.selectedStreet}`);
        mapService.highlightStreet(mapState.selectedStreetGeometry);
      }

      // Добавляем обработчики для отслеживания изменений
      map.on('moveend', saveMapPosition);
      map.on('zoomend', saveMapPosition);

      mapState.isInitialized = true;
      console.log('MapState: Карта инициализирована с состоянием');

      return map;
    } catch (error) {
      console.error('MapState: Ошибка инициализации карты:', error);
      throw error;
    }
  };

  /**
   * Ожидание готовности карты
   */
  const waitForMapReady = async (maxAttempts = 10) => {
    for (let i = 0; i < maxAttempts; i++) {
      if (mapService.isMapReady()) {
        console.log('MapState: Карта готова к работе');
        return true;
      }

      console.log(
        `MapState: Ожидание готовности карты (попытка ${i + 1}/${maxAttempts})...`
      );
      await new Promise(resolve => setTimeout(resolve, 100));

      // Принудительно обновляем размер карты
      if (mapService.map) {
        mapService.map.invalidateSize();
      }
    }

    console.warn('⚠️ MapState: Карта не готова после ожидания');
    return false;
  };

  /**
   * Сохранение текущей позиции и зума карты
   */
  const saveMapPosition = () => {
    if (mapService.map) {
      const center = mapService.map.getCenter();
      const zoom = mapService.map.getZoom();

      mapState.center = [center.lat, center.lng];
      mapState.zoom = zoom;

      console.log(
        `💾 MapState: Сохранена позиция: [${center.lat.toFixed(4)}, ${center.lng.toFixed(4)}], зум: ${zoom}`
      );
    }
  };

  /**
   * Восстановление состояния карты
   */
  const restoreMapState = async () => {
    if (!mapService.map) return;

    // Восстанавливаем позицию без анимации
    mapService.setViewInstant(mapState.center, mapState.zoom);

    console.log(
      `MapState: Мгновенно восстановлена позиция: ${mapState.center}, зум: ${mapState.zoom}`
    );

    // Восстанавливаем выбранную улицу
    if (mapState.selectedStreet && mapState.selectedStreetGeometry) {
      mapService.highlightStreet(mapState.selectedStreetGeometry);
    }
  };

  /**
   * Сохранение выбранной улицы
   */
  const saveSelectedStreet = (streetName, geometry) => {
    mapState.selectedStreet = streetName;
    mapState.selectedStreetGeometry = geometry;
    console.log(`💾 MapState: Сохранена выбранная улица: ${streetName}`);
  };

  /**
   * Очистка выбранной улицы
   */
  const clearSelectedStreet = () => {
    mapState.selectedStreet = null;
    mapState.selectedStreetGeometry = null;

    // Уведомляем все компоненты об очистке улицы
    eventCallbacks.streetCleared.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('MapState: Ошибка в callback streetCleared:', error);
      }
    });

    console.log('🗑️ MapState: Очищена выбранная улица');
  };

  /**
   * Подписка на событие очистки улицы
   */
  const onStreetCleared = callback => {
    eventCallbacks.streetCleared.push(callback);
    console.log('📡 MapState: Добавлена подписка на очистку улицы');
  };

  /**
   * Отписка от события очистки улицы
   */
  const offStreetCleared = callback => {
    const index = eventCallbacks.streetCleared.indexOf(callback);
    if (index > -1) {
      eventCallbacks.streetCleared.splice(index, 1);
      console.log('📡 MapState: Удалена подписка на очистку улицы');
    }
  };

  /**
   * Получение текущего состояния карты
   */
  const getMapState = () => {
    return {
      isInitialized: mapState.isInitialized,
      center: [...mapState.center],
      zoom: mapState.zoom,
      selectedStreet: mapState.selectedStreet,
      hasSelectedStreet: !!mapState.selectedStreet
    };
  };

  /**
   * Сброс состояния карты к начальному
   */
  const resetMapState = () => {
    mapState.center = [49.9935, 36.2304];
    mapState.zoom = 12;
    mapState.selectedStreet = null;
    mapState.selectedStreetGeometry = null;

    if (mapService.map) {
      // Сброс без анимации
      mapService.setViewInstant(mapState.center, mapState.zoom);
      mapService.clearHighlightedStreet();
    }

    console.log('MapState: Состояние карты сброшено без анимации');
  };

  return {
    // Состояние
    mapState: mapState,

    // Методы
    initMapWithState,
    saveMapPosition,
    restoreMapState,
    saveSelectedStreet,
    clearSelectedStreet,
    getMapState,
    resetMapState,

    // События
    onStreetCleared,
    offStreetCleared
  };
}
