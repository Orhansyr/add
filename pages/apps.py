from django.apps import AppConfig


class PagesConfig(AppConfig):
    name = "pages"
    verbose_name = "Haberler ve Resimler"

    def ready(self):
        import pages.signals
