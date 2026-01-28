"""
Development settings for docsai project.

These settings are used when DJANGO_ENV=development or when DEBUG=True
"""

from .base import *  # noqa

# Override base settings for development
DEBUG = True
ALLOWED_HOSTS = ['*']  # Allow all hosts in development

# Development-specific middleware (optional)
# Install with: pip install django-debug-toolbar django-extensions
try:
    import debug_toolbar  # noqa
    INSTALLED_APPS += ['debug_toolbar']  # noqa
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE  # noqa
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass  # Debug toolbar not installed

try:
    import django_extensions  # noqa
    INSTALLED_APPS += ['django_extensions']  # noqa
except ImportError:
    pass  # Django extensions not installed

# Email Backend (Console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging - more verbose in development
LOGGING['handlers']['console']['level'] = 'DEBUG'  # noqa
LOGGING['root']['level'] = 'DEBUG'  # noqa

# Session cookies not secure in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True
