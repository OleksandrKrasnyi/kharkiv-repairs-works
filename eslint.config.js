import js from '@eslint/js';
import vue from 'eslint-plugin-vue';
import globals from 'globals';

export default [
  js.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    // Основные файлы приложения - используют глобальные переменные
    files: ['frontend/static/js/app.js', 'frontend/static/js/components/**/*.js'],
    languageOptions: {
      globals: {
        ...globals.browser,
        Vue: 'readonly',
        L: 'readonly', // Leaflet
        window: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly',
        // Ваши модули
        mapService: 'readonly',
        workTypeManager: 'readonly',
        streetSearcher: 'readonly',
        workFormHandler: 'readonly',
        workListManager: 'readonly',
        uiManager: 'readonly',
        apiService: 'readonly',
        // Утилиты
        DateUtils: 'readonly',
        GeoUtils: 'readonly',
        Validators: 'readonly',
        ApiError: 'readonly'
      },
      ecmaVersion: 2022,
      sourceType: 'script'
    },
    rules: {
      // Общие правила качества кода
      'no-unused-vars': 'warn',
      'no-console': 'off', // разрешаем console для отладки
      'no-debugger': 'error',
      'no-duplicate-imports': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-arrow-callback': 'warn',
      
      // Стиль кода
      'indent': ['error', 2],
      'quotes': ['error', 'single', { 'allowTemplateLiterals': true }],
      'semi': ['error', 'always'],
      'comma-dangle': ['error', 'never'],
      'object-curly-spacing': ['error', 'always'],
      'array-bracket-spacing': ['error', 'never'],
      
      // Качество кода
      'eqeqeq': ['error', 'always'],
      'no-implicit-globals': 'error',
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      
      // Современные практики
      'prefer-template': 'warn',
      'template-curly-spacing': ['error', 'never'],
      'prefer-destructuring': ['warn', {
        'array': false,
        'object': true
      }],
      
      // Обработка ошибок
      'no-empty': ['error', { 'allowEmptyCatch': false }],
      'handle-callback-err': 'warn'
    }
  },
  {
    // Файлы, которые определяют глобальные переменные
    files: ['frontend/static/js/services/**/*.js', 'frontend/static/js/utils/**/*.js'],
    languageOptions: {
      globals: {
        ...globals.browser,
        Vue: 'readonly',
        L: 'readonly',
        window: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly'
      },
      ecmaVersion: 2022,
      sourceType: 'script'
    },
    rules: {
      // Общие правила качества кода
      'no-unused-vars': 'warn',
      'no-console': 'off',
      'no-debugger': 'error',
      'no-duplicate-imports': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-arrow-callback': 'warn',
      
      // Стиль кода
      'indent': ['error', 2],
      'quotes': ['error', 'single', { 'allowTemplateLiterals': true }],
      'semi': ['error', 'always'],
      'comma-dangle': ['error', 'never'],
      'object-curly-spacing': ['error', 'always'],
      'array-bracket-spacing': ['error', 'never'],
      
      // Качество кода
      'eqeqeq': ['error', 'always'],
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      
      // Современные практики
      'prefer-template': 'warn',
      'template-curly-spacing': ['error', 'never'],
      'prefer-destructuring': ['warn', {
        'array': false,
        'object': true
      }],
      
      // Для глобальных переменных
      'no-implicit-globals': 'off',
      'no-redeclare': 'off'
    }
  },
  {
    files: ['frontend/**/*.html'],
    languageOptions: {
      globals: {
        ...globals.browser
      }
    }
  }
]; 