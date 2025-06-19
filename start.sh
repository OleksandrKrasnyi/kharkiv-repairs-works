#!/bin/sh
set -e

# Получаем порт из переменной окружения
PORT_NUM=${PORT:-8000}

echo "=== Railway Startup Script ==="
echo "PORT environment variable: '$PORT'"
echo "Using port number: $PORT_NUM"
echo "ENVIRONMENT: $ENVIRONMENT"
echo "Starting application..."

# Запускаем приложение
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT_NUM" --log-level info 