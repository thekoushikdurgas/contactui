from django.apps import AppConfig


class DurgasflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.durgasflow'
    verbose_name = 'Durgasflow Workflow Automation'

    def ready(self):
        # Import signals if needed
        pass
