# backend/api/apps.py
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        import api.signals # If you have signals
        # You can also initialize things here if needed when Django starts
        # (but heavy initializations are better in specific modules or management commands)
        pass
