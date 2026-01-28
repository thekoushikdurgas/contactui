"""Knowledge base app configuration."""
from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    """Knowledge base app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge'
    verbose_name = 'Knowledge Base'
