#!/bin/bash

set -e

mkdir -p /app/logs

echo "Starting Portfolio Application..."
echo "Environment: ${FLASK_ENV:-development}"

# With Nginx, we ONLY need Gunicorn on port 5000
# No SSL handling, no redirect server - Nginx does it all

echo "Starting Gunicorn on port 5000 (internal)..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app