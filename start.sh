#!/bin/sh
set -e

echo "=== Railway Startup Script ==="
echo "Starting application on port 8000 (ignoring PORT variable due to Railway bug)"

# Запускаем приложение на фиксированном порту 8000
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --log-level info 