"""API gateway app configuration."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration for API gateway app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
    verbose_name = 'API Gateway'
