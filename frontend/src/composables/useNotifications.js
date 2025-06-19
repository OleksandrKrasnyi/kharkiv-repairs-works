import { ref } from 'vue';

// Глобальное состояние уведомлений
const errorMessage = ref('');
const successMessage = ref('');
const loading = ref(false);

/**
 * Composable для работы с уведомлениями
 * Заменяет глобальные window.showError, window.showSuccess, window.showLoading
 */
export function useNotifications() {
  const showError = message => {
    errorMessage.value = message;
    successMessage.value = '';
    setTimeout(() => {
      errorMessage.value = '';
    }, 5000);
  };

  const showSuccess = message => {
    successMessage.value = message;
    errorMessage.value = '';
    setTimeout(() => {
      successMessage.value = '';
    }, 3000);
  };

  const clearError = () => {
    errorMessage.value = '';
  };

  const clearSuccess = () => {
    successMessage.value = '';
  };

  const showLoading = show => {
    loading.value = show;
  };

  return {
    // Состояние
    errorMessage,
    successMessage,
    loading,

    // Методы
    showError,
    showSuccess,
    clearError,
    clearSuccess,
    showLoading
  };
}
