#!/bin/bash
# entrypoint.sh - Docker container startup script

set -e

# Create log directory if it doesn't exist
mkdir -p /app/logs

echo "Starting Portfolio Application..."
echo "Environment: ${FLASK_ENV:-development}"

# Check if SSL certificates exist and we're in production
if [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ] && [ "$FLASK_ENV" = "production" ]; then
    echo "SSL certificates found. Starting production servers with SSL..."
    echo "Certificate: $SSL_CERT_PATH"
    echo "Key: $SSL_KEY_PATH"
    
    # Start HTTP redirect server on port 80 in background
    echo "Starting HTTP redirect server on port 80..."
    python3 -c "
from flask import Flask, redirect
app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirect_to_https(path):
    return redirect(f'https://jaquesburger.com/{path}', code=301)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
" &
    
    # Start HTTPS server with Gunicorn on port 443
    echo "Starting HTTPS server on port 443 with SSL..."
    exec gunicorn \
        --bind 0.0.0.0:443 \
        --workers 3 \
        --timeout 60 \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --certfile="$SSL_CERT_PATH" \
        --keyfile="$SSL_KEY_PATH" \
        app:app
    
else
    echo "Running without SSL (development mode or certificates not found)..."
    if [ "$FLASK_ENV" = "production" ]; then
        echo "Expected certificate at: $SSL_CERT_PATH"
        echo "Expected key at: $SSL_KEY_PATH"
    fi
    
    # Start your existing setup - HTTP server on port 5000
    echo "Starting HTTP server on port 5000..."
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 3 \
        --timeout 60 \
        --access-logfile - \
        --error-logfile - \
        app:app
fi