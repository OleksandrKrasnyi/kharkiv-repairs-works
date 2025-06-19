<template>
  <div class="notifications-container">
    <!-- Error Message -->
    <div v-if="errorMessage" class="error-message" :class="{ visible: errorMessage }">
      <i class="fas fa-exclamation-triangle" />
      {{ errorMessage }}
      <button class="close-btn" @click="clearError">
        <i class="fas fa-times" />
      </button>
    </div>

    <!-- Success Message -->
    <div
      v-if="successMessage"
      class="success-message"
      :class="{ visible: successMessage }"
    >
      <i class="fas fa-check-circle" />
      {{ successMessage }}
      <button class="close-btn" @click="clearSuccess">
        <i class="fas fa-times" />
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner" />
      <p>Завантаження...</p>
    </div>
  </div>
</template>

<script>
import { useNotifications } from '../composables/useNotifications.js';

export default {
  name: 'GlobalNotifications',
  setup() {
    // Используем composable вместо локального состояния
    const { errorMessage, successMessage, loading, clearError, clearSuccess } =
      useNotifications();

    return {
      errorMessage,
      successMessage,
      loading,
      clearError,
      clearSuccess
    };
  }
};
</script>

<style scoped>
.notifications-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.error-message,
.success-message {
  padding: 12px 16px;
  margin-bottom: 10px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateX(100%);
  transition: transform 0.3s ease-out;
}

.error-message.visible,
.success-message.visible {
  transform: translateX(0);
}

.error-message {
  background-color: #fee;
  color: #c53030;
  border-left: 4px solid #c53030;
}

.success-message {
  background-color: #f0fff4;
  color: #2d7d32;
  border-left: 4px solid #2d7d32;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.7;
  margin-left: auto;
  padding: 4px;
}

.close-btn:hover {
  opacity: 1;
}

.loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
