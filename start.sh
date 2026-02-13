#!/bin/bash
# Use the PORT environment variable if present, otherwise default to 80
PORT="${PORT:-80}"
echo "Starting application on port $PORT..."
exec gunicorn --bind "0.0.0.0:$PORT" --workers 1 --timeout 120 app:app
