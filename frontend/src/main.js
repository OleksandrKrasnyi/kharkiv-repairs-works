import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';
import './style.css';

// Импорт компонентов для роутинга
import CreateWork from './components/CreateWork.vue';
import WorksList from './components/WorksList.vue';
import WorkTypes from './components/WorkTypes.vue';

// Роуты
const routes = [
  { path: '/', redirect: '/create' },
  { path: '/create', component: CreateWork, name: 'create' },
  { path: '/list', component: WorksList, name: 'list' },
  { path: '/types', component: WorkTypes, name: 'types' }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 🏗️ Создание Vue приложения
const app = createApp(App);
app.use(router);
app.mount('#app');
