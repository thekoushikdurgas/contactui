"""
WSGI entry point for Gunicorn (production).

Re-exports the Django WSGI application from docsai.wsgi so that
`gunicorn config.wsgi:application` works. Django settings are loaded
via config.settings (controlled by DJANGO_ENV).
"""

from docsai.wsgi import application

__all__ = ["application"]
