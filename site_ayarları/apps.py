from django.apps import AppConfig


class SiteAyarlarıConfig(AppConfig):
    name = 'site_ayarları'

    def ready(self):
        from . import signals  # noqa: F401
