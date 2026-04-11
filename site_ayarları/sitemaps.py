from django.contrib.sitemaps import Sitemap
from pages.models import News, Category

class NewsSitemap(Sitemap):
    changefreq = "hourly" # Haberler sık güncellenir
    priority = 0.9        # Haberler önceliklidir

    def items(self):
        return News.objects.filter(is_active=True).order_by('-published_date')[:100] # Son 100 aktif haber

    def lastmod(self, obj):
        return obj.published_date # Veya updated_at alanınız varsa o

class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Category.objects.all()