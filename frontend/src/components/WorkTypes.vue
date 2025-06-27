<template>
  <div class="content-container">
    <!-- Боковая панель без карты -->
    <div class="panel full-width">
      <div class="section">
        <div class="section-header">
          <h2>
            <i class="fas fa-cogs" />
            Управління типами робіт
          </h2>
          <p>Створюйте та редагуйте типи ремонтних робіт</p>
        </div>

        <div class="work-type-form">
          <h4>
            <i class="fas fa-plus" />
            {{ editingWorkType ? 'Редагувати тип роботи' : 'Додати новий тип роботи' }}
          </h4>
          <div class="form-group">
            <label>Назва типу робіт</label>
            <input
              v-model="newWorkType.name"
              placeholder="Наприклад: Ремонт дорожнього покриття"
              class="form-control"
            />
          </div>
          <div class="form-group">
            <label>Опис (необов'язково)</label>
            <textarea
              v-model="newWorkType.description"
              placeholder="Детальний опис типу робіт..."
              rows="2"
              class="form-control"
            />
          </div>
          <div class="form-group">
            <label>Колір на карті:</label>
            <div class="color-input-group">
              <input v-model="newWorkType.color" type="color" class="color-picker" />
              <span
                class="color-preview"
                :style="{ backgroundColor: newWorkType.color }"
              />
            </div>
          </div>
          <div class="button-group">
            <button
              class="btn"
              :disabled="!newWorkType.name.trim()"
              @click="saveWorkType"
            >
              <i :class="editingWorkType ? 'fas fa-save' : 'fas fa-plus'" />
              {{ editingWorkType ? 'Зберегти зміни' : 'Додати тип роботи' }}
            </button>
            <button v-if="editingWorkType" class="btn-secondary" @click="cancelEdit">
              <i class="fas fa-times" />
              Скасувати
            </button>
          </div>
        </div>

        <div class="work-types-list">
          <h4>
            <i class="fas fa-list" />
            Існуючі типи робіт ({{ workTypes.length }})
          </h4>
          <div v-for="type in workTypes" :key="type.id" class="work-type-item">
            <div class="work-type-color" :style="{ backgroundColor: type.color }" />
            <div class="work-type-info">
              <strong>{{ type.name }}</strong>
              <p v-if="type.description">
                {{ type.description }}
              </p>
            </div>
            <div class="work-type-actions">
              <button
                class="btn-edit btn-small"
                title="Редагувати"
                @click="editWorkType(type)"
              >
                <i class="fas fa-edit" />
              </button>
              <button
                class="btn-danger btn-small"
                title="Видалити"
                @click="deleteWorkType(type.id)"
              >
                <i class="fas fa-trash" />
              </button>
            </div>
          </div>
          <div v-if="workTypes.length === 0" class="empty-state">
            <i class="fas fa-cogs" />
            <p>Типів робіт поки немає</p>
            <p class="small-text">Створіть перший тип роботи за допомогою форми вище</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import { useApi } from '../composables/useApi.js';
import { useNotifications } from '../composables/useNotifications.js';

export default {
  name: 'WorkTypes',
  setup() {
    // Composables
    const api = useApi();
    const { showError, showSuccess } = useNotifications();

    // Реактивные данные
    const workTypes = ref([]);
    const editingWorkType = ref(null);

    const newWorkType = reactive({
      name: '',
      description: '',
      color: '#667eea'
    });

    // Методы
    const fetchWorkTypes = async () => {
      try {
        const types = await api.fetchWorkTypes();
        workTypes.value = types;
      } catch (error) {
        console.error('Ошибка загрузки типов работ:', error);
        showError('Помилка завантаження типів робіт');
      }
    };

    const createWorkType = async () => {
      if (!newWorkType.name.trim()) return;

      try {
        const createdType = await api.createWorkType({
          name: newWorkType.name.trim(),
          description: newWorkType.description.trim() || null,
          color: newWorkType.color
        });

        workTypes.value.push(createdType);
        resetWorkTypeForm();

        showSuccess('Тип роботи успішно створено!');
      } catch (error) {
        console.error('Ошибка создания типа работы:', error);

        const errorMessage = error.getUserMessage
          ? error.getUserMessage()
          : error.message || 'Невідома помилка';

        showError(errorMessage);
      }
    };

    const updateWorkType = async () => {
      if (!newWorkType.name.trim() || !editingWorkType.value) return;

      try {
        const updatedType = await api.updateWorkType(editingWorkType.value.id, {
          name: newWorkType.name.trim(),
          description: newWorkType.description.trim() || null,
          color: newWorkType.color
        });

        const index = workTypes.value.findIndex(
          type => type.id === editingWorkType.value.id
        );
        if (index !== -1) {
          workTypes.value[index] = updatedType;
        }

        resetWorkTypeForm();

        showSuccess('Тип роботи успішно оновлено!');
      } catch (error) {
        console.error('Ошибка обновления типа работы:', error);

        const errorMessage = error.getUserMessage
          ? error.getUserMessage()
          : error.message || 'Невідома помилка';

        showError(errorMessage);
      }
    };

    const saveWorkType = async () => {
      if (editingWorkType.value) {
        await updateWorkType();
      } else {
        await createWorkType();
      }
    };

    const deleteWorkType = async typeId => {
      try {
        await api.deleteWorkType(typeId);
        workTypes.value = workTypes.value.filter(type => type.id !== typeId);
        showSuccess('Тип роботи успішно видалено');
      } catch (error) {
        console.error('Ошибка удаления типа работы:', error);

        const errorMessage = error.getUserMessage
          ? error.getUserMessage()
          : error.message || 'Невідома помилка';

        showError(errorMessage);
      }
    };

    const editWorkType = workType => {
      editingWorkType.value = workType;
      newWorkType.name = workType.name;
      newWorkType.description = workType.description || '';
      newWorkType.color = workType.color;
    };

    const cancelEdit = () => {
      resetWorkTypeForm();
    };

    const resetWorkTypeForm = () => {
      editingWorkType.value = null;
      newWorkType.name = '';
      newWorkType.description = '';
      newWorkType.color = '#667eea';
    };

    // Инициализация
    onMounted(() => {
      fetchWorkTypes();
    });

    return {
      workTypes,
      newWorkType,
      editingWorkType,
      fetchWorkTypes,
      saveWorkType,
      deleteWorkType,
      editWorkType,
      cancelEdit,
      resetWorkTypeForm
    };
  }
};
</script>

<style scoped>
.full-width {
  width: 100%;
}

.button-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.color-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-picker {
  width: 50px;
  height: 40px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.color-preview {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 2px solid #ddd;
}

.work-type-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 10px;
}

.work-type-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
}

.work-type-info {
  flex: 1;
}

.work-type-info strong {
  display: block;
  margin-bottom: 5px;
}

.work-type-info p {
  margin: 0;
  color: #666;
  font-size: 0.9em;
}

.work-type-actions {
  display: flex;
  gap: 8px;
}

.small-text {
  font-size: 0.9em;
  color: #666;
}
</style>
