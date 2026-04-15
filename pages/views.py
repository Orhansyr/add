from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import News, Category, Author, NewsVideo
from django.views.decorators.cache import cache_page
#import feedparser

# Anasayfa için view fonksiyonu
@cache_page(60 * 60 * 24)  # Anasayfa içeriğini 24 saat cache'ler
def home(request):
    news = (
        News.objects.filter(is_active=True)
        .order_by("-published_date")[:10]
        .select_related("category", "author")
        .prefetch_related("images")
    )
    videos = (
        NewsVideo.objects.filter(news__is_active=True)
        .select_related("news", "news__category")
        .prefetch_related("news__images")
    )

    context = {"news": news, "videos": videos}
    return render(request, "index.html", context)
   



# Haber detay sayfası için view fonksiyonu
@cache_page(60 * 60 * 24)  # Haber detay sayfasını 24 saat cache'ler
def news_detail(request, slug):
    #print(f"%%% news_detail view calisti %%%% : {slug}")
    news = (
        News.objects.all()
        .select_related("category", "author")
        .prefetch_related("images", "videos")
        .filter(slug=slug, is_active=True)
        .first()
    )
    if not news:
        raise Http404("Haber bulunamadı.")

    # Yüklenme sırasını id alanı ile takip ederek bir önceki ve bir sonraki haberi bulur.
    prev_news = (
        News.objects.filter(is_active=True, pk__lt=news.pk)
        .order_by("-pk")
        .first()
    )
    next_news = (
        News.objects.filter(is_active=True, pk__gt=news.pk)
        .order_by("pk")
        .first()
    )

    benzer_haberler = (
        News.objects.filter(is_active=True)
        .exclude(slug=slug)
        .order_by("-published_date")[:6]
    )  # benzer haberler için aynı kategorideki diğer haberleri getirir, exclude ile şu anki haberi hariç tutar, order_by ile yayınlanma tarihine göre sıralar ve [:6] ile sadece 6 tanesini alır

    context = {
        "news": news,
        "benzer_haberler": benzer_haberler,
        "prev_news": prev_news,
        "next_news": next_news,
       
    }
    return render(request, "news_detail.html", context)



# Kategori sayfası için view fonksiyonu
@cache_page(60 * 60 * 24)  # Kategori sayfasını 24 saat cache'ler
def category_list(request, slug):
    """View: show news for a given category slug."""
    category = get_object_or_404(Category, slug=slug)
    items = (
        News.objects.filter(category=category, is_active=True)
        .select_related("author", "category")
        .prefetch_related("images", "videos")
        .order_by("-published_date")
    )
    # items kategorideki  haberleri getirir, select_related ile author bilgilerini tek sorguda getirir, prefetch_related ile de haberin resimlerini tek sorguda getirir
    context = {"category": category, "items": items}
    return render(request, "category_list.html", context)


# Yazar sayfası için view fonksiyonu
@cache_page(60 * 60 * 24)  # Yazar sayfasını 24 saat cache'ler
def authors(request, slug):
    author = get_object_or_404(Author, slug=slug)
    news_list = (
        News.objects.filter(author=author, is_active=True)
        .select_related("category")
        .prefetch_related("images")
    )

    context = {"author": author, "news_list": news_list}
    return render(request, "authors.html", context)



def search(request):
    from django.db.models import Q
    query = request.GET.get("q", "")
    results = []
    if query:
        results = (
            News.objects.filter(Q(name__icontains=query) | Q(content__icontains=query), is_active=True)
            .select_related("category", "author")
            .prefetch_related("images")
            .order_by("-published_date")
    )
    context = {"query": query, "results": results}
    return render(request, "search.html", context)



