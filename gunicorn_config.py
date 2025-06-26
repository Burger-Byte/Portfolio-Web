# gunicorn_config.py - Production configuration for Gunicorn
import os

# Server socket
bind = "0.0.0.0:443"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# SSL Configuration
cert_path = os.getenv('SSL_CERT_PATH')
key_path = os.getenv('SSL_KEY_PATH')

if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
    certfile = cert_path
    keyfile = key_path
    ssl_version = 5  # TLS 1.2+
    
# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'portfolio_app'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# Preload app for better performance
preload_app = True

# Restart workers after this many requests (helps with memory leaks)
max_requests = 1000
max_requests_jitter = 50