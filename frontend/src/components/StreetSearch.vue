<template>
  <div class="search-panel">
    <div class="search-container">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Введіть назву вулиці для пошуку..."
        class="search-input"
        @keyup.enter="searchStreets"
        @input="onSearchInput"
      />
      <button class="search-btn" :disabled="!searchQuery.trim()" @click="searchStreets">
        <i class="fas fa-search" />
      </button>

      <!-- 🎯 Кнопка очистки выбранной улицы -->
      <button
        v-if="isStreetSelected"
        class="clear-street-btn"
        title="Очистити виділення вулиці"
        @click="clearStreetSelection"
      >
        <i class="fas fa-times" />
      </button>
      <div v-if="searchResults.length > 0" class="search-results">
        <div
          v-for="result in searchResults"
          :key="result.street_name"
          class="search-result-item"
          @click="selectSearchResult(result)"
        >
          <i class="fas fa-map-marker-alt" />
          {{ result.street_name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, computed } from 'vue';
import { useMap } from '../composables/useMap.js';
import { useApi } from '../composables/useApi.js';
import { useNotifications } from '../composables/useNotifications.js';

export default {
  name: 'StreetSearch',
  setup() {
    // Composables
    const map = useMap();
    const api = useApi();
    const { showError, showSuccess } = useNotifications();

    const searchQuery = ref('');
    const searchResults = ref([]);
    let searchTimeout = null;

    // Computed свойство для определения выбранной улицы
    const isStreetSelected = computed(() => {
      const mapState = map.getMapState();
      return mapState.hasSelectedStreet;
    });

    // Восстановление выбранной улицы при загрузке компонента
    onMounted(() => {
      const mapState = map.getMapState();
      if (mapState.selectedStreet) {
        searchQuery.value = mapState.selectedStreet;
        console.log(
          `StreetSearch: Восстановлена выбранная улица: ${mapState.selectedStreet}`
        );
      }
    });

    const onSearchInput = async () => {
      // Debounce search
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }

      searchTimeout = setTimeout(async () => {
        if (searchQuery.value.trim().length >= 2) {
          await searchStreets();
        } else {
          searchResults.value = [];
        }
      }, 300);
    };

    const searchStreets = async () => {
      if (!searchQuery.value.trim()) {
        searchResults.value = [];
        return;
      }

      try {
        // Используем быстрый поиск из нашего API
        const response = await api.searchStreets(searchQuery.value);
        searchResults.value = response;
      } catch (error) {
        showError('Помилка пошуку вулиць: ' + error.message);
        searchResults.value = [];
      }
    };

    const selectSearchResult = async result => {
      try {
        // Получаем геометрию улицы для выделения, передаем ключ если есть
        let geometry;
        if (result.street_key) {
          // Используем специальный метод API с ключом
          const baseUrl =
            window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
          const response = await fetch(
            `${baseUrl}/api/v1/streets/fast-geometry/${encodeURIComponent(result.street_name)}?street_key=${encodeURIComponent(result.street_key)}`
          );
          geometry = response.ok ? await response.json() : null;
        } else {
          geometry = await api.getStreetGeometry(result.street_name);
        }

        if (
          geometry &&
          ((geometry.coordinates && geometry.coordinates.length > 0) ||
            (geometry.segments && geometry.segments.length > 0))
        ) {
          // Выделяем улицу на карте
          map.highlightStreet(geometry);

          // Сохраняем выбранную улицу в глобальном состоянии
          map.saveSelectedStreet(result.street_name, geometry);

          // Центрируем карту на улице с улучшенной логикой
          if (geometry.segments && geometry.segments.length > 0) {
            // Используем улучшенный метод для сегментов
            map.fitBoundsForSegments(geometry.segments, {
              padding: [40, 40],
              maxZoom: 15
            });
          } else if (geometry.coordinates && geometry.coordinates.length > 0) {
            map.fitBounds(geometry.coordinates, { padding: [40, 40], maxZoom: 16 });
          }

          showSuccess(`Знайдено: ${result.street_name}`);
        } else {
          showError('Не вдалося знайти геометрію вулиці');
        }

        // Обновляем поле поиска с выбранным названием
        searchQuery.value = result.street_name;

        // Скрываем результаты поиска
        searchResults.value = [];
      } catch {
        showError('Помилка відображення вулиці на карті');
      }
    };

    // Метод для очистки выбранной улицы
    const clearStreetSelection = () => {
      // Очищаем глобальное состояние
      map.clearSelectedStreet();

      // Очищаем подсветку на карте
      map.clearHighlightedStreet();

      // Очищаем поле поиска
      searchQuery.value = '';

      showSuccess('Виділення вулиці очищено');
      console.log('🗑️ StreetSearch: Очищено выбранную улицу');
    };

    // Очистка результатов при изменении запроса
    watch(searchQuery, newQuery => {
      if (!newQuery.trim()) {
        searchResults.value = [];
      }
    });

    return {
      // Состояние
      searchQuery,
      searchResults,
      isStreetSelected,

      // Методы
      onSearchInput,
      searchStreets,
      selectSearchResult,
      clearStreetSelection
    };
  }
};
</script>

<style scoped>
.search-panel {
  padding: 15px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.search-container {
  position: relative;
  max-width: 600px;
  margin: 0 auto;
}

.search-input {
  width: 100%;
  padding: 12px 50px 12px 16px;
  border: 2px solid #ddd;
  border-radius: 25px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.3s;
}

.search-input:focus {
  border-color: #667eea;
}

.search-btn {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
  background: #667eea;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-btn:hover:not(:disabled) {
  background: #5a67d8;
}

.search-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 🎯 Кнопка очистки выбранной улицы */
.clear-street-btn {
  position: absolute;
  right: 50px;
  top: 50%;
  transform: translateY(-50%);
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 50%;
  width: 35px;
  height: 35px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.clear-street-btn:hover {
  background: #ff5252;
  transform: translateY(-50%) scale(1.05);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-top: 5px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-result-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.3s;
}

.search-result-item:hover {
  background: #f8f9fa;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item i {
  color: #667eea;
  flex-shrink: 0;
}
</style>
