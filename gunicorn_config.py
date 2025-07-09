import os

# Simple configuration for internal use only
bind = "0.0.0.0:5000"
workers = 3
worker_class = "sync"
timeout = 60
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = 'portfolio_app'

# App loading
preload_app = True