/**
 * Центральный экспорт всех composables
 * Упрощает импорт в компонентах
 */

export { useApi } from './useApi.js';
export { useMap } from './useMap.js';
export { useNotifications } from './useNotifications.js';
export { useRouter } from './useRouter.js';

/**
 * Пример использования:
 *
 * import { useApi, useMap, useNotifications } from '../composables/index.js';
 *
 * setup() {
 *   const api = useApi();
 *   const map = useMap();
 *   const { showError, showSuccess } = useNotifications();
 *
 *   // ...
 * }
 */
