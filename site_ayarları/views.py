from django.shortcuts import render

def borsa(request):
    return render(request, "borsa.html")

def eczane(request):
    return render(request, "eczane.html")