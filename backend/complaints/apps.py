# from django.apps import AppConfig
 
 
# class ComplaintsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'complaints'

from django.apps import AppConfig
import os


class ComplaintsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'complaints'

    def ready(self):
        # RUN_MAIN=true means we are in the actual worker process.
        # Without this check, scheduler starts twice due to Django's auto-reloader.
        if os.environ.get('RUN_MAIN') == 'true':
            try:
                from complaints.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                print(f"[Scheduler] Failed to start: {e}")