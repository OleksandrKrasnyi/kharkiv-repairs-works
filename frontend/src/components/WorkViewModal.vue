<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <!-- Кнопка закрытия -->
      <button class="modal-close" @click="closeModal" title="Закрити">
        <i class="fas fa-times" />
      </button>

      <!-- Заголовок модального окна -->
      <div class="modal-header">
        <h2>
          <i :class="isEditMode ? 'fas fa-edit' : 'fas fa-eye'" />
          {{ isEditMode ? 'Редагування ремонтної роботи' : 'Деталі ремонтної роботи' }}
        </h2>
        <div class="header-actions">
          <div
            v-if="work.work_type"
            class="work-type-badge"
            :style="{ backgroundColor: work.work_type.color }"
          >
            {{ work.work_type.name }}
          </div>
          <button
            v-if="!isEditMode"
            class="btn-edit-toggle"
            @click="toggleEditMode"
            title="Редагувати роботу"
          >
            <i class="fas fa-edit" />
            Редагувати
          </button>
        </div>
      </div>

      <!-- Мини-карта -->
      <div class="mini-map-container">
        <div id="work-detail-map" class="mini-map" />
        <div class="map-overlay">
          <div class="map-overlay-content">
            <i class="fas fa-map-marker-alt" />
            <span>{{ workLocationText }}</span>
          </div>
        </div>
      </div>

      <!-- Содержимое модального окна -->
      <div class="modal-body">
        <div v-if="!isEditMode" class="work-details-grid">
          <!-- Режим просмотра -->
          <!-- Основная информация -->
          <div class="detail-section">
            <h3>
              <i class="fas fa-info-circle" />
              Основна інформація
            </h3>
            <div class="detail-row">
              <label>Опис:</label>
              <span>{{ work.description || 'Не вказано' }}</span>
            </div>
            <div v-if="work.notes" class="detail-row">
              <label>Примітки:</label>
              <span>{{ work.notes }}</span>
            </div>
            <div class="detail-row">
              <label>Статус:</label>
              <span class="status-badge" :class="work.status">
                <i class="fas fa-flag" />
                {{ getStatusText(work.status) }}
              </span>
            </div>
          </div>

          <!-- Временные рамки -->
          <div class="detail-section">
            <h3>
              <i class="fas fa-calendar" />
              Часові рамки
            </h3>
            <div class="detail-row">
              <label>Початок роботи:</label>
              <span>{{ formatDateTime(work.start_datetime) }}</span>
            </div>
            <div v-if="work.end_datetime" class="detail-row">
              <label>Завершення роботи:</label>
              <span>{{ formatDateTime(work.end_datetime) }}</span>
            </div>
            <div v-if="work.planned_duration_hours" class="detail-row">
              <label>Планована тривалість:</label>
              <span>{{ work.planned_duration_hours }} год.</span>
            </div>
          </div>

          <!-- Местоположение -->
          <div class="detail-section">
            <h3>
              <i class="fas fa-map-marker-alt" />
              Місцезнаходження
            </h3>
            <div v-if="readableAddresses.location || work.location" class="detail-row">
              <label>Точкова локація:</label>
              <span>{{ readableAddresses.location || work.location }}</span>
            </div>
            <div
              v-if="readableAddresses.start_location || work.start_location"
              class="detail-row"
            >
              <label>Початкова точка:</label>
              <span>{{ readableAddresses.start_location || work.start_location }}</span>
            </div>
            <div
              v-if="readableAddresses.end_location || work.end_location"
              class="detail-row"
            >
              <label>Кінцева точка:</label>
              <span>{{ readableAddresses.end_location || work.end_location }}</span>
            </div>
            <div v-if="work.street_name" class="detail-row">
              <label>Вулиця:</label>
              <span>{{ work.street_name }}</span>
            </div>
          </div>

          <!-- Системная информация -->
          <div class="detail-section">
            <h3>
              <i class="fas fa-cog" />
              Системна інформація
            </h3>
            <div class="detail-row">
              <label>ID роботи:</label>
              <span>{{ work.id }}</span>
            </div>
            <div class="detail-row">
              <label>Створено:</label>
              <span>{{ formatDateTime(work.created_at) }}</span>
            </div>
            <div v-if="work.updated_at" class="detail-row">
              <label>Оновлено:</label>
              <span>{{ formatDateTime(work.updated_at) }}</span>
            </div>
          </div>

          <!-- Фотографии -->
          <div class="detail-section">
            <h3>
              <i class="fas fa-camera" />
              Фотографії
              <span v-if="photos.length > 0" class="photo-count">
                ({{ photos.length }})
              </span>
            </h3>
            <div v-if="photos.length === 0" class="no-photos">
              <i class="fas fa-camera" />
              <p>Фотографії ще не додані</p>
            </div>
            <div v-else class="photos-grid">
              <div
                v-for="photo in photos"
                :key="photo.id"
                class="photo-item"
                @click="openPhotoModal(photo)"
              >
                <img
                  :src="getPhotoUrl(photo.id)"
                  :alt="photo.description || 'Фото роботи'"
                  class="photo-thumbnail"
                />
                <div v-if="photo.description" class="photo-description">
                  {{ photo.description }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Режим редактирования -->
        <div v-else class="edit-form">
          <div class="form-section">
            <h3>
              <i class="fas fa-info-circle" />
              Основна інформація
            </h3>

            <div class="form-group">
              <label>
                <i class="fas fa-tools" />
                Вид робіт
              </label>
              <select v-model="editableWork.work_type_id" class="form-control">
                <option value="">Оберіть вид робіт</option>
                <option v-for="type in workTypes" :key="type.id" :value="type.id">
                  {{ type.name }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>
                <i class="fas fa-clipboard" />
                Опис роботи
              </label>
              <textarea
                v-model="editableWork.description"
                placeholder="Детальний опис ремонтних робіт..."
                rows="3"
                class="form-control"
              />
            </div>

            <div class="form-group">
              <label>
                <i class="fas fa-sticky-note" />
                Примітки
              </label>
              <textarea
                v-model="editableWork.notes"
                placeholder="Додаткові примітки..."
                rows="2"
                class="form-control"
              />
            </div>

            <div class="form-group">
              <label>
                <i class="fas fa-flag" />
                Статус
              </label>
              <select v-model="editableWork.status" class="form-control">
                <option value="planned">Заплановано</option>
                <option value="in_progress">В процесі</option>
                <option value="completed">Завершено</option>
                <option value="cancelled">Скасовано</option>
                <option value="delayed">Відкладено</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h3>
              <i class="fas fa-calendar" />
              Часові рамки
            </h3>

            <div class="form-group">
              <label>
                <i class="fas fa-calendar" />
                Початок роботи *
              </label>
              <input
                v-model="editableWork.start_datetime"
                type="datetime-local"
                required
                class="form-control"
              />
            </div>

            <div class="form-group">
              <label>
                <i class="fas fa-calendar" />
                Завершення роботи
              </label>
              <input
                v-model="editableWork.end_datetime"
                type="datetime-local"
                class="form-control"
              />
            </div>

            <div class="form-group">
              <label>
                <i class="fas fa-clock" />
                Планована тривалість (годин)
              </label>
              <input
                v-model.number="editableWork.planned_duration_hours"
                type="number"
                min="1"
                max="8760"
                class="form-control"
              />
            </div>
          </div>

          <div class="form-section">
            <h3>
              <i class="fas fa-map-marker-alt" />
              Місцезнаходження
            </h3>
            <div class="readonly-info">
              <i class="fas fa-info-circle" />
              Місцезнаходження та координати можна змінити тільки при створенні нової
              роботи
            </div>

            <div v-if="readableAddresses.location || work.location" class="form-group">
              <label>Точкова локація:</label>
              <input
                :value="readableAddresses.location || work.location"
                readonly
                class="form-control readonly"
              />
            </div>

            <div
              v-if="
                readableAddresses.start_location ||
                readableAddresses.end_location ||
                work.start_location ||
                work.end_location
              "
            >
              <div
                v-if="readableAddresses.start_location || work.start_location"
                class="form-group"
              >
                <label>Початкова точка:</label>
                <input
                  :value="readableAddresses.start_location || work.start_location"
                  readonly
                  class="form-control readonly"
                />
              </div>
              <div
                v-if="readableAddresses.end_location || work.end_location"
                class="form-group"
              >
                <label>Кінцева точка:</label>
                <input
                  :value="readableAddresses.end_location || work.end_location"
                  readonly
                  class="form-control readonly"
                />
              </div>
            </div>

            <div v-if="work.street_name" class="form-group">
              <label>Вулиця:</label>
              <input :value="work.street_name" readonly class="form-control readonly" />
            </div>
          </div>

          <!-- Фотографии в режиме редактирования -->
          <div class="form-section">
            <h3>
              <i class="fas fa-camera" />
              Фотографії
              <span v-if="photos.length > 0" class="photo-count">
                ({{ photos.length }})
              </span>
            </h3>

            <!-- Загрузка новых фотографий -->
            <div class="photo-upload-section">
              <div class="form-group">
                <label>
                  <i class="fas fa-plus" />
                  Додати фотографії
                </label>
                <input
                  ref="photoInput"
                  type="file"
                  accept="image/*"
                  multiple
                  class="form-control"
                  @change="handlePhotoUpload"
                />
                <div class="upload-help">
                  Підтримуються формати: JPG, PNG, WEBP. Максимальний розмір: 10MB
                </div>
              </div>
            </div>

            <!-- Список существующих фотографий -->
            <div v-if="photos.length === 0" class="no-photos">
              <i class="fas fa-camera" />
              <p>Фотографії ще не додані</p>
            </div>
            <div v-else class="photos-edit-list">
              <div v-for="photo in photos" :key="photo.id" class="photo-edit-item">
                <img
                  :src="getPhotoUrl(photo.id)"
                  :alt="photo.description || 'Фото роботи'"
                  class="photo-thumbnail-edit"
                  @click="openPhotoModal(photo)"
                />
                <div class="photo-edit-info">
                  <div class="form-group">
                    <label>Опис фотографії:</label>
                    <input
                      v-model="photo.description"
                      type="text"
                      class="form-control"
                      placeholder="Опис фотографії..."
                      @blur="updatePhotoDescription(photo)"
                    />
                  </div>
                  <div class="photo-actions">
                    <button
                      type="button"
                      class="btn-danger-small"
                      @click="deletePhoto(photo)"
                      title="Видалити фотографію"
                    >
                      <i class="fas fa-trash" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Футер модального окна -->
      <div class="modal-footer">
        <div v-if="!isEditMode" class="footer-actions">
          <button class="btn-secondary" @click="closeModal">
            <i class="fas fa-times" />
            Закрити
          </button>
        </div>
        <div v-else class="footer-actions">
          <button class="btn-secondary" @click="cancelEdit">
            <i class="fas fa-times" />
            Скасувати
          </button>
          <button class="btn-primary" @click="saveWork" :disabled="isSaving">
            <i :class="isSaving ? 'fas fa-spinner fa-spin' : 'fas fa-save'" />
            {{ isSaving ? 'Збереження...' : 'Зберегти' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Модальное окно для просмотра фотографии -->
  <div v-if="photoModalVisible" class="photo-modal-overlay" @click="closePhotoModal">
    <div class="photo-modal-content" @click.stop>
      <button class="photo-modal-close" @click="closePhotoModal" title="Закрити">
        <i class="fas fa-times" />
      </button>
      <div v-if="selectedPhoto" class="photo-modal-body">
        <img
          :src="getPhotoUrl(selectedPhoto.id)"
          :alt="selectedPhoto.description || 'Фото роботи'"
          class="photo-full-size"
        />
        <div v-if="selectedPhoto.description" class="photo-modal-description">
          {{ selectedPhoto.description }}
        </div>
        <div class="photo-modal-info">
          <div class="photo-info-item">
            <i class="fas fa-file" />
            {{ selectedPhoto.filename }}
          </div>
          <div v-if="selectedPhoto.file_size" class="photo-info-item">
            <i class="fas fa-weight" />
            {{ formatFileSize(selectedPhoto.file_size) }}
          </div>
          <div class="photo-info-item">
            <i class="fas fa-calendar" />
            {{ formatDateTime(selectedPhoto.created_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch, onMounted, onUnmounted, computed } from 'vue';
import { useApi } from '../composables/useApi.js';
import { useNotifications } from '../composables/useNotifications.js';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default {
  name: 'WorkViewModal',
  props: {
    isVisible: {
      type: Boolean,
      required: true
    },
    work: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'workUpdated'],
  setup(props, { emit }) {
    const api = useApi();
    const { showSuccess, showError } = useNotifications();

    const miniMap = ref(null);
    const isEditMode = ref(false);
    const isSaving = ref(false);
    const workTypes = ref([]);

    // Редактируемая копия работы
    const editableWork = reactive({});

    // Читаемые адреса
    const readableAddresses = reactive({
      location: '',
      start_location: '',
      end_location: ''
    });

    // Фотографии
    const photos = ref([]);
    const photoInput = ref(null);
    const photoModalVisible = ref(false);
    const selectedPhoto = ref(null);
    const isUploadingPhoto = ref(false);

    const closeModal = () => {
      emit('close');
    };

    const toggleEditMode = () => {
      isEditMode.value = true;
      // Копируем данные для редактирования
      Object.assign(editableWork, {
        ...props.work,
        work_type_id: props.work.work_type?.id || '',
        start_datetime: formatDateTimeForInput(props.work.start_datetime),
        end_datetime: formatDateTimeForInput(props.work.end_datetime)
      });
    };

    const cancelEdit = () => {
      isEditMode.value = false;
      // Очищаем редактируемые данные
      Object.keys(editableWork).forEach(key => delete editableWork[key]);
    };

    const saveWork = async () => {
      isSaving.value = true;
      try {
        const updateData = {
          work_type_id: editableWork.work_type_id || null,
          description: editableWork.description || null,
          notes: editableWork.notes || null,
          status: editableWork.status,
          start_datetime: editableWork.start_datetime,
          end_datetime: editableWork.end_datetime || null,
          planned_duration_hours: editableWork.planned_duration_hours || null
        };

        const updatedWork = await api.updateRepairWork(props.work.id, updateData);

        showSuccess('Роботу успішно оновлено!');
        isEditMode.value = false;

        // Уведомляем родительский компонент об обновлении
        emit('workUpdated', updatedWork);
      } catch (error) {
        console.error('Ошибка обновления работы:', error);
        let errorMessage = 'Помилка оновлення роботи';

        if (error.name === 'ApiError' && typeof error.getUserMessage === 'function') {
          errorMessage = error.getUserMessage();
        } else if (error.details) {
          if (Array.isArray(error.details)) {
            errorMessage = error.details
              .map(err => err.msg || err.message || String(err))
              .join(', ');
          } else if (typeof error.details === 'string') {
            errorMessage = error.details;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }

        showError(errorMessage);
      } finally {
        isSaving.value = false;
      }
    };

    const fetchWorkTypes = async () => {
      try {
        const types = await api.fetchWorkTypes();
        workTypes.value = types;
      } catch (error) {
        console.error('Ошибка загрузки типов работ:', error);
      }
    };

    // === ФУНКЦИИ ДЛЯ РАБОТЫ С ФОТОГРАФИЯМИ ===

    const fetchPhotos = async () => {
      if (!props.work?.id) return;

      try {
        const result = await api.getRepairWorkPhotos(props.work.id);
        photos.value = result.photos || [];
      } catch (error) {
        console.error('Ошибка загрузки фотографий:', error);
        photos.value = [];
      }
    };

    const getPhotoUrl = photoId => {
      return api.getRepairWorkPhotoUrl(props.work.id, photoId);
    };

    const openPhotoModal = photo => {
      selectedPhoto.value = photo;
      photoModalVisible.value = true;
    };

    const closePhotoModal = () => {
      photoModalVisible.value = false;
      selectedPhoto.value = null;
    };

    const handlePhotoUpload = async event => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      isUploadingPhoto.value = true;

      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];

          // Проверяем размер файла (10MB)
          if (file.size > 10 * 1024 * 1024) {
            showError(`Файл ${file.name} занадто великий. Максимальний розмір: 10MB`);
            continue;
          }

          // Проверяем тип файла
          if (!file.type.startsWith('image/')) {
            showError(`Файл ${file.name} не є зображенням`);
            continue;
          }

          await api.uploadRepairWorkPhoto(props.work.id, file, '', photos.value.length);
        }

        // Обновляем список фотографий
        await fetchPhotos();

        // Очищаем input
        if (photoInput.value) {
          photoInput.value.value = '';
        }

        showSuccess('Фотографії успішно завантажені!');
      } catch (error) {
        console.error('Ошибка загрузки фотографии:', error);
        showError('Помилка завантаження фотографій');
      } finally {
        isUploadingPhoto.value = false;
      }
    };

    const updatePhotoDescription = async photo => {
      try {
        await api.updateRepairWorkPhoto(props.work.id, photo.id, {
          description: photo.description
        });
        showSuccess('Опис фотографії оновлено');
      } catch (error) {
        console.error('Ошибка обновления описания фотографии:', error);
        showError('Помилка оновлення опису фотографії');
      }
    };

    const deletePhoto = async photo => {
      if (!confirm('Ви впевнені, що хочете видалити цю фотографію?')) {
        return;
      }

      try {
        await api.deleteRepairWorkPhoto(props.work.id, photo.id);

        // Обновляем список фотографий
        await fetchPhotos();

        showSuccess('Фотографію видалено');
      } catch (error) {
        console.error('Ошибка удаления фотографии:', error);
        showError('Помилка видалення фотографії');
      }
    };

    const formatFileSize = bytes => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Форматирование адреса из результата геокодирования
    const formatAddress = geocodeResult => {
      if (!geocodeResult || !geocodeResult.address) {
        return geocodeResult?.display_name || '';
      }
      const a = geocodeResult.address;
      const parts = [];
      if (a.house_number) {
        parts.push(a.house_number);
      }
      if (a.road || geocodeResult.street_name) {
        parts.push(a.road || geocodeResult.street_name);
      }
      if (a.suburb) {
        parts.push(a.suburb);
      } else if (a.city_district) {
        parts.push(a.city_district);
      }
      if (a.postcode) {
        parts.push(a.postcode);
      }
      if (a.city) {
        parts.push(a.city);
      }
      return parts.join(', ');
    };

    // Загрузка читаемых адресов из координат
    const loadReadableAddresses = async () => {
      if (!props.isVisible) return; // Не загружаем если модал закрыт

      try {
        // Загружаем адрес для точечной локации
        if (props.work.latitude && props.work.longitude) {
          try {
            const result = await api.reverseGeocode(
              props.work.latitude,
              props.work.longitude
            );
            if (props.isVisible) {
              // Проверяем что модал еще открыт
              readableAddresses.location =
                formatAddress(result) ||
                `${props.work.latitude.toFixed(6)}, ${props.work.longitude.toFixed(6)}`;
            }
          } catch (error) {
            console.warn('Ошибка геокодирования точки:', error);
            if (props.isVisible) {
              readableAddresses.location = `${props.work.latitude.toFixed(6)}, ${props.work.longitude.toFixed(6)}`;
            }
          }
        }

        // Загружаем адреса для сегментной работы
        if (props.work.start_latitude && props.work.start_longitude) {
          try {
            const result = await api.reverseGeocode(
              props.work.start_latitude,
              props.work.start_longitude
            );
            if (props.isVisible) {
              readableAddresses.start_location =
                formatAddress(result) ||
                `${props.work.start_latitude.toFixed(6)}, ${props.work.start_longitude.toFixed(6)}`;
            }
          } catch (error) {
            console.warn('Ошибка геокодирования начальной точки:', error);
            if (props.isVisible) {
              readableAddresses.start_location = `${props.work.start_latitude.toFixed(6)}, ${props.work.start_longitude.toFixed(6)}`;
            }
          }
        }

        if (props.work.end_latitude && props.work.end_longitude) {
          try {
            const result = await api.reverseGeocode(
              props.work.end_latitude,
              props.work.end_longitude
            );
            if (props.isVisible) {
              readableAddresses.end_location =
                formatAddress(result) ||
                `${props.work.end_latitude.toFixed(6)}, ${props.work.end_longitude.toFixed(6)}`;
            }
          } catch (error) {
            console.warn('Ошибка геокодирования конечной точки:', error);
            if (props.isVisible) {
              readableAddresses.end_location = `${props.work.end_latitude.toFixed(6)}, ${props.work.end_longitude.toFixed(6)}`;
            }
          }
        }
      } catch (error) {
        console.error('Ошибка загрузки адресов:', error);
      }
    };

    const initMiniMap = () => {
      // Уничтожаем существующую карту если есть
      if (miniMap.value) {
        miniMap.value.remove();
        miniMap.value = null;
      }

      // Создаем новую мини-карту
      const mapContainer = document.getElementById('work-detail-map');
      if (!mapContainer || !props.work) return;

      // Определяем центр карты и зум на основе данных работы
      let center,
        zoom = 15;

      if (props.work.latitude && props.work.longitude) {
        // Точечная работа
        center = [props.work.latitude, props.work.longitude];
      } else if (
        props.work.start_latitude &&
        props.work.start_longitude &&
        props.work.end_latitude &&
        props.work.end_longitude
      ) {
        // Сегментная работа - центр между точками
        center = [
          (props.work.start_latitude + props.work.end_latitude) / 2,
          (props.work.start_longitude + props.work.end_longitude) / 2
        ];
        zoom = 14;
      } else {
        // Нет координат - показываем общий вид Харькова
        center = [49.9935, 36.2304];
        zoom = 12;
      }

      miniMap.value = L.map('work-detail-map', {
        zoomControl: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        dragging: false,
        touchZoom: false,
        boxZoom: false,
        keyboard: false
      }).setView(center, zoom);

      // Исправляем иконки маркеров
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-icon-2x.png',
        iconUrl:
          'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-icon.png',
        shadowUrl:
          'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.3/images/marker-shadow.png'
      });

      // Добавляем тайлы
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }).addTo(miniMap.value);

      // Если есть GeoJSON геометрия улицы, показываем её (приоритет)
      if (props.work.street_segment_geojson) {
        try {
          const geojson = JSON.parse(props.work.street_segment_geojson);
          const geoLayer = L.geoJSON(geojson, {
            style: {
              color: props.work.work_type?.color || '#3388ff',
              weight: 6,
              opacity: 0.7
            }
          }).addTo(miniMap.value);

          // Подстраиваем вид под GeoJSON геометрию
          miniMap.value.fitBounds(geoLayer.getBounds(), { padding: [15, 15] });
        } catch (error) {
          console.warn('Ошибка парсинга GeoJSON:', error);
          // Если ошибка с GeoJSON, показываем fallback
          addFallbackMarkers();
        }
      } else {
        // Если нет GeoJSON, показываем маркеры
        addFallbackMarkers();
      }

      function addFallbackMarkers() {
        if (props.work.latitude && props.work.longitude) {
          // Точечная работа
          L.marker([props.work.latitude, props.work.longitude]).addTo(miniMap.value);
        } else if (
          props.work.start_latitude &&
          props.work.start_longitude &&
          props.work.end_latitude &&
          props.work.end_longitude
        ) {
          // Сегментная работа без GeoJSON - показываем только центральную точку
          const centerLat = (props.work.start_latitude + props.work.end_latitude) / 2;
          const centerLng = (props.work.start_longitude + props.work.end_longitude) / 2;

          L.marker([centerLat, centerLng]).addTo(miniMap.value);
        }
      }

      // Небольшая задержка для корректного отображения
      setTimeout(() => {
        if (miniMap.value) {
          miniMap.value.invalidateSize();
        }
      }, 100);
    };

    const workLocationText = computed(() => {
      // Для точечных работ - показываем полный адрес
      if (readableAddresses.location) {
        return readableAddresses.location;
      }

      // Для сегментных работ - показываем только название улицы, если есть
      if (readableAddresses.start_location || readableAddresses.end_location) {
        if (props.work.street_name) {
          return props.work.street_name;
        }
        // Если нет названия улицы, показываем краткий адрес
        if (readableAddresses.start_location) {
          // Берем только первую часть адреса (до первой запятой)
          return readableAddresses.start_location.split(',')[0];
        }
      }

      // Fallback к исходным данным только если нет читаемых адресов
      if (
        props.work.location &&
        !props.work.location.includes(',') &&
        !props.work.location.includes('.')
      ) {
        return props.work.location;
      }
      if (props.work.street_name) return props.work.street_name;
      return 'Місцезнаходження не вказано';
    });

    const getStatusText = status => {
      const statusMap = {
        planned: 'Заплановано',
        in_progress: 'В процесі',
        completed: 'Завершено',
        cancelled: 'Скасовано',
        delayed: 'Відкладено'
      };
      return statusMap[status] || status;
    };

    const formatDateTime = dateStr => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('uk-UA', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const formatDateTimeForInput = dateStr => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
      return date.toISOString().slice(0, 16);
    };

    // Watcher для инициализации карты при открытии модального окна
    watch(
      () => props.isVisible,
      newValue => {
        if (newValue) {
          // Загружаем типы работ
          fetchWorkTypes();

          // Загружаем читаемые адреса
          loadReadableAddresses();

          // Загружаем фотографии
          fetchPhotos();

          // Небольшая задержка для того, чтобы DOM обновился
          setTimeout(() => {
            initMiniMap();
          }, 50);
        } else {
          // Уничтожаем карту при закрытии
          if (miniMap.value) {
            miniMap.value.remove();
            miniMap.value = null;
          }

          // Сбрасываем режим редактирования
          isEditMode.value = false;
          Object.keys(editableWork).forEach(key => delete editableWork[key]);

          // Очищаем адреса
          readableAddresses.location = '';
          readableAddresses.start_location = '';
          readableAddresses.end_location = '';
        }
      }
    );

    // Закрытие по Escape
    const handleKeydown = event => {
      if (event.key === 'Escape' && props.isVisible) {
        if (isEditMode.value) {
          cancelEdit();
        } else {
          closeModal();
        }
      }
    };

    // Добавляем обработчик клавиш при монтировании
    onMounted(() => {
      document.addEventListener('keydown', handleKeydown);
    });

    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeydown);
      if (miniMap.value) {
        miniMap.value.remove();
      }
    });

    return {
      isEditMode,
      isSaving,
      workTypes,
      editableWork,
      readableAddresses,
      closeModal,
      toggleEditMode,
      cancelEdit,
      saveWork,
      workLocationText,
      getStatusText,
      formatDateTime,
      // Фотографии
      photos,
      photoInput,
      photoModalVisible,
      selectedPhoto,
      isUploadingPhoto,
      getPhotoUrl,
      openPhotoModal,
      closePhotoModal,
      handlePhotoUpload,
      updatePhotoDescription,
      deletePhoto,
      formatFileSize
    };
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  max-width: 1000px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.modal-close {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  font-size: 18px;
  color: #666;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #f5f5f5;
  color: #333;
}

