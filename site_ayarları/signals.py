from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Reklam, SiteSettings


CACHE_KEYS_TO_CLEAR = [
    "site_settings",
    "categories",
    "site_categories",
    "news_cache",
    "top_10_news_schema",
]


def clear_common_context_cache():
    for key in CACHE_KEYS_TO_CLEAR:
        cache.delete(key)


@receiver(post_save, sender=SiteSettings)
@receiver(post_delete, sender=SiteSettings)
def clear_cache_on_site_settings_change(sender, **kwargs):
    clear_common_context_cache()


@receiver(post_save, sender=Reklam)
@receiver(post_delete, sender=Reklam)
def clear_cache_on_reklam_change(sender, **kwargs):
    clear_common_context_cache()
