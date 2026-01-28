"""Development Gunicorn configuration."""
from .base import *

# Development-specific overrides
bind = '0.0.0.0:8000'
workers = 2  # Fewer workers for development
worker_class = 'sync'
timeout = 120  # Longer timeout for debugging
max_requests = 0  # No limit in development
max_requests_jitter = 0

# Logging - more verbose in development
accesslog = '-'  # stdout
errorlog = '-'  # stderr
loglevel = 'debug'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'docsai-dev'

# Don't preload in development for easier debugging
preload_app = False

# Reload on code changes
reload = True
