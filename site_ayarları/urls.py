from django.urls import path
from site_ayarları import views
from django.views.decorators.cache import cache_page
from .feeds import CategoryNewsFeed, LatestNewsFeed


urlpatterns = [
    path("rss/", cache_page(60 * 60)(LatestNewsFeed()), name="rss_feed"),
    path("borsa/",views.borsa , name="borsa"),

    
]
