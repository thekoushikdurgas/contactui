"""
Django settings package.

This module loads settings based on the DJANGO_SETTINGS_MODULE environment variable.
Default is 'config.settings.development' for local development.
"""

import os

# Determine which settings module to use
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development').lower()

if DJANGO_ENV == 'production':
    from .production import *  # noqa
elif DJANGO_ENV == 'staging':
    from .staging import *  # noqa
elif DJANGO_ENV == 'testing' or 'test' in DJANGO_ENV:
    from .testing import *  # noqa
else:
    from .development import *  # noqa
