"""Production Gunicorn configuration."""
from .base import *
import multiprocessing

# Production-specific overrides
bind = 'unix:/run/gunicorn.sock'
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
timeout = 30
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = '/var/log/django/gunicorn-access.log'
errorlog = '/var/log/django/gunicorn-error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'docsai-production'

# Preload app for better performance
preload_app = True

# Graceful timeout
graceful_timeout = 30

# Worker timeout
worker_tmp_dir = '/dev/shm'  # Use shared memory for worker temp files (faster)

# StatsD integration (optional)
# statsd_host = 'localhost:8125'
# statsd_prefix = 'docsai'
