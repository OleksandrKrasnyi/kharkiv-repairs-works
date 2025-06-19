<template>
  <div id="app">
    <!-- Главный заголовок -->
    <div class="header">
      <h1>
        <i class="fas fa-tools" />
        Харків Ремонтні Роботи
      </h1>
      <p>Система управління ремонтними роботами на дорогах міста</p>
    </div>

    <!-- Навигационная панель -->
    <div :key="navigationKey" class="navigation">
      <router-link
        to="/create"
        class="nav-btn"
        :class="{ active: $route.name === 'create' }"
      >
        <i class="fas fa-plus-circle" />
        <span>Створити ремонтну роботу</span>
      </router-link>
      <router-link
        to="/list"
        class="nav-btn"
        :class="{ active: $route.name === 'list' }"
      >
        <i class="fas fa-list-ul" />
        <span>Список робіт</span>
      </router-link>
      <router-link
        to="/types"
        class="nav-btn"
        :class="{ active: $route.name === 'types' }"
      >
        <i class="fas fa-cogs" />
        <span>Типи робіт</span>
      </router-link>
    </div>

    <!-- Основной контент -->
    <div class="main-container">
      <router-view />
    </div>

    <!-- Глобальные уведомления -->
    <GlobalNotifications />
  </div>
</template>

<script>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import GlobalNotifications from './components/GlobalNotifications.vue';

export default {
  name: 'App',
  components: {
    GlobalNotifications
  },
  setup() {
    const route = useRoute();
    const navigationKey = ref(0);

    // Принудительное обновление навигации при смене маршрута
    watch(
      () => route.name,
      () => {
        navigationKey.value++;
      }
    );

    return {
      navigationKey
    };
  }
};
</script>

<style>
/* Дополнительные стили для router-link */
.nav-btn {
  text-decoration: none;
  color: inherit;
}

.nav-btn.router-link-active,
.nav-btn.active {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}
</style>
