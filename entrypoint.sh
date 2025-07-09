#!/bin/bash

set -e

mkdir -p /app/logs

echo "Starting Portfolio Application..."
echo "Environment: ${FLASK_ENV:-development}"

if [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ] && [ "$FLASK_ENV" = "production" ]; then
    echo "SSL certificates found. Starting production server with SSL..."
    echo "Certificate: $SSL_CERT_PATH"
    echo "Key: $SSL_KEY_PATH"
    
    # Create a simple HTTP redirect app file
    cat > /tmp/redirect_app.py << 'EOF'
from flask import Flask, redirect, request

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirect_to_https(path):
    return redirect(f'https://{request.host.split(":")[0]}/{path}', code=301)
EOF
    
    echo "Starting HTTP redirect server on port 80..."
    # Use gunicorn for the redirect server too
    gunicorn \
        --bind 0.0.0.0:80 \
        --workers 1 \
        --daemon \
        --access-logfile /app/logs/redirect-access.log \
        --error-logfile /app/logs/redirect-error.log \
        --pid /tmp/redirect.pid \
        redirect_app:app \
        --chdir /tmp
    
    echo "Starting HTTPS server on port 443 with SSL..."
    exec gunicorn \
        --bind 0.0.0.0:443 \
        --workers 3 \
        --timeout 60 \
        --access-logfile - \
        --error-logfile - \
        --certfile="$SSL_CERT_PATH" \
        --keyfile="$SSL_KEY_PATH" \
        app:app
    
else
    echo "Running without SSL (development mode or certificates not found)..."
    if [ "$FLASK_ENV" = "production" ]; then
        echo "Expected certificate at: $SSL_CERT_PATH"
        echo "Expected key at: $SSL_KEY_PATH"
    fi
    
    echo "Starting HTTP server on port 5000..."
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 3 \
        --timeout 60 \
        --access-logfile - \
        --error-logfile - \
        app:app
fi