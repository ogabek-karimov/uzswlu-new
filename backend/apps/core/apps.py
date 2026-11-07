from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'
    label = 'core'
    verbose_name = 'Umumiy'

    def ready(self):
        from . import checks, signals  # noqa: F401
