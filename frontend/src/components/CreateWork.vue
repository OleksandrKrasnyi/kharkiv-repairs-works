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
              <i class="fas fa-plus-circle" />
              Створення ремонтної роботи
            </h2>
            <p>Оберіть тип роботи та вкажіть місцезнаходження на карті</p>
          </div>

          <WorkForm />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted } from 'vue';
import { useApi } from '../composables/useApi.js';
import { useMap } from '../composables/useMap.js';
import StreetSearch from './StreetSearch.vue';
import WorkForm from './WorkForm.vue';

export default {
  name: 'CreateWork',
  components: {
    StreetSearch,
    WorkForm
  },
  setup() {
    // Composables
    const api = useApi();
    const map = useMap();

    onMounted(async () => {
      console.log('🗺️ CreateWork: Начало инициализации...');

      // Инициализация карты
      console.log('🗺️ CreateWork: Инициализация карты...');
      await map.initMap();
      console.log('✅ CreateWork: Карта успешно инициализирована');

      // Загружаем существующие работы на карту
      try {
        console.log('📋 CreateWork: Загрузка существующих работ...');
        const works = await api.fetchRepairWorks();
        console.log(`📋 CreateWork: Получено ${works?.length || 0} работ`);

        if (works && works.length > 0) {
          await map.loadWorksToMap(works);
          console.log('✅ CreateWork: Работы добавлены на карту');
        }
      } catch (error) {
        console.error('❌ CreateWork: Ошибка загрузки работ на карту:', error);
      }

      console.log('✅ CreateWork: Инициализация завершена');
      // Обработчик кликов будет настроен в WorkForm компоненте
    });

    return {};
  }
};
</script>
