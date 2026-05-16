from django.apps import AppConfig


class ActivityConfig(AppConfig):
    name = 'activity'
    def ready(self):
        # import signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
