"""
Testing settings for docsai project.

These settings are used when running tests (DJANGO_ENV=testing or pytest)
"""

from .base import *  # noqa

# Override base settings for testing
DEBUG = False

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations during tests (optional - can speed up tests)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()

# Password hashing - use faster hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend - use locmem for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Cache - use dummy cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# CORS - allow all in tests
CORS_ALLOW_ALL_ORIGINS = True

# Disable SuperAdmin-only enforcement so view tests don't require external auth
SUPER_ADMIN_ONLY_ENABLED = False

# Use only ModelBackend in tests so force_login() works (Appointment360Backend.get_user returns None)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
