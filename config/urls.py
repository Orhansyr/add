
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from site_ayarları.sitemaps import NewsSitemap, CategorySitemap
from django.views.decorators.cache import cache_page






def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    rss_url = request.build_absolute_uri('/rss/')
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /search/",
        "Disallow: /accounts/",
        "Allow: /static/",
        "Allow: /media/",
        f"Sitemap: {sitemap_url}",
        f"RSS: {rss_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

sitemaps = {
    'news': NewsSitemap,
    'categories': CategorySitemap,
         }



urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', cache_page(60 * 60 * 24)(sitemap), {'sitemaps': sitemaps}),
    path("robots.txt", robots_txt),
    path('', include('site_ayarları.urls')),
    path('', include('pages.urls', namespace='pages'), name='pages'),
    path('tinymce/', include('tinymce.urls')),
    
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

