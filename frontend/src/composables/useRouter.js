import { useRouter as vueUseRouter } from 'vue-router';

/**
 * Composable для работы с роутингом
 * Заменяет глобальный window.router
 */
export function useRouter() {
  const router = vueUseRouter();

  return {
    // Навигация
    push: to => router.push(to),
    replace: to => router.replace(to),
    go: delta => router.go(delta),
    back: () => router.back(),
    forward: () => router.forward(),

    // Текущий маршрут
    currentRoute: router.currentRoute,

    // Прямой доступ к роутеру
    router
  };
}
