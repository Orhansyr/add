"""Haber içeriğini bölmek için özel template filtreleri."""

from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe
import re
from pages.models import News

register = template.Library()

# Bu özel template tag, belirli bir kategoriye ait aktif haberleri döndürür. news_detail.html'deki sidebar daki "tab bölümü haberler " bölümünde kullanılır.
@register.simple_tag
def get_tab_news(category_slug, current_slug=None, limit=6):
    """Return latest active news for a given category slug for sidebar tabs."""
    qs = (
        News.objects.filter(is_active=True, category__slug__iexact=category_slug)
        .select_related("category")
        .prefetch_related("images")
        .annotate(
            image_count=Count("images", distinct=True),
            video_count=Count("videos", distinct=True),
        )
        .exclude(image_count=0, video_count__gt=0)
        .order_by("-published_date")
    )
    if current_slug:
        qs = qs.exclude(slug=current_slug)# mevcut haberin slug'ını dışarıda bırakır, böylece aynı haber hem içerikte hem de "son haberler" bölümünde görünmez.
    return qs[:limit]



# Bu özel template tag, en son aktif haberleri döndürür. news_detail.html'deki "son haberler" bölümünde kullanılır. 
# @register.simple_tag
# def get_latest_news(limit=4, current_slug=None, hide_video_only=False):
#     """Return latest active news for simple sidebar/widget usage."""
#     qs = (
#         News.objects.filter(is_active=True)
#         .select_related("category")
#         .prefetch_related("images")
#         .order_by("-published_date")
#     )
#
#     hide_video_only_flag = str(hide_video_only).lower() in {"1", "true", "yes", "on"}
#     if hide_video_only_flag:
#         qs = qs.annotate(
#             image_count=Count("images", distinct=True),
#             video_count=Count("videos", distinct=True),
#         ).exclude(image_count=0, video_count__gt=0)
#
#     if current_slug:
#         qs = qs.exclude(slug=current_slug)
#     return qs[:limit]


# üstteki için-- widget olarak kullanmak için inclusion_tag olarak tanımlanır. news_detail.html'deki "son haberler" bölümünde {% get_latest_news 4 news.slug True as latest_news %} şeklinde kullanılır. hide_video_only parametresi, sadece video içeren haberleri gizlemek için kullanılır.
@register.inclusion_tag("partials/latest_news_widget.html")
def latest_news_widget(limit=4, current_slug=None, hide_video_only=False, title="Son Haberler"):
    """Render latest news widget directly from template."""
    qs = (
        News.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .order_by("-published_date")
    )

    hide_video_only_flag = str(hide_video_only).lower() in {"1", "true", "yes", "on"}
    if hide_video_only_flag:
        qs = qs.annotate(
            image_count=Count("images", distinct=True),
            video_count=Count("videos", distinct=True),
        ).exclude(image_count=0, video_count__gt=0)

    if current_slug:
        qs = qs.exclude(slug=current_slug)

    return {
        "widget_title": title,
        "latest_news": qs[:limit],
    }



# Haber içeriğini kelime sayısına göre iki parçaya bölen yardımcı fonksiyon content_first ve content_after filtrelerinde kullanılır. news_detail.html'de 
def _split_html_by_words(html_content, word_count):
    """
    HTML içeriği kelime sayısına göre ikiye böler.
    HTML etiketlerini korur, kırılmayı engeller.
    """
    if not html_content:
        return "", ""

    text = str(html_content)
    # HTML etiketleri ve kelimeler ayrı ayrı tokenize edilir
    tokens = re.findall(r"(<[^>]+>|[^\s<]+)", text)

    words_seen = 0
    split_index = len(tokens)  # varsayılan: tamamı ilk parça

    for i, token in enumerate(tokens):
        if not token.startswith("<"):  # HTML etiketi değilse kelimedir
            words_seen += 1
            if words_seen >= word_count:
                split_index = i + 1
                break

    first_part = " ".join(tokens[:split_index])
    second_part = " ".join(tokens[split_index:])

    return first_part, second_part


@register.filter(name="content_first")
def content_first(value, word_count=25):
    """İçeriğin ilk N kelimesini döndürür (HTML korunur)."""
    first, _ = _split_html_by_words(value, int(word_count))
    return mark_safe(first)


@register.filter(name="content_after")
def content_after(value, word_count=25):
    """İçeriğin ilk N kelimesinden sonrasını döndürür (HTML korunur)."""
    _, second = _split_html_by_words(value, int(word_count))
    return mark_safe(second)
