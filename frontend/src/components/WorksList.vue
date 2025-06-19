<template>
  <div>
    <!-- Панель поиска улиц -->
    <StreetSearch />

    <div class="content-container">
      <!-- Карта -->
      <div id="map" />

      <!-- Боковая панель -->
      <div class="panel">
        <div class="section">
          <div class="section-header">
            <h2>
              <i class="fas fa-list-ul" />
              Список ремонтних робіт
            </h2>
            <div class="stats-info">
              <div class="stat-item">
                <span class="stat-number">{{ repairWorks.length }}</span>
                <span class="stat-label">
                  {{ getWorkCountText(repairWorks.length) }}
                </span>
                <span
                  v-if="
                    hasActiveFilters && repairWorks.length !== allRepairWorks.length
                  "
                  class="stat-total"
                >
                  з {{ allRepairWorks.length }}
                </span>
              </div>
              <div v-if="hasActiveFilters" class="active-filters-indicator">
                <i class="fas fa-filter" />
                <span>Фільтри активні</span>
              </div>
            </div>
            <div class="header-controls">
              <button
                class="btn-filter"
                :class="{
                  active: filters.showFilters,
                  'has-filters': hasActiveFilters
                }"
                @click="toggleFilters"
              >
                <i class="fas fa-filter" />
                Фільтри
                <span v-if="hasActiveFilters" class="filter-count">
                  {{ activeFiltersCount }}
                </span>
              </button>
            </div>
          </div>

          <!-- Панель сортировки -->
          <div class="sort-panel">
            <div class="sort-controls">
              <div class="sort-group">
                <label>
                  <i class="fas fa-sort" />
                  Сортувати за:
                </label>
                <select
                  v-model="sortBy"
                  class="form-control sort-select"
                  @change="setSortParameters(sortBy, sortOrder)"
                >
                  <option
                    v-for="option in getSortOptions()"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </div>
              <button
                class="btn-sort-order"
                :title="
                  sortOrder === 'asc'
                    ? 'Сортувати за спаданням'
                    : 'Сортувати за зростанням'
                "
                @click="toggleSortOrder"
              >
                <i
                  :class="sortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'"
                />
                {{ sortOrder === 'asc' ? 'За зростанням' : 'За спаданням' }}
              </button>
            </div>
          </div>

          <!-- Панель фильтрации -->
          <div v-if="filters.showFilters" class="filters-panel">
            <div class="filters-container">
              <div class="filter-group">
                <label>
                  <i class="fas fa-flag" />
                  Статус роботи
                </label>
                <select v-model="filters.status" class="form-control">
                  <option value="">Всі статуси</option>
                  <option value="planned">Заплановано</option>
                  <option value="in_progress">В процесі</option>
                  <option value="completed">Завершено</option>
                  <option value="cancelled">Скасовано</option>
                  <option value="delayed">Відкладено</option>
                </select>
              </div>

              <div class="filter-group">
                <label>
                  <i class="fas fa-tools" />
                  Тип роботи
                </label>
                <select v-model="filters.workTypeId" class="form-control">
                  <option value="">Всі типи</option>
                  <option v-for="type in workTypes" :key="type.id" :value="type.id">
                    {{ type.name }}
                  </option>
                </select>
              </div>

              <div class="filter-group">
                <label>
                  <i class="fas fa-calendar" />
                  Дата початку роботи (з)
                </label>
                <input v-model="filters.startDate" type="date" class="form-control" />
              </div>

              <div class="filter-group">
                <label>
                  <i class="fas fa-calendar" />
                  Дата початку роботи (до)
                </label>
                <input v-model="filters.endDate" type="date" class="form-control" />
              </div>

              <div class="filter-group">
                <label>
                  <i class="fas fa-check-circle" />
                  Завершеність
                </label>
                <select v-model="filters.isCompleted" class="form-control">
                  <option value="">Всі роботи</option>
                  <option value="true">Тільки завершені</option>
                  <option value="false">Тільки незавершені</option>
                </select>
              </div>

              <div class="filter-actions">
                <button class="btn-secondary" @click="resetFilters">
                  <i class="fas fa-undo" />
                  Скинути фільтри
                </button>
              </div>
            </div>
          </div>

          <div class="works-list">
            <div v-for="work in repairWorks" :key="work.id" class="work-item">
              <div class="work-header">
                <div class="work-title">
                  <div
                    v-if="work.work_type"
                    class="work-type-indicator"
                    :style="{ backgroundColor: work.work_type.color }"
                  />
                  <i class="fas fa-tools" />
                  {{ work.description || 'Ремонтні роботи' }}
                </div>
                <div class="work-actions">
                  <button class="btn-edit" title="Редагувати" @click="editWork(work)">
                    <i class="fas fa-edit" />
                  </button>
                  <button
                    class="btn-danger btn-small"
                    title="Видалити"
                    @click="deleteWork(work.id)"
                  >
                    <i class="fas fa-trash" />
                  </button>
                </div>
              </div>
              <div v-if="work.work_type" class="work-type-name">
                <i class="fas fa-tag" />
                {{ work.work_type.name }}
              </div>
              <div class="work-status">
                <i class="fas fa-flag" />
                {{ getStatusText(work.status) }}
              </div>
              <div class="work-details">
                <i class="fas fa-map-marker-alt" />
                {{ getWorkLocation(work) }}
              </div>
              <div class="work-time">
                <i class="fas fa-calendar" />
                {{ formatDateTime(work.start_datetime) }}
                {{
                  work.end_datetime
                    ? ' - ' + formatDateTime(work.end_datetime)
                    : ' (триває)'
                }}
              </div>
            </div>
            <!-- Улучшенное пустое состояние -->
            <div v-if="repairWorks.length === 0" class="empty-state">
              <div class="empty-icon">
                <i v-if="hasActiveFilters" class="fas fa-search" />
                <i v-else class="fas fa-inbox" />
              </div>
              <h3 v-if="hasActiveFilters">Жодної роботи не знайдено</h3>
              <h3 v-else>Ремонтних робіт поки немає</h3>
              <p v-if="hasActiveFilters">
                Спробуйте змінити параметри фільтрації або скинути фільтри
              </p>
              <p v-else>Створіть першу ремонтну роботу щоб побачити її тут</p>

              <div class="empty-actions">
                <button
                  v-if="hasActiveFilters"
                  class="btn-secondary"
                  @click="resetFilters"
                >
                  <i class="fas fa-undo" />
                  Скинути фільтри
                </button>
                <button class="btn-primary" @click="$router.push('/create')">
                  <i class="fas fa-plus" />
                  Створити роботу
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useApi } from '../composables/useApi.js';
import { useMap } from '../composables/useMap.js';
import { useNotifications } from '../composables/useNotifications.js';
import StreetSearch from './StreetSearch.vue';

