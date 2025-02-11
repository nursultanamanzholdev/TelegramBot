# meabot/apps.py

from django.apps import AppConfig

class MeabotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meabot'
    # No calls to initialize(), no code in ready()
