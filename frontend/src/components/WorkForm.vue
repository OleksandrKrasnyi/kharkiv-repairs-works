<template>
  <div class="form-container">
    <div class="instructions">
      <i class="fas fa-info-circle" />
      <strong>Інструкція:</strong>
      <span v-if="workType === 'smart-point'">
        Натисніть на карту - адреса та улица визначаться автоматично.
      </span>
      <span v-if="workType === 'smart-segment'">
        <span v-if="!hasSelectedStreetFromSearch">
          1-й клік: оберіть улицю та точку 1. 2-й клік: оберіть точку 2 на тій же вулиці
          для створення сегменту.
        </span>
        <span v-else>
          <i class="fas fa-check-circle" style="color: #28a745" />
          Вулиця вже обрана! Клікніть на мапу для обрання точки 1, потім точки 2 для
          створення сегмента.
        </span>
      </span>
    </div>

    <div class="work-type-selector">
      <div
        class="work-type-btn"
        :class="{ active: workType === 'smart-point' }"
        title="Автоматическое определение адреса при клике"
        @click="setWorkType('smart-point')"
      >
        <i class="fas fa-map-marker-alt" />
        <br />
        Точка
      </div>
      <div
        class="work-type-btn"
        :class="{ active: workType === 'smart-segment' }"
        title="Автоматическое создание сегмента дороги"
        @click="setWorkType('smart-segment')"
      >
        <i class="fas fa-road" />
        <br />
        Сегмент дороги
      </div>
    </div>

    <div class="form-group">
      <label>
        <i class="fas fa-tools" />
        Вид робіт
      </label>
      <select v-model="selectedWorkTypeId" class="form-control">
        <option value="">Оберіть вид робіт</option>
        <option v-for="type in workTypes" :key="type.id" :value="type.id">
          {{ type.name }}
        </option>
      </select>
    </div>

    <div class="form-group">
      <label>
        <i class="fas fa-map-marker-alt" />
        Місцезнаходження
      </label>
      <input
        v-if="workType === 'smart-point'"
        v-model="location"
        placeholder="Натисніть на карту - адреса визначиться автоматично"
        readonly
        class="form-control"
      />
      <div v-if="workType === 'smart-segment'">
        <div
          v-if="!calculatedSegment || !calculatedSegment.start_lat"
          class="smart-segment-info"
        >
          <p>
            <i class="fas fa-road" />
            Натисніть на карту - оберіть улицу та точку 1
          </p>
        </div>
        <div
          v-if="calculatedSegment && calculatedSegment.start_lat"
          class="street-segment-container"
        >
          <div class="selected-street-info">
            <i class="fas fa-road" />
            Обрана вулиця:
            <strong>{{ calculatedSegment.street_name }}</strong>
            <button
              class="btn-small btn-secondary"
              style="margin-left: 10px"
              @click="clearSelectedStreet"
            >
              <i class="fas fa-times" />
              Змінити
            </button>
          </div>
          <input
            v-model="segmentStartPoint"
            placeholder="Точка 1 обрана"
            readonly
            class="form-control"
            style="margin-bottom: 0.5rem"
          />
          <input
            v-model="segmentEndPoint"
            placeholder="Оберіть точку 2 на вулиці"
            readonly
            class="form-control"
          />
          <div v-if="calculatedSegment" class="segment-info">
            <p>
              <i class="fas fa-ruler" />
              Довжина сегменту: {{ Math.round(calculatedSegment.distance_meters) }} м
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="form-group">
      <label>
        <i class="fas fa-clipboard" />
        Опис роботи
      </label>
      <textarea
        v-model="description"
        placeholder="Детальний опис ремонтних робіт..."
        rows="3"
        class="form-control"
      />
    </div>

    <div class="form-group">
      <label>
        <i class="fas fa-clock" />
        Початок роботи *
      </label>
      <input v-model="startTime" type="datetime-local" required class="form-control" />
    </div>

    <div class="form-group">
      <label>
        <i class="fas fa-clock" />
        Завершення роботи
      </label>
      <input v-model="endTime" type="datetime-local" class="form-control" />
    </div>

    <button
      class="btn"
      :disabled="isSubmitting || !canCreateWork"
      @click="submitRepairWork"
    >
      <i class="fas fa-save" />
      {{ isSubmitting ? 'Збереження...' : 'Додати роботу' }}
    </button>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useApi } from '../composables/useApi.js';