export default {
  name: 'WorksList',
  components: {
    StreetSearch
  },
  setup() {
    // Composables
    const api = useApi();
    const map = useMap();
    const { showError, showSuccess } = useNotifications();

    // Реактивные данные - ЕДИНЫЙ ИСТОЧНИК ИСТИНЫ
    const allRepairWorks = ref([]); // Все работы с сервера
    const workTypes = ref([]);
    const sortBy = ref('created_at');
    const sortOrder = ref('desc');

    const filters = reactive({
      status: '',
      workTypeId: '',
      startDate: '',
      endDate: '',
      isCompleted: '',
      showFilters: false
    });

    // Computed свойства
    const hasActiveFilters = computed(() => {
      return !!(
        filters.status ||
        filters.workTypeId ||
        filters.startDate ||
        filters.endDate ||
        filters.isCompleted
      );
    });

    const activeFiltersCount = computed(() => {
      let count = 0;
      if (filters.status) count++;
      if (filters.workTypeId) count++;
      if (filters.startDate) count++;
      if (filters.endDate) count++;
      if (filters.isCompleted) count++;
      return count;
    });

    // Автоматическая фильтрация и сортировка
    const repairWorks = computed(() => {
      console.log('🔄 WorksList: Пересчет отфильтрованных работ...');
      let filtered = [...allRepairWorks.value];

      // Применяем фильтры
      if (filters.status) {
        filtered = filtered.filter(work => work.status === filters.status);
      }

      if (filters.workTypeId) {
        filtered = filtered.filter(
          work => work.work_type && work.work_type.id === parseInt(filters.workTypeId)
        );
      }

      if (filters.startDate) {
        const startDate = new Date(filters.startDate);
        filtered = filtered.filter(work => {
          if (!work.start_datetime) return false;
          const workDate = new Date(work.start_datetime);
          return workDate >= startDate;
        });
      }

      if (filters.endDate) {
        const endDate = new Date(filters.endDate);
        endDate.setHours(23, 59, 59, 999);
        filtered = filtered.filter(work => {
          if (!work.start_datetime) return false;
          const workDate = new Date(work.start_datetime);
          return workDate <= endDate;
        });
      }

      if (filters.isCompleted !== '') {
        const isCompleted = filters.isCompleted === 'true';
        filtered = filtered.filter(work => {
          const workCompleted = work.status === 'completed';
          return workCompleted === isCompleted;
        });
      }

      // Применяем сортировку
      const sorted = [...filtered].sort((a, b) => {
        let aValue, bValue;

        switch (sortBy.value) {
          case 'created_at':
            aValue = new Date(a.created_at || 0);
            bValue = new Date(b.created_at || 0);
            break;
          case 'start_datetime':
            aValue = new Date(a.start_datetime || 0);
            bValue = new Date(b.start_datetime || 0);
            break;
          case 'end_datetime':
            aValue = new Date(a.end_datetime || 0);
            bValue = new Date(b.end_datetime || 0);
            break;
          case 'status':
            aValue = a.status || '';
            bValue = b.status || '';
            break;
          case 'work_type':
            aValue = a.work_type?.name || '';
            bValue = b.work_type?.name || '';
            break;
          default:
            aValue = a[sortBy.value] || '';
            bValue = b[sortBy.value] || '';
        }

        if (aValue < bValue) return sortOrder.value === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortOrder.value === 'asc' ? 1 : -1;
        return 0;
      });

      console.log(
        `✅ WorksList: Отфильтровано и отсортировано ${sorted.length} из ${allRepairWorks.value.length} работ`
      );
      return sorted;
    });

    // Методы
    const fetchRepairWorks = async () => {
      try {
        console.log('📋 WorksList: Загрузка работ из API...');
        const works = await api.fetchRepairWorks();
        allRepairWorks.value = works;
        console.log(`📋 WorksList: Получено ${works?.length || 0} работ`);

        // 🎯 Автоматическая фильтрация через computed свойство
        // Карта обновится автоматически через watcher
      } catch (error) {
        console.error('❌ WorksList: Ошибка загрузки работ:', error);
        showError('Помилка завантаження робіт');
      }
    };

    const fetchWorkTypes = async () => {
      try {
        console.log('📋 WorksList: Загрузка типов работ из API...');
        const types = await api.fetchWorkTypes();
        workTypes.value = types;
        console.log(`📋 WorksList: Получено ${types?.length || 0} типов работ`);
      } catch (error) {
        console.error('❌ WorksList: Ошибка загрузки типов работ:', error);
      }
    };

    const deleteWork = async workId => {
      if (!confirm('Ви впевнені, що хочете видалити цю роботу?')) {
        return;
      }

      try {
        await api.deleteRepairWork(workId);

        // 🎯 УПРОЩЕНО: обновляем только один источник истины
        allRepairWorks.value = allRepairWorks.value.filter(work => work.id !== workId);
        // repairWorks обновится автоматически через computed свойство!

        // Убираем работу с карты
        map.removeWorkFromMap(workId);

        showSuccess('Роботу успішно видалено');
      } catch (error) {
        console.error('Ошибка удаления работы:', error);
        showError('Помилка видалення роботи');
      }
    };

    const editWork = () => {
      showError('Редагування робіт буде реалізовано пізніше');
    };

    const toggleFilters = () => {
      filters.showFilters = !filters.showFilters;
    };

    const resetFilters = () => {
      filters.status = '';
      filters.workTypeId = '';
      filters.startDate = '';
      filters.endDate = '';
      filters.isCompleted = '';
      // 🎯 Фильтрация произойдет автоматически через computed свойство
    };

    // 🎯 УПРОЩЕННЫЕ МЕТОДЫ СОРТИРОВКИ (без дублирования логики)
    const setSortParameters = (newSortBy, newSortOrder) => {
      console.log(`📊 WorksList: Изменение сортировки: ${newSortBy} ${newSortOrder}`);
      sortBy.value = newSortBy;
      sortOrder.value = newSortOrder;
      // Пересортировка произойдет автоматически через computed свойство
    };

    const toggleSortOrder = () => {
      const newOrder = sortOrder.value === 'asc' ? 'desc' : 'asc';
      setSortParameters(sortBy.value, newOrder);
    };

    const getSortOptions = () => {
      return [
        { value: 'created_at', label: 'Дата створення' },
        { value: 'start_datetime', label: 'Дата початку' },
        { value: 'end_datetime', label: 'Дата завершення' },
        { value: 'status', label: 'Статус' },
        { value: 'work_type', label: 'Тип роботи' }
      ];
    };

    const getWorkCountText = count => {
      if (count === 0) return 'робіт';
      if (count === 1) return 'робота';
      if (count >= 2 && count <= 4) return 'роботи';
      return 'робіт';
    };

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

    const getWorkLocation = work => {
      if (work.location) {
        return work.location;
      }
      if (work.street_name) {
        return work.street_name;
      }
      if (work.latitude && work.longitude) {
        return `${work.latitude.toFixed(4)}, ${work.longitude.toFixed(4)}`;
      }
      return 'Місцезнаходження не вказано';
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

    // 🎯 WATCHER для автоматического обновления карты при изменении отфильтрованных работ
    watch(
      repairWorks,
      async newWorks => {
        console.log('🗺️ WorksList: Обновление карты с новыми данными...');
        try {
          await map.loadWorksToMap(newWorks);
          console.log(`✅ WorksList: Карта обновлена с ${newWorks.length} работами`);
        } catch (error) {
          console.error('❌ WorksList: Ошибка обновления карты:', error);
        }
      },
      { deep: true }
    );

    // Инициализация
    onMounted(async () => {
      console.log('📋 WorksList: Инициализация компонента...');

      console.log('📋 WorksList: Загрузка типов работ...');
      await fetchWorkTypes();

      // Инициализация карты
      console.log('🗺️ WorksList: Инициализация карты...');
      await map.initMap();
      console.log('✅ WorksList: Карта инициализирована');

      // Загружаем работы после инициализации карты
      console.log('📋 WorksList: Загрузка списка работ...');
      await fetchRepairWorks();

      console.log('✅ WorksList: Компонент полностью инициализирован');
    });

    return {
      // 🎯 НОВАЯ АРХИТЕКТУРА: Единый источник истины + computed фильтрация
      repairWorks, // Computed свойство для отфильтрованных работ
      allRepairWorks, // Единый источник истины
      workTypes,
      filters,
      sortBy,
      sortOrder,
      hasActiveFilters,
      activeFiltersCount,

      // Методы (упрощенные)
      fetchRepairWorks,
      deleteWork,
      editWork,
      toggleFilters,
      resetFilters,
      setSortParameters,
      toggleSortOrder,
      getSortOptions,
      getWorkCountText,
      getStatusText,
      getWorkLocation,
      formatDateTime
    };
  }
};
</script>

<style scoped>
/* ===============================
   УЛУЧШЕННЫЕ СТИЛИ ДЛЯ СПИСКА РАБОТ
   =============================== */

/* Улучшенный заголовок */
.stats-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 8px 0;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  font-size: 16px;
  color: #4a5568;
}

