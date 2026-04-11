
# RSS beslemesi için gerekli sınıflar ve yapılandırmalar
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Rss201rev2Feed
from django.template.defaultfilters import truncatewords
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils import timezone
from typing import cast

from pages.models import Category, News
from site_ayarları.models import SiteSettings

# Google News uyumlu RSS beslemesi oluşturmak için özel bir feed generator sınıfı
class GoogleNewsRssFeedGenerator(Rss201rev2Feed):
    def rss_attributes(self):
        attrs = super().rss_attributes()  # type: ignore[attr-defined]
        attrs["xmlns:media"] = "http://search.yahoo.com/mrss/"
        return attrs

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        media_content_url = item.get("media_content_url")
        if media_content_url:
            handler.addQuickElement(  # type: ignore[attr-defined]
                "media:content",
                "",
                {"url": media_content_url, "medium": "image"},
            )
# RSS beslemesi için haber(news) beslemesigerekli site adı, açıklama, haberler ve diğer bilgileri sağlayan sınıflar
class LatestNewsFeed(Feed):
    feed_type = GoogleNewsRssFeedGenerator
    link = "/rss/"

    def get_feed(self, obj, request):
        self._request = request
        return super().get_feed(obj, request)

    def title(self):
        settings_obj = SiteSettings.objects.first()
        if settings_obj and settings_obj.site_name:
            return f"{settings_obj.site_name} - RSS"
        return "Haberler - RSS"

    def description(self):
        settings_obj = SiteSettings.objects.first()
        if settings_obj and settings_obj.description:
            return Truncator(strip_tags(settings_obj.description)).chars(200)
        return "Sitemizde yayinlanan guncel haberler."

    def items(self):
        return (
            News.objects.filter(is_active=True)
            .select_related("category", "author")
            .prefetch_related("images")
            .order_by("-published_date")[:10]
        )
# RSS içindeki her haber için açıklama alanını üretir.
    def item_description(self, item):
        news = cast(News, item)
        plain_text = strip_tags(news.content or "")
        return truncatewords(plain_text, 28)
    
# RSS içindeki her haber için link alanını üretir.
    def item_link(self, item):
        news = cast(News, item)
        return news.get_absolute_url()
    
#RSS item’ı için benzersiz kimlik verir (guid).
#Aynı haberin tekrar mı yeni mi olduğunu feed okuyucular bu değerle #takip eder.
    def item_guid(self, item):
        news = cast(News, item)
        return news.get_absolute_url()

    def item_guid_is_permalink(self, item):
        return True

    def item_pubdate(self, item):
        news = cast(News, item)
        return news.published_date
    
# RSS item’ına medya içeriği (örneğin haber resmi) eklemek için özel bir alan sağlar.görsel URL’ini döndürür.
    def item_extra_kwargs(self, item):
        news = cast(News, item)
        image_url = None
        first_image = news.images.all().first()  # type: ignore[attr-defined]
        request = getattr(self, "_request", None)
        if first_image and first_image.image:
            if request is not None:
                image_url = request.build_absolute_uri(first_image.image.url)
            else:
                image_url = first_image.image.url
        return {"media_content_url": image_url}

    def item_author_name(self, item):
        news = cast(News, item)
        if news.author and news.author.name:
            return news.author.name
        return "Editor"

    def item_categories(self, item):
        news = cast(News, item)
        if news.category and news.category.name:
            return [news.category.name]
        return []


# Kategori(başlık,menü) özel RSS beslemesi - 
class CategoryNewsFeed(LatestNewsFeed):
    def get_object(self, request, slug=None):  # type: ignore[override]
        if slug:
            return get_object_or_404(Category, slug=slug)
        return None

    def title(self, obj):  # type: ignore[override]
        settings_obj = SiteSettings.objects.first()
        site_name = settings_obj.site_name if settings_obj and settings_obj.site_name else "Haberler"
        if obj is None:
            return f"{site_name} - Kategoriler RSS"
        return f"{site_name} - {obj.name} RSS"

    def description(self, obj):  # type: ignore[override]
        if obj is None:
            return "Sitedeki tum kategorilerin RSS listesi."
        return f"{obj.name} kategorisindeki guncel haberler."

    def link(self, obj):  # type: ignore[override]
        if obj is None:
            return "/rss/kategori/"
        return f"/rss/kategori/{obj.slug}/"
   
   # Kategori listesi istendiyse kategorileri, kategori secildiyse haberleri dondurur.
    def items(self, obj):  # type: ignore[override]
        if obj is None:
            return Category.objects.order_by("order", "name")
        return (
            News.objects.filter(is_active=True, category=obj)
            .select_related("category", "author")
            .prefetch_related("images")
            .order_by("-published_date")[:10]
        )

    def item_description(self, item):
        if isinstance(item, Category):
            return f"{item.name} kategorisinin RSS yayini"
        return super().item_description(item)

    def item_link(self, item):
        if isinstance(item, Category):
            return f"/rss/kategori/{item.slug}/"
        return super().item_link(item)

    def item_guid(self, item):
        if isinstance(item, Category):
            return f"/rss/kategori/{item.slug}/"
        return super().item_guid(item)

    def item_pubdate(self, item):
        if isinstance(item, Category):
            return timezone.now()
        return super().item_pubdate(item)

    def item_extra_kwargs(self, item):
        if isinstance(item, Category):
            return {"media_content_url": None}
        return super().item_extra_kwargs(item)

    def item_author_name(self, item):
        if isinstance(item, Category):
            return ""
        return super().item_author_name(item)

    def item_categories(self, item):
        if isinstance(item, Category):
            return [item.name]
        return super().item_categories(item)
