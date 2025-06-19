#!/bin/sh
set -e

echo "=== Railway Startup Script ==="
echo "PORT environment variable: '$PORT'"
echo "All environment variables:"
printenv | grep -E "PORT|RAILWAY" || true

# Попробуем разные способы получения порта
if [ -n "$PORT" ]; then
    PORT_NUM="$PORT"
    echo "Using PORT: $PORT_NUM"
elif [ -n "$RAILWAY_PORT" ]; then
    PORT_NUM="$RAILWAY_PORT"
    echo "Using RAILWAY_PORT: $PORT_NUM"
else
    PORT_NUM="8000"
    echo "Using default port: $PORT_NUM"
fi

echo "Final port number: $PORT_NUM"
echo "Starting application..."

# Запускаем приложение
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT_NUM" --log-level info 