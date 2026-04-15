from django.shortcuts import render
from django.views.decorators.cache import cache_page


def borsa(request):
    return render(request, "borsa.html")
@cache_page(60 * 60 * 24)  # Cache for 24 hours
def eczane(request):
    return render(request, "eczane.html")

@cache_page(60 * 60 * 24)  # Cache for 24 hours
def page_not_found(request, exception):
    return render(request, "404.html", status=404)