.stat-total {
  font-size: 14px;
  color: #718096;
  background: #edf2f7;
  padding: 2px 6px;
  border-radius: 12px;
}

.active-filters-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #d69e2e;
  font-size: 14px;
  background: #fefcbf;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid #f6e05e;
}

/* Кнопка фильтров */
.btn-filter {
  position: relative;
  transition: all 0.2s;
}

.btn-filter.has-filters {
  background: #d69e2e;
  color: white;
  border-color: #d69e2e;
}

.btn-filter.has-filters:hover {
  background: #b7791f;
}

.filter-count {
  background: rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 12px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
}

/* Сортировка */
.sort-panel {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap; /* Запрещаем перенос */
}

.sort-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0; /* Позволяем сжиматься */
}

.sort-select {
  flex: 1;
  min-width: 120px; /* Уменьшили минимальную ширину */
}

.btn-sort-order {
  background: #4299e1;
  color: white;
  border: 1px solid #4299e1;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-sort-order:hover {
  background: #3182ce;
  border-color: #3182ce;
}

/* Фильтры */
.filters-panel {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 16px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filters-container {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  font-weight: 500;
  color: #4a5568;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
  margin-top: 8px;
}

/* Улучшенное пустое состояние */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #718096;
  background: #fafafa;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
  margin: 24px 0;
}

