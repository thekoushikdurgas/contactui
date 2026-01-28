"""
Staging settings for docsai project.

These settings are used when DJANGO_ENV=staging
Staging is typically a pre-production environment for testing.
"""

from .base import *  # noqa

# Override base settings for staging
DEBUG = False  # Never debug in staging

# Staging-specific ALLOWED_HOSTS
# Override in environment variables for your staging domain
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'staging.example.com').split(',')

# Security settings (similar to production but may be relaxed for testing)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (shorter duration for staging)
SECURE_HSTS_SECONDS = 86400  # 1 day (shorter than production)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # Don't preload in staging

# Email Backend (SMTP for staging)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Logging - more verbose than production for debugging
LOGGING['handlers']['console']['level'] = 'INFO'  # noqa
LOGGING['root']['level'] = 'INFO'  # noqa

# CORS - restrict to staging frontend
CORS_ALLOW_ALL_ORIGINS = False
# Set CORS_ALLOWED_ORIGINS in environment variables

# Database connection pooling for staging
if DATABASE_ENGINE == 'postgresql':
    DATABASES['default']['CONN_MAX_AGE'] = 300  # noqa
    DATABASES['default']['ATOMIC_REQUESTS'] = True  # noqa
