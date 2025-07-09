#!/bin/bash

set -e

mkdir -p /app/logs

echo "Starting Portfolio Application..."
echo "Environment: ${FLASK_ENV:-development}"

# Function to create redirect app
create_redirect_app() {
    cat > /app/redirect_server.py << 'EOF'
from werkzeug.serving import run_simple
from werkzeug.wrappers import Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException

class RedirectApp:
    def __init__(self):
        self.url_map = Map([
            Rule('/', defaults={'path': ''}, endpoint='redirect'),
            Rule('/<path:path>', endpoint='redirect')
        ])
    
    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return self.on_redirect(request, **values)
        except HTTPException as e:
            return e
    
    def on_redirect(self, request, path=''):
        host = request.headers.get('Host', 'jaquesburger.com').split(':')[0]
        location = f'https://{host}/{path}'
        if request.query_string:
            location += f'?{request.query_string.decode()}'
        return Response('', status=301, headers={'Location': location})
    
    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)
    
    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

from werkzeug.wrappers import Request
application = RedirectApp()
EOF
}

if [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ] && [ "$FLASK_ENV" = "production" ]; then
    echo "SSL certificates found. Starting production servers with SSL..."
    echo "Certificate: $SSL_CERT_PATH"
    echo "Key: $SSL_KEY_PATH"
    
    # Create the redirect app
    create_redirect_app
    
    # Start HTTP redirect server with gunicorn in background
    echo "Starting HTTP redirect server on port 80..."
    gunicorn \
        --bind 0.0.0.0:80 \
        --workers 2 \
        --worker-class sync \
        --daemon \
        --access-logfile /app/logs/redirect-access.log \
        --error-logfile /app/logs/redirect-error.log \
        --pid /tmp/redirect.pid \
        redirect_server:application &
    
    # Give redirect server time to start
    sleep 2
    
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
        echo "WARNING: Running in production without SSL!"
        echo "Expected certificate at: $SSL_CERT_PATH"
        echo "Expected key at: $SSL_KEY_PATH"
    fi
    
    # For development or when SSL certs are missing
    # Only bind to port 80, not 5000
    echo "Starting HTTP server on port 80..."
    exec gunicorn \
        --bind 0.0.0.0:80 \
        --workers 3 \
        --timeout 60 \
        --access-logfile - \
        --error-logfile - \
        app:app
fi