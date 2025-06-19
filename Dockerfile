# Multi-stage build для оптимизации размера
# Version: 2024-12-28-v2 - Fixed Vite build with npx
FROM node:18-alpine AS frontend-builder

# Установка зависимостей frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Копирование исходников frontend
COPY frontend/ ./frontend/
COPY vite.config.js ./

# Отладочная информация
RUN ls -la
RUN ls -la frontend/
RUN npm list vite || echo "Vite not found in dependencies"

# Сборка frontend (минимальные требования к памяти)
ENV NODE_OPTIONS="--max-old-space-size=384"
RUN npx vite build --mode production

# Python backend stage
FROM python:3.11-slim AS backend

# Установка системных зависимостей
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Установка uv
RUN pip install --no-cache-dir uv

# Создание рабочей директории
WORKDIR /app

# Копирование конфигурации uv
COPY pyproject.toml ./
COPY uv.lock ./

# Копирование исходного кода
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Отладочная информация  
RUN ls -la  
RUN cat pyproject.toml | head -20

# Установка зависимостей через uv (основные пакеты)
RUN uv pip install --system fastapi uvicorn[standard] sqlalchemy alembic pydantic pydantic-settings python-dotenv structlog shapely aiofiles aiohttp fuzzywuzzy numpy

# Копирование собранного frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Копирование данных улиц
COPY frontend/static/data/ ./frontend/static/data/

# Копирование startup script
COPY start.sh ./
RUN chmod +x start.sh

# Создание директории для базы данных
RUN mkdir -p /app/db && chmod 755 /app/db

# Создание пользователя для безопасности (отключаем для отладки)
# RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
# USER app

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENVIRONMENT=production
ENV DATABASE_TYPE=sqlite
ENV SQLITE_DATABASE_PATH=/app/db/app.db

# Принудительное обновление кеша (изменяем при каждом деплое)
ARG CACHE_BUST=2024-12-28-v4-fixed-port
RUN echo "Cache bust: $CACHE_BUST"

# Здоровье контейнера (Railway делает свой healthcheck)
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:$PORT/health || exit 1

# Экспорт порта
EXPOSE $PORT

# Отладочная информация перед запуском
RUN echo "Checking application structure..." && ls -la backend/app/ && ls -la frontend/

# Команда запуска через startup script
CMD ["./start.sh"] 