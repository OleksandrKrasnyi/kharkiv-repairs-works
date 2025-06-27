/**
 * Централизованный API сервис для работы с бэкендом
 * Содержит все HTTP запросы и логику обработки ошибок
 */

// Базовая конфигурация API
const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000
};

/**
 * Определяет базовый URL для API в зависимости от окружения
 */
function getApiBaseUrl() {
  // Проверяем, работаем ли мы в режиме разработки
  const isDevelopment =
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.port === '3000';

  if (isDevelopment) {
    // В локальной разработке используем полный URL к бекенду
    return 'http://localhost:8000';
  } else {
    // В продакшене используем относительные URL (тот же домен)
    return '';
  }
}

/**
 * Утилиты для работы с HTTP запросами
 */
class HttpClient {
  constructor(config = {}) {
    this.baseURL = config.baseURL || API_CONFIG.BASE_URL;
    this.timeout = config.timeout || API_CONFIG.TIMEOUT;
    this.retryAttempts = config.retryAttempts || API_CONFIG.RETRY_ATTEMPTS;
    this.retryDelay = config.retryDelay || API_CONFIG.RETRY_DELAY;
  }

  /**
   * Создает AbortController с таймаутом
   */
  createAbortController() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, this.timeout);

    return { controller, timeoutId };
  }

  /**
   * Задержка для retry логики
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Выполняет HTTP запрос с retry логикой
   */
  async request(url, options = {}, attempt = 1) {
    const { controller, timeoutId } = this.createAbortController();

    try {
      const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;

      const response = await fetch(fullUrl, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorDetails = await this.parseErrorResponse(response);
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorDetails
        );
      }
      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      // Если это последняя попытка или ошибка не подходит для retry
      if (attempt >= this.retryAttempts || !this.shouldRetry(error)) {
        throw error;
      }

      // Ждем перед повторной попыткой
      const retryDelay = this.retryDelay * attempt;
      await this.delay(retryDelay);
      return this.request(url, options, attempt + 1);
    }
  }

  /**
   * Определяет, стоит ли повторить запрос
   */
  shouldRetry(error) {
    // Не повторяем для клиентских ошибок (4xx)
    if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
      return false;
    }

    // Повторяем для сетевых ошибок и серверных ошибок (5xx)
    return (
      error.name === 'AbortError' ||
      error.name === 'TypeError' ||
      (error instanceof ApiError && error.status >= 500)
    );
  }

  /**
   * Парсит ответ с ошибкой
   */
  async parseErrorResponse(response) {
    try {
      const data = await response.json();
      // Обрабатываем FastAPI/Pydantic ошибки валидации
      if (data.detail && Array.isArray(data.detail)) {
        return data.detail;
      }
      return data.detail || data.message || data;
    } catch {
      return response.statusText;
    }
  }

  // HTTP методы
  async get(url, options = {}) {
    const response = await this.request(url, { method: 'GET', ...options });
    return response.json();
  }

  async post(url, data, options = {}) {
    const response = await this.request(url, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options
    });
    return response.json();
  }

  async put(url, data, options = {}) {
    const response = await this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options
    });
    return response.json();
  }

  async delete(url, options = {}) {
    const response = await this.request(url, { method: 'DELETE', ...options });
    return response.status === 204 ? null : response.json();
  }
}

/**
 * Кастомный класс ошибок API
 */
class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }

  /**
   * Форматирует сообщение об ошибке для пользователя
   */
  getUserMessage() {
    if (this.status >= 400 && this.status < 500) {
      // Если это массив ошибок валидации (обычно 422)
      if (Array.isArray(this.details)) {
        return this.details
          .map(err => {
            // Переводим типичные ошибки валидации дат
            if (err.msg && err.loc && err.loc.includes('end_datetime')) {
              if (
                err.msg.includes('повинен бути пізніше') ||
                err.msg.includes('should be after')
              ) {
                return 'Час завершення повинен бути пізніше часу початку роботи';
              }
            }
            return err.msg || err.message || String(err);
          })
          .join(', ');
      }

      // Если это строка с детальным сообщением (например, от BusinessLogicError)
      if (typeof this.details === 'string') {
        return this.details;
      }

      // Если это объект с полем detail
      if (this.details && this.details.detail) {
        return this.details.detail;
      }

      // Возвращаем детали или основное сообщение
      return this.details || this.message;
    }

    if (this.status >= 500) {
      return 'Помилка сервера. Спробуйте пізніше.';
    }

    return "Помилка з'єднання з сервером";
  }
}

