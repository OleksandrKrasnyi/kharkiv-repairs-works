import apiService from '../services/apiService.js';

/**
 * Composable для работы с API
 * Заменяет глобальный window.apiService
 */
export function useApi() {
  return {
    // Типы работ
    getWorkTypes: () => apiService.getWorkTypes(),
    createWorkType: workType => apiService.createWorkType(workType),
    updateWorkType: (typeId, workType) => apiService.updateWorkType(typeId, workType),
    deleteWorkType: typeId => apiService.deleteWorkType(typeId),

    // Улицы
    searchStreets: query => apiService.searchStreets(query),
    getStreetGeometry: streetName => apiService.getStreetGeometry(streetName),
    getStreetGeometryByOsm: (osmType, osmId) =>
      apiService.getStreetGeometryByOsm(osmType, osmId),
    reverseGeocode: (lat, lon) => apiService.reverseGeocode(lat, lon),
    calculateStreetSegment: segmentData =>
      apiService.calculateStreetSegment(segmentData),

    // Ремонтные работы
    getRepairWorks: (filters = {}) => apiService.getRepairWorks(filters),
    getRepairWork: workId => apiService.getRepairWork(workId),
    createRepairWork: workData => apiService.createRepairWork(workData),
    updateRepairWork: (workId, workData) =>
      apiService.updateRepairWork(workId, workData),
    deleteRepairWork: workId => apiService.deleteRepairWork(workId),

    // Фотографии ремонтных работ
    getRepairWorkPhotos: workId => apiService.getRepairWorkPhotos(workId),
    uploadRepairWorkPhoto: (workId, file, description, sortOrder) =>
      apiService.uploadRepairWorkPhoto(workId, file, description, sortOrder),
    updateRepairWorkPhoto: (workId, photoId, updateData) =>
      apiService.updateRepairWorkPhoto(workId, photoId, updateData),
    deleteRepairWorkPhoto: (workId, photoId) =>
      apiService.deleteRepairWorkPhoto(workId, photoId),
    getRepairWorkPhotoUrl: (workId, photoId) =>
      apiService.getRepairWorkPhotoUrl(workId, photoId),

    // Алиасы для совместимости с существующими компонентами
    fetchWorkTypes: () => apiService.getWorkTypes(),
    fetchRepairWorks: (filters = {}) => apiService.getRepairWorks(filters)
  };
}
