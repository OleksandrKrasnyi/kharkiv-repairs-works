import mapService from '../services/mapService.js';
import { useMapState } from './useMapState.js';

/**
 * Composable для работы с картой
 * Включает поддержку глобального состояния карты
 */
export function useMap() {
  const mapState = useMapState();

  return {
    // Инициализация с сохранением состояния
    initMap: () => mapState.initMapWithState(),

    // Управление состоянием карты
    saveSelectedStreet: mapState.saveSelectedStreet,
    clearSelectedStreet: mapState.clearSelectedStreet,
    getMapState: mapState.getMapState,
    resetMapState: mapState.resetMapState,

    // События
    onStreetCleared: mapState.onStreetCleared,
    offStreetCleared: mapState.offStreetCleared,

    // Маркеры
    addTempMarker: (latlng, options = {}) => mapService.addTempMarker(latlng, options),
    clearTempMarkers: () => mapService.clearTempMarkers(),

    // Работы на карте
    addWorkToMap: work => mapService.addWorkToMap(work),
    removeWorkFromMap: workId => mapService.removeWorkFromMap(workId),
    clearWorksFromMap: () => mapService.clearWorkMarkers(),
    loadWorksToMap: async works => await mapService.addAllWorksToMap(works),

    // Улицы и сегменты
    highlightStreet: geometry => mapService.highlightStreet(geometry),
    clearHighlightedStreet: () => mapService.clearHighlightedStreet(),
    showSelectedSegment: result => mapService.displayCalculatedSegment(result),
    displayCalculatedSegment: result => mapService.displayCalculatedSegment(result),
    clearSelectedSegment: () => mapService.clearSelectedSegment(),

    // Обработчики событий
    onMapClick: callback => mapService.setMapClickCallback(callback),
    offMapClick: () => mapService.setMapClickCallback(null),

    // Получение данных
    getCurrentPoint: () => mapService.getCurrentPoint(),

    // Утилиты
    fitBounds: (coordinates, options) => mapService.fitBounds(coordinates, options),
    fitBoundsForSegments: (segments, options) =>
      mapService.fitBoundsForSegments(segments, options),
    fitToBounds: bounds => mapService.fitToBounds(bounds),
    setView: (latlng, zoom) => mapService.setView(latlng, zoom),

    // Прямой доступ к объекту карты (для сложных случаев)
    getMapInstance: () => mapService.map
  };
}
