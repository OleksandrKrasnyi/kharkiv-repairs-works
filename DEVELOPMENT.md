# Руководство по локальной разработке

## Быстрый старт

### 1. Подготовка окружения

```powershell
# Создание необходимых директорий
New-Item -ItemType Directory -Force -Path "frontend/static"
New-Item -ItemType Directory -Force -Path "frontend/dist/assets"

# Установка зависимостей Python (если еще не установлены)
pip install -r requirements.txt

# Или через uv (рекомендуется)
uv pip install fastapi uvicorn[standard] sqlalchemy alembic pydantic pydantic-settings python-dotenv structlog shapely aiofiles aiohttp fuzzywuzzy numpy python-levenshtein

# Установка зависимостей Node.js
npm install
```

### 2. Запуск приложения

**Вариант 1 (самый простой) - скрипты запуска:**

```powershell
# Запуск через батч-файл (Windows)
.\start-dev.bat

# Или через PowerShell скрипт
.\start-dev.ps1
```

**Вариант 2 (рекомендуемый) - все одной командой:**

```powershell
npm run dev:full
```

**Вариант 3 (раздельно):**

```powershell
# Терминал 1 - Бекенд
npm run dev:backend

# Терминал 2 - Фронтенд
npm run dev
```

**Вариант 4 (вручную):**

```powershell
# Терминал 1 - Бекенд
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Терминал 2 - Фронтенд
npm run dev
```

### 3. Проверка работы

После запуска будут доступны:

- Фронтенд: `http://localhost:3000`
- Бекенд: `http://localhost:8000`
- API документация: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 4. Остановка приложения

```powershell
# Остановить все процессы
Ctrl+C

# Или если нужно убить процессы принудительно
Get-Process | Where-Object {$_.ProcessName -eq "node" -or $_.ProcessName -eq "python"} | Stop-Process -Force
```

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Конфигурация приложения
ENVIRONMENT=development

# База данных
DATABASE_TYPE=sqlite
SQLITE_DATABASE_PATH=db/app.db

# Сервер
HOST=0.0.0.0
PORT=8000
DEBUG=true
RELOAD=true

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Логирование
LOG_LEVEL=INFO
```

## Особенности конфигурации

### Автоматическое определение окружения

Код автоматически определяет, в какой среде он работает:

- **Локально**: если `hostname` равен `localhost`, `127.0.0.1` или порт `3000`
- **Продакшн**: во всех остальных случаях

### Настройка API URL

В `frontend/src/services/apiService.js` реализована логика:

```javascript
function getApiBaseUrl() {
  const isDevelopment =
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.port === '3000';

  if (isDevelopment) {
    return 'http://localhost:8000'; // Полный URL для локальной разработки
  } else {
    return ''; // Относительный URL для продакшена
  }
}
```

## Проблемы и решения

### Проблема: CORS ошибки

**Решение**: Убедитесь, что в `backend/app/config.py` в `cors_origins` указаны корректные домены для фронтенда.

### Проблема: 404 ошибки на API запросы

**Решение**:

1. Проверьте, что бекенд запущен на порту 8000
2. Проверьте настройки прокси в `vite.config.js`

### Проблема: Фронтенд не подключается к бекенду

**Решение**: Убедитесь, что логика определения окружения в `apiService.js` работает корректно.