/**
 * Основной API сервис
 */
class ApiService {
  constructor() {
    this.http = new HttpClient();
  }

  // ===== ТИПЫ РАБОТ =====

  /**
   * Получить все типы работ
   */
  async getWorkTypes() {
    return this.http.get('/api/v1/work-types/');
  }

  /**
   * Создать новый тип работы
   */
  async createWorkType(workType) {
    return this.http.post('/api/v1/work-types/', workType);
  }

  /**
   * Обновить тип работы
   */
  async updateWorkType(typeId, workType) {
    return this.http.put(`/api/v1/work-types/${typeId}`, workType);
  }

  /**
   * Удалить тип работы
   */
  async deleteWorkType(typeId) {
    return this.http.delete(`/api/v1/work-types/${typeId}`);
  }

  // ===== УЛИЦЫ =====

  /**
   * Быстрый поиск улиц
   */
  async searchStreets(query) {
    const encodedQuery = encodeURIComponent(query);
    return this.http.get(`/api/v1/streets/fast-search?q=${encodedQuery}&limit=10`);
  }

  /**
   * Получить геометрию улицы по названию
   */
  async getStreetGeometry(streetName) {
    const encodedName = encodeURIComponent(streetName);
    return this.http.get(`/api/v1/streets/fast-geometry/${encodedName}`);
  }

  /**
   * Получить геометрию улицы по OSM данным
   */
  async getStreetGeometryByOsm(osmType, osmId) {
    return this.http.get(`/api/v1/streets/geometry/${osmType}/${osmId}`);
  }

  /**
   * Обратное геокодирование
   */
  async reverseGeocode(lat, lon) {
    return this.http.get(`/api/v1/streets/reverse?lat=${lat}&lon=${lon}`);
  }

  /**
   * Вычислить сегмент улицы
   */
  async calculateStreetSegment(segmentData) {
    return this.http.post('/api/v1/streets/segment-local', segmentData);
  }

  // ===== РЕМОНТНЫЕ РАБОТЫ =====

  /**
   * Получить все ремонтные работы с фильтрами
   */
  async getRepairWorks(filters = {}) {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value);
      }
    });

    const queryString = params.toString();
    const url = queryString
      ? `/api/v1/repair-works/?${queryString}`
      : '/api/v1/repair-works/';

    return this.http.get(url);
  }

  /**
   * Получить одну ремонтную работу по ID
   */
  async getRepairWork(workId) {
    return this.http.get(`/api/v1/repair-works/${workId}`);
  }

  /**
   * Создать новую ремонтную работу
   */
  async createRepairWork(workData) {
    return this.http.post('/api/v1/repair-works/', workData);
  }

  /**
   * Обновить ремонтную работу
   */
  async updateRepairWork(workId, workData) {
    return this.http.put(`/api/v1/repair-works/${workId}`, workData);
  }

  /**
   * Удалить ремонтную работу
   */
  async deleteRepairWork(workId) {
    return this.http.delete(`/api/v1/repair-works/${workId}`);
  }

  // === ФОТОГРАФИИ РЕМОНТНЫХ РАБОТ ===

  // Получить все фотографии ремонтной работы
  async getRepairWorkPhotos(workId) {
    return this.http.get(`/api/v1/repair-works/${workId}/photos`);
  }

  // Загрузить фотографию для ремонтной работы
  async uploadRepairWorkPhoto(workId, file, description = '', sortOrder = 0) {
    const formData = new FormData();
    formData.append('file', file);
    if (description) {
      formData.append('description', description);
    }
    formData.append('sort_order', sortOrder.toString());

    const response = await fetch(
      `${this.http.baseURL}/api/v1/repair-works/${workId}/photos`,
      {
        method: 'POST',
        body: formData
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // Обновить информацию о фотографии
  async updateRepairWorkPhoto(workId, photoId, updateData) {
    return this.http.put(
      `/api/v1/repair-works/${workId}/photos/${photoId}`,
      updateData
    );
  }

  // Удалить фотографию
  async deleteRepairWorkPhoto(workId, photoId) {
    return this.http.delete(`/api/v1/repair-works/${workId}/photos/${photoId}`);
  }

  // Получить URL для скачивания/просмотра фотографии
  getRepairWorkPhotoUrl(workId, photoId) {
    return `${this.http.baseURL}/api/v1/repair-works/${workId}/photos/${photoId}/download`;
  }
}

// Создаем экземпляр сервиса
const apiService = new ApiService();

export default apiService;
