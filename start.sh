#!/bin/sh
set -e

# Determine port to listen on (Railway sets $PORT)
PORT=${PORT:-8000}

echo "=== Railway Startup Script ==="
echo "Starting application on port $PORT"

# Launch the application
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" --log-level info 