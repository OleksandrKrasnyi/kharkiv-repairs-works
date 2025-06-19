# Multi-stage build для оптимизации размера
FROM node:18-alpine AS frontend-builder

# Установка зависимостей frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Копирование исходников frontend
COPY frontend/ ./frontend/
COPY vite.config.js ./

# Сборка frontend
RUN npm run build

# Python backend stage
FROM python:3.11-slim AS backend

# Установка системных зависимостей
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Установка Python зависимостей
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Копирование backend кода
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Копирование собранного frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Копирование данных улиц
COPY frontend/static/data/ ./frontend/static/data/

# Создание директории для базы данных
RUN mkdir -p /app/db

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Здоровье контейнера
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Экспорт порта
EXPOSE $PORT

# Команда запуска
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"] 