from django.urls import path
from . import views

app_name = "pages"


urlpatterns = [
    path("", views.home, name="home"),
    path("kategori/<slug:slug>/", views.category_list, name="category_list"),
    path("haber/<slug:slug>/", views.news_detail, name="news_detail"),
    path("yazar/<slug:slug>/", views.authors, name="authors"),
    path("search/", views.search, name="news_search"),
    
]