.empty-icon {
  font-size: 48px;
  color: #cbd5e0;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  color: #4a5568;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 24px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

/* Элементы работ */
.work-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background: white;
  transition: all 0.2s;
  position: relative;
}

.work-item:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.work-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.work-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #2d3748;
  flex: 1;
}

.work-type-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.work-actions {
  display: flex;
  gap: 8px;
}

.work-type-name,
.work-status,
.work-details,
.work-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  margin-bottom: 8px;
  color: #4a5568;
}

.work-type-name i,
.work-status i,
.work-details i,
.work-time i {
  width: 16px;
  color: #718096;
}

/* Адаптивность */
@media (max-width: 768px) {
  .filters-container {
    grid-template-columns: 1fr;
  }

  .sort-controls {
    flex-wrap: wrap; /* На мобильных разрешаем перенос */
    gap: 8px;
  }

  .sort-group {
    min-width: auto;
    flex: 1 1 100%; /* На мобильных занимает всю ширину */
  }

  .btn-sort-order {
    justify-content: center;
    flex: 1 1 auto;
  }
}

@media (max-width: 480px) {
  .sort-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .sort-group {
    min-width: auto;
  }

  .btn-sort-order {
    justify-content: center;
  }
  .empty-actions {
    flex-direction: column;
    align-items: center;
  }

  .work-header {
    flex-direction: column;
    gap: 12px;
  }

  .work-actions {
    align-self: flex-end;
  }
}
</style>