.modal-header {
  padding: 20px 60px 16px 24px; /* Увеличиваем правый отступ для кнопки закрытия */
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0; /* Позволяет сжиматься при необходимости */
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0; /* Не позволяет сжиматься */
}

.work-type-badge {
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.btn-edit-toggle {
  background: #4299e1;
  color: white;
  border: 1px solid #4299e1;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  transition: all 0.2s;
}

.btn-edit-toggle:hover {
  background: #3182ce;
  border-color: #3182ce;
}

.mini-map-container {
  position: relative;
  height: 200px;
  background: #f8f9fa;
  border-bottom: 1px solid #e5e5e5;
}

.mini-map {
  width: 100%;
  height: 100%;
}

.map-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.4));
  padding: 12px 16px;
  z-index: 1000;
}

.map-overlay-content {
  color: white;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

/* Режим просмотра */
.work-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.detail-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.detail-section h3 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-row label {
  font-weight: 500;
  color: #666;
  white-space: nowrap;
  min-width: 120px;
}

.detail-row span {
  text-align: right;
  word-break: break-word;
  flex: 1;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-badge.planned {
  background: #e3f2fd;
  color: #1976d2;
}

.status-badge.in_progress {
  background: #fff3e0;
  color: #f57c00;
}

.status-badge.completed {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-badge.cancelled {
  background: #ffebee;
  color: #d32f2f;
}

.status-badge.delayed {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Режим редактирования */
.edit-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.form-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.form-section h3 {
  margin: 0 0 20px 0;
  font-size: 14px;
  font-weight: 600;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #555;
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.form-control.readonly {
  background: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
}

.readonly-info {
  background: #fef3cd;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e5e5;
  display: flex;
  justify-content: flex-end;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.btn-secondary {
  background: #6c757d;
  color: white;
  border: 1px solid #6c757d;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #5a6268;
  border-color: #5a6268;
}

.btn-primary {
  background: #4299e1;
  color: white;
  border: 1px solid #4299e1;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #3182ce;
  border-color: #3182ce;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Адаптивность */
@media (max-width: 768px) {
  .modal-overlay {
    padding: 10px;
  }

  .modal-content {
    max-height: 95vh;
  }

  .work-details-grid,
  .edit-form {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .detail-row label {
    min-width: auto;
  }

  .detail-row span {
    text-align: left;
  }

  .mini-map-container {
    height: 150px;
  }

  .modal-header {
    padding: 20px 50px 16px 20px; /* Уменьшаем отступы на мобильных */
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .modal-header h2 {
    font-size: 18px;
  }

  .header-actions {
    flex-direction: row;
    align-items: center;
    gap: 8px;
    width: 100%;
    justify-content: flex-start;
  }

  .btn-edit-toggle {
    font-size: 11px;
    padding: 5px 10px;
  }

  .work-type-badge {
    font-size: 11px;
    padding: 3px 8px;
  }

  .footer-actions {
    flex-direction: column;
    width: 100%;
  }

  .footer-actions button {
    width: 100%;
    justify-content: center;
  }
}

/* Для очень маленьких экранов */
@media (max-width: 480px) {
  .modal-header {
    padding: 15px 45px 15px 15px;
  }

  .modal-close {
    top: 15px;
    right: 15px;
    width: 28px;
    height: 28px;
    font-size: 16px;
  }

  .header-actions {
    flex-wrap: wrap;
  }

  .btn-edit-toggle {
    font-size: 10px;
    padding: 4px 8px;
  }

  .work-type-badge {
    font-size: 10px;
    padding: 2px 6px;
  }
}

/* === СТИЛИ ДЛЯ ФОТОГРАФИЙ === */

.photo-count {
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.no-photos {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.no-photos i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-photos p {
  margin: 0;
  font-size: 16px;
}

/* Сетка фотографий в режиме просмотра */
.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.photo-item {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  background: #f8f9fa;
}

.photo-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.photo-thumbnail {
  width: 100%;
  height: 120px;
  object-fit: cover;
  display: block;
}

.photo-description {
  padding: 8px 12px;
  font-size: 12px;
  color: #666;
  background: white;
  border-top: 1px solid #e5e5e5;
}

/* Список фотографий в режиме редактирования */
.photo-upload-section {
  margin-bottom: 24px;
}

.upload-help {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.photos-edit-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.photo-edit-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  background: #f8f9fa;
}

.photo-thumbnail-edit {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.photo-thumbnail-edit:hover {
  transform: scale(1.05);
}

.photo-edit-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.photo-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-danger-small {
  background: #dc3545;
  color: white;
  border: 1px solid #dc3545;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.btn-danger-small:hover {
  background: #c82333;
  border-color: #c82333;
}

/* Модальное окно для просмотра фотографии */
.photo-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}

.photo-modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.photo-modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  z-index: 10;
  transition: background 0.2s;
}

.photo-modal-close:hover {
  background: rgba(0, 0, 0, 0.7);
}

.photo-modal-body {
  display: flex;
  flex-direction: column;
}

.photo-full-size {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  display: block;
}

.photo-modal-description {
  padding: 16px 20px 12px;
  font-size: 16px;
  color: #333;
  background: white;
  border-bottom: 1px solid #e5e5e5;
}

.photo-modal-info {
  padding: 16px 20px;
  background: #f8f9fa;
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.photo-info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.photo-info-item i {
  color: #999;
}

/* Адаптивность для фотографий */
@media (max-width: 768px) {
  .photos-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
  }

  .photo-thumbnail {
    height: 100px;
  }

  .photo-edit-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .photo-thumbnail-edit {
    width: 100%;
    height: 150px;
  }

  .photo-modal-info {
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .photos-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }

  .photo-thumbnail {
    height: 80px;
  }

  .photo-modal-overlay {
    padding: 10px;
  }

  .photo-full-size {
    max-height: 60vh;
  }
}
</style>