import { useMap } from '../composables/useMap.js';
import { useNotifications } from '../composables/useNotifications.js';
import { useRouter } from '../composables/useRouter.js';

export default {
  name: 'WorkForm',
  setup() {
    // Composables
    const api = useApi();
    const map = useMap();
    const { showError, showSuccess } = useNotifications();
    const { push } = useRouter();

    // Реактивные данные
    const workType = ref('smart-point');
    const location = ref('');
    const description = ref('');
    const startTime = ref('');
    const endTime = ref('');
    const selectedWorkTypeId = ref('');
    const isSubmitting = ref(false);
    const workTypes = ref([]);

    // Данные для сегментов
    const selectedStreetForSegment = ref(null);
    const segmentStartPoint = ref('');
    const segmentEndPoint = ref('');
    const calculatedSegment = ref(null);

    // Вычисляемые свойства
    const canCreateWork = computed(() => {
      const hasWorkType = selectedWorkTypeId.value;
      const hasLocation =
        workType.value === 'smart-point' ? location.value : calculatedSegment.value;
      const hasStartTime = startTime.value;
      return hasWorkType && hasLocation && hasStartTime;
    });

    // Проверяем, есть ли выбранная улица из поиска
    const hasSelectedStreetFromSearch = computed(() => {
      if (workType.value !== 'smart-segment') return false;
      const currentMapState = map.getMapState();
      return currentMapState.hasSelectedStreet;
    });

    // Методы
    const setWorkType = type => {
      workType.value = type;

      // Очищаем данные при смене типа
      location.value = '';
      segmentStartPoint.value = '';
      segmentEndPoint.value = '';
      calculatedSegment.value = null;

      // Очищаем временные маркеры и выбранный сегмент
      map.clearTempMarkers();
      map.clearSelectedSegment();

      // Сохраняем выбранную улицу при переключении на сегмент
      if (type === 'smart-segment') {
        // Проверяем, есть ли уже выбранная улица в глобальном состоянии
        const currentMapState = map.getMapState();

        if (currentMapState.hasSelectedStreet) {
          console.log(
            `WorkForm: Сохраняем выбранную улицу при переключении: ${currentMapState.selectedStreet}`
          );
          // НЕ очищаем подсветку улицы - оставляем её видимой
          // selectedStreetForSegment остается null - будет заполнен при первом клике
        } else {
          // Если улицы нет - очищаем подсветку
          map.clearHighlightedStreet();
          selectedStreetForSegment.value = null;
        }
      } else {
        // Для режима точки очищаем подсветку улицы
        map.clearHighlightedStreet();
        selectedStreetForSegment.value = null;
      }

      // Убеждаемся, что обработчик кликов все еще активен
      map.onMapClick(handleMapClick);
    };

    const clearSelectedStreet = () => {
      selectedStreetForSegment.value = null;
      segmentStartPoint.value = '';
      segmentEndPoint.value = '';
      calculatedSegment.value = null;

      // Очищаем карту
      map.clearTempMarkers();
      map.clearSelectedSegment();
      map.clearHighlightedStreet();
    };

    const setDefaultDateTime = () => {
      const now = new Date();
      now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
      startTime.value = now.toISOString().slice(0, 16);
    };

    const fetchWorkTypes = async () => {
      try {
        // Логи удалены в продакшн
        const types = await api.fetchWorkTypes();
        workTypes.value = types;
      } catch (error) {
        console.error('WorkForm: Ошибка загрузки типов работ:', error);
        showError('Помилка завантаження типів робіт');
      }
    };

    const submitRepairWork = async () => {
      if (!canCreateWork.value) return;

      isSubmitting.value = true;
      try {
        const workData = {
          work_type_id: selectedWorkTypeId.value,
          description: description.value,
          start_datetime: startTime.value,
          end_datetime: endTime.value || null,
          status: 'planned'
        };

        if (workType.value === 'smart-point') {
          // Данные точки из mapService или текущих координат
          const point = map.getCurrentPoint();
          if (point) {
            workData.latitude = point.lat;
            workData.longitude = point.lng;
            workData.location = location.value;
          }
        } else if (workType.value === 'smart-segment' && calculatedSegment.value) {
          // Данные сегмента
          workData.street_name = selectedStreetForSegment.value?.name;
          workData.start_latitude = calculatedSegment.value.start_lat;
          workData.start_longitude = calculatedSegment.value.start_lon;
          workData.end_latitude = calculatedSegment.value.end_lat;
          workData.end_longitude = calculatedSegment.value.end_lon;
          workData.start_location = `${calculatedSegment.value.start_lat.toFixed(6)}, ${calculatedSegment.value.start_lon.toFixed(6)}`;
          workData.end_location = `${calculatedSegment.value.end_lat.toFixed(6)}, ${calculatedSegment.value.end_lon.toFixed(6)}`;

          // Геометрия сегмента как GeoJSON строка
          if (calculatedSegment.value.geometry) {
            workData.street_segment_geojson = JSON.stringify(
              calculatedSegment.value.geometry
            );
          }
        }

        const newWork = await api.createRepairWork(workData);

        // Добавляем новую работу на карту
        if (newWork) {
          map.addWorkToMap(newWork);
        }

        showSuccess('Ремонтну роботу успішно створено!');
        resetForm();

        // Небольшая задержка перед переходом для корректного рендеринга
        await new Promise(resolve => setTimeout(resolve, 100));

        // Переход к списку работ
        push('/list');
      } catch (error) {
        console.error('Ошибка создания работы:', error);
        // Используем правильную обработку ошибок API
        let errorMessage = 'Помилка створення роботи';

        if (error.name === 'ApiError' && typeof error.getUserMessage === 'function') {
          errorMessage = error.getUserMessage();
        } else if (error.details) {
          // Обрабатываем Pydantic ошибки валидации (422)
          if (Array.isArray(error.details)) {
            const validationErrors = error.details
              .map(err => {
                // Переводим типичные ошибки валидации дат
                if (err.msg && err.msg.includes('end_datetime')) {
                  if (
                    err.msg.includes('позже времени начала') ||
                    err.msg.includes('should be after start')
                  ) {
                    return 'Час завершення повинен бути пізніше часу початку роботи';
                  }
                }
                return err.msg || err.message || String(err);
              })
              .join(', ');
            errorMessage = validationErrors;
          } else if (typeof error.details === 'string') {
            errorMessage = error.details;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }

        showError(errorMessage);
      } finally {
        isSubmitting.value = false;
      }
    };

    const resetForm = () => {
      description.value = '';
      endTime.value = '';
      selectedWorkTypeId.value = '';
      location.value = '';
      selectedStreetForSegment.value = null;
      segmentStartPoint.value = '';
      segmentEndPoint.value = '';
      calculatedSegment.value = null;
      setDefaultDateTime();

      // Очищаем карту
      map.clearTempMarkers();
      map.clearSelectedSegment();
      map.clearHighlightedStreet();

      // 🎯 Очищаем выбранную улицу из глобального состояния
      map.clearSelectedStreet();

      // 🎯 Уведомляем компонент поиска об очистке
      notifyStreetCleared();
    };

    // 🎯 Функция для уведомления компонента поиска об выборе улицы
    const notifyStreetSelected = streetName => {
      // Отправляем событие через window для связи между компонентами
      window.dispatchEvent(
        new CustomEvent('streetSelected', {
          detail: { streetName }
        })
      );
      console.log(`🎯 WorkForm: Уведомили о выборе улицы: ${streetName}`);
    };

    // 🎯 Функция для уведомления компонента поиска об очистке улицы
    const notifyStreetCleared = () => {
      // Отправляем событие через window для связи между компонентами
      window.dispatchEvent(new CustomEvent('streetCleared'));
      console.log('🎯 WorkForm: Уведомили об очистке улицы');
    };

    // Обработка кликов по карте
    const handleMapClick = async e => {
      if (workType.value === 'smart-point') {
        // Режим точки - определяем адрес
        try {
          const result = await api.reverseGeocode(e.latlng.lat, e.latlng.lng);
          const formatted = formatAddress(result);
          location.value =
            formatted || `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;

          // Очищаем предыдущие маркеры и добавляем новый
          map.clearTempMarkers();
          map.addTempMarker(e.latlng, {
            title: 'Місце роботи',
            className: 'temp-marker' // Убран класс 'selected' для устранения пульсации
          });
        } catch (error) {
          console.error('Ошибка геокодирования:', error);
          location.value = `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;
        }
      } else if (workType.value === 'smart-segment') {
        // Режим сегмента
        await handleSegmentClick(e);
      }
    };

    // 🚏 Форматирование адреса (дом, улица, район, индекс)
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

    // Быстрая функция расстояния (Хаверсин)
    const haversine = (lat1, lon1, lat2, lon2) => {
      const R = 6371000; // m
      const toRad = deg => (deg * Math.PI) / 180;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
      return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    };

    // Обработка кликов для сегментов
    const handleSegmentClick = async e => {
      if (!calculatedSegment.value || !calculatedSegment.value.start_lat) {
        // Первый клик - выбираем улицу и устанавливаем точку 1
        try {
          // Проверяем, есть ли уже выбранная улица в глобальном состоянии
          const currentMapState = map.getMapState();
          let streetName;
          let useSelectedStreet = false;

          if (currentMapState.hasSelectedStreet) {
            // Используем уже выбранную улицу
            streetName = currentMapState.selectedStreet;
            useSelectedStreet = true;
            console.log(`WorkForm: Используем сохраненную улицу: ${streetName}`);
          } else {
            // Определяем улицу по клику
            const result = await api.reverseGeocode(e.latlng.lat, e.latlng.lng);
            if (
              result.street_name ||
              result.road ||
              (result.address && result.address.road)
            ) {
              // Определяем название улицы из разных возможных полей
              streetName =
                result.street_name ||
                result.road ||
                (result.address && result.address.road);
            }
          }

          if (streetName) {
            selectedStreetForSegment.value = { name: streetName };

            // Загружаем и подсвечиваем геометрию улицы (только если не используем уже выбранную)
            if (!useSelectedStreet) {
              const geometry = await api.getStreetGeometry(streetName);
              if (geometry) {
                map.highlightStreet(geometry);
                // Сохраняем в глобальном состоянии для будущих переключений
                map.saveSelectedStreet(streetName, geometry);

                // 🎯 Уведомляем компонент поиска об обновлении выбранной улицы
                notifyStreetSelected(streetName);
              }
            } else {
              // 🎯 Если используем уже выбранную улицу, все равно уведомляем поиск
              notifyStreetSelected(streetName);
            }

            // Получаем читаемый адрес для точки 1
            let startPointAddress;
            try {
              const startPointGeocode = await api.reverseGeocode(
                e.latlng.lat,
                e.latlng.lng
              );
              startPointAddress =
                formatAddress(startPointGeocode) ||
                `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;
            } catch (geocodeError) {
              console.error('Ошибка геокодирования точки 1:', geocodeError);
              startPointAddress = `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;
            }

            // Устанавливаем точку 1 с читаемым адресом
            segmentStartPoint.value = `Точка 1: ${startPointAddress}`;
            segmentEndPoint.value = 'Натисніть для вибору точки 2 на цій вулиці';

            // Добавляем маркер точки 1
            map.clearTempMarkers();
            map.addTempMarker(e.latlng, {
              title: 'Точка 1',
              className: 'temp-marker start'
            });

            // Сохраняем начальную точку
            calculatedSegment.value = {
              start_lat: e.latlng.lat,
              start_lon: e.latlng.lng,
              street_name: streetName
            };
          } else {
            // Улица не найдена
            showError('Не вдалося визначити вулицю в цій точці');
          }
        } catch (error) {
          console.error('Ошибка выбора улицы:', error);
          showError('Помилка вибору вулиці');
        }
      } else {
        // Если сегмент уже полностью определён (есть start и end) — модифицируем ближайшую точку
        if (calculatedSegment.value && calculatedSegment.value.end_lat) {
          // Считаем расстояние клика до start и end
          const distToStart = haversine(
            e.latlng.lat,
            e.latlng.lng,
            calculatedSegment.value.start_lat,
            calculatedSegment.value.start_lon
          );
          const distToEnd = haversine(
            e.latlng.lat,
            e.latlng.lng,
            calculatedSegment.value.end_lat,
            calculatedSegment.value.end_lon
          );

          // Определяем какую точку двигаем
          let newStartLat = calculatedSegment.value.start_lat;
          let newStartLon = calculatedSegment.value.start_lon;
          let newEndLat = calculatedSegment.value.end_lat;
          let newEndLon = calculatedSegment.value.end_lon;

          if (distToStart < distToEnd) {
            // Обновляем стартовую точку
            newStartLat = e.latlng.lat;
            newStartLon = e.latlng.lng;
          } else {
            // Обновляем конечную точку
            newEndLat = e.latlng.lat;
            newEndLon = e.latlng.lng;
          }

          const segmentData = {
            street_name: calculatedSegment.value.street_name,
            start_lat: newStartLat,
            start_lon: newStartLon,
            end_lat: newEndLat,
            end_lon: newEndLon
          };

          try {
            const result = await api.calculateStreetSegment(segmentData);
            calculatedSegment.value = {
              ...calculatedSegment.value,
              start_lat: result.start_point.lat,
              start_lon: result.start_point.lon,
              end_lat: result.end_point.lat,
              end_lon: result.end_point.lon,
              distance_meters: result.distance_meters,
              geometry: result.segment_geojson
            };

            // Перерисовываем маркеры
            map.clearTempMarkers();
            map.addTempMarker(
              { lat: result.start_point.lat, lng: result.start_point.lon },
              {
                title: 'Точка 1',
                className: 'temp-marker start'
              }
            );
            map.addTempMarker(
              { lat: result.end_point.lat, lng: result.end_point.lon },
              {
                title: 'Точка 2',
                className: 'temp-marker end'
              }
            );

            // Обновляем подписи
            try {
              const startAddr = await api.reverseGeocode(
                result.start_point.lat,
                result.start_point.lon
              );
              const endAddr = await api.reverseGeocode(
                result.end_point.lat,
                result.end_point.lon
              );
              segmentStartPoint.value = `Точка 1: ${formatAddress(startAddr)}`;
              segmentEndPoint.value = `Точка 2: ${formatAddress(endAddr)}`;
            } catch {
              segmentStartPoint.value = `Точка 1: ${result.start_point.lat.toFixed(6)}, ${result.start_point.lon.toFixed(6)}`;
              segmentEndPoint.value = `Точка 2: ${result.end_point.lat.toFixed(6)}, ${result.end_point.lon.toFixed(6)}`;
            }

            // Отображаем вычисленный сегмент
            // Сначала убираем подсветку всей улицы
            map.clearHighlightedStreet();
            // Затем отображаем только сегмент
            map.displayCalculatedSegment(result);
          } catch (err) {
            console.error('Ошибка изменения сегмента:', err);
            showError('Не вдалося змінити сегмент');
          }

          return; // прекращаем дальнейшую обработку, т.к. уже обработали клик
        }

        // Второй клик - устанавливаем точку 2 и вычисляем сегмент
        try {
          // Получаем читаемый адрес для точки 2
          const endPointGeocode = await api.reverseGeocode(e.latlng.lat, e.latlng.lng);
          const endPointAddress =
            formatAddress(endPointGeocode) ||
            `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;

          segmentEndPoint.value = `Точка 2: ${endPointAddress}`;

          // Добавляем маркер точки 2
          map.addTempMarker(e.latlng, {
            title: 'Точка 2',
            className: 'temp-marker end'
          });
        } catch (geocodeError) {
          console.error('Ошибка геокодирования точки 2:', geocodeError);
          // В случае ошибки геокодирования используем координаты
          segmentEndPoint.value = `Точка 2: ${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;

          // Добавляем маркер точки 2
          map.addTempMarker(e.latlng, {
            title: 'Точка 2',
            className: 'temp-marker end'
          });
        }

        // Вычисляем сегмент
        try {
          const segmentData = {
            street_name: calculatedSegment.value.street_name,
            start_lat: calculatedSegment.value.start_lat,
            start_lon: calculatedSegment.value.start_lon,
            end_lat: e.latlng.lat,
            end_lon: e.latlng.lng
          };

          const result = await api.calculateStreetSegment(segmentData);
          // Обновляем данные сегмента с учётом скорректированных ("прищелкнутых") точек
          calculatedSegment.value = {
            ...calculatedSegment.value,
            start_lat: result.start_point.lat,
            start_lon: result.start_point.lon,
            end_lat: result.end_point.lat,
            end_lon: result.end_point.lon,
            distance_meters: result.distance_meters,
            geometry: result.segment_geojson
          };

          // Перерисовываем маркеры точек уже на самой дороге
          map.clearTempMarkers();
          map.addTempMarker(
            { lat: result.start_point.lat, lng: result.start_point.lon },
            {
              title: 'Точка 1 (уточнено)',
              className: 'temp-marker start'
            }
          );
          map.addTempMarker(
            { lat: result.end_point.lat, lng: result.end_point.lon },
            {
              title: 'Точка 2 (уточнено)',
              className: 'temp-marker end'
            }
          );

          // Обновляем текстовое представление точек с новыми координатами
          try {
            const startAddr = await api.reverseGeocode(
              result.start_point.lat,
              result.start_point.lon
            );
            const endAddr = await api.reverseGeocode(
              result.end_point.lat,
              result.end_point.lon
            );
            segmentStartPoint.value = `Точка 1: ${formatAddress(startAddr)}`;
            segmentEndPoint.value = `Точка 2: ${formatAddress(endAddr)}`;
          } catch {
            segmentStartPoint.value = `Точка 1: ${result.start_point.lat.toFixed(6)}, ${result.start_point.lon.toFixed(6)}`;
            segmentEndPoint.value = `Точка 2: ${result.end_point.lat.toFixed(6)}, ${result.end_point.lon.toFixed(6)}`;
          }

          // Отображаем вычисленный сегмент
          // Сначала убираем подсветку всей улицы
          map.clearHighlightedStreet();
          // Затем отображаем только сегмент
          map.displayCalculatedSegment(result);
        } catch (error) {
          console.error('Ошибка вычисления сегмента:', error);
          showError('Помилка обчислення сегменту');
        }
      }
    };

    // Обработчик очистки улицы из поиска
    const handleStreetCleared = () => {
      console.log('WorkForm: Получено событие очистки улицы');

      // Очищаем локальное состояние сегмента
      selectedStreetForSegment.value = null;
      segmentStartPoint.value = '';
      segmentEndPoint.value = '';
      calculatedSegment.value = null;

      // Очищаем временные маркеры и выбранный сегмент на карте
      map.clearTempMarkers();
      map.clearSelectedSegment();

      console.log('WorkForm: Локальное состояние сегмента очищено');
    };

    // Инициализация
    onMounted(() => {
      setDefaultDateTime();
      fetchWorkTypes();
      map.onMapClick(handleMapClick);

      // Подписываемся на событие очистки улицы
      map.onStreetCleared(handleStreetCleared);
    });

    // Очистка при размонтировании
    onUnmounted(() => {
      // Отписываемся от события очистки улицы
      map.offStreetCleared(handleStreetCleared);
    });

    return {
      workType,
      location,
      description,
      startTime,
      endTime,
      selectedWorkTypeId,
      isSubmitting,
      workTypes,
      selectedStreetForSegment,
      segmentStartPoint,
      segmentEndPoint,
      calculatedSegment,
      canCreateWork,
      hasSelectedStreetFromSearch,
      setWorkType,
      clearSelectedStreet,
      submitRepairWork,
      resetForm,
      handleMapClick,
      handleSegmentClick
    };
  }
};
</script>
