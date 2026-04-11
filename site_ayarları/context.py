
import json
import re
import xml.etree.ElementTree as ET
from django.core.cache import cache
from site_ayarları.models import SiteSettings
from pages.models import Category, News, NewsImage
import requests




def menu(request):
    menus = Category.objects.filter(parent__isnull=True).prefetch_related("children")
    
    return {"menus": menus}
            


# Site ayarlarını önbelleğe alarak tüm şablonlarda kullanılabilir hale getirir
def site_settings(request):
    settings_obj = cache.get("site_settings")
    if settings_obj is None:
        settings_obj = SiteSettings.objects.first()
        cache.set("site_settings", settings_obj, 60 * 60 * 12)  # 12 saat boyunca önbellekte tut

    ad_haber_detay = None # haber detay sayfası için reklam
    ad_yazar_detay = None #yazar sayfası için reklam
    if settings_obj:
        ad_haber_detay = settings_obj.reklamlar.filter(position="haber_detay", is_active=True).first() # type: ignore
        ad_yazar_detay = settings_obj.reklamlar.filter(position="yazar_detay", is_active=True).first() # type: ignore
        
    return {
        "site_settings": settings_obj,
        "ad_haber_detay": ad_haber_detay,
        "ad_yazar_detay": ad_yazar_detay,
       
    }



# Kategorileri önbelleğe alarak tüm şablonlarda MENÜ olarak kullanılabilir hale getirir
def site_categories(request):
    categories = cache.get("categories")
    if not categories:
        categories = Category.objects.all()
        cache.set("categories", categories, 60 * 60 * 12)  # 12 saat boyunca önbellekte tut
    return {'categories': categories}




# (google yandex SEO için) global meta tags ve yapılandırılmış veri (structured data) sağlamak için context processor   
def site_structured_data(request):
    settings = cache.get('site_settings')
    categories = cache.get('site_categories')
    news = cache.get('news_cache')

    if not news:
        news= News.objects.filter(is_active=True).order_by('-published_date')[:10]
        cache.set('news_cache', news, 60*60*12) # 12 saat


    if not settings:
        settings = SiteSettings.objects.first()
        cache.set('site_settings', settings, timeout=60 * 60 * 24 * 3)  # 3 gün

    if not categories:
        categories = Category.objects.all()
        cache.set('site_categories', categories, timeout=60 * 60 * 24 * 3)

    if not settings:
        return {}

    has_part = []
    for category in categories:
        has_part.append({
            "@type": "SiteNavigationElement",
            "name": category.name,
            "url": f"{request.scheme}://{request.get_host()}/{category.slug}/"
        })

    item_list = []
    for index, item in enumerate(news, start=1):
        item_list.append({
            "@type": "ListItem",
            "position": index,
            "url": f"{request.scheme}://{request.get_host()}{item.get_absolute_url()}",
            "name": item.name,
        })

    structured_data = {
        "@context": "https://schema.org",
        "@type": "NewsMediaOrganization",
        "name": settings.site_name,
        "url": f"{request.scheme}://{request.get_host()}",
        "logo": settings.logo.url if settings.logo else None,
        "description": f"📢 {settings.description}" if settings.description else "📢 Guncel haberler ve son dakika gelismeleri.",
        "image": settings.favicon.url if settings.favicon else None,
        "hasPart": has_part,
        "itemListElement": item_list,
        
    }

    news_structured_data_json = None
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match and resolver_match.url_name == "news_detail":
        slug = resolver_match.kwargs.get("slug")
        if slug:
            news = (
                News.objects.filter(slug=slug, is_active=True)
                .select_related("category", "author")
                .prefetch_related("images")
                .first()
            )
            if news:
                news_url = request.build_absolute_uri(news.get_absolute_url())
                image_url = None
                first_image = NewsImage.objects.filter(news=news).order_by("order").first()
                if first_image and first_image.image:
                    image_url = request.build_absolute_uri(first_image.image.url)

                publisher = {
                    "@type": "Organization",
                    "name": settings.site_name if settings.site_name else request.get_host(),
                }
                if settings.logo:
                    publisher["logo"] = {
                        "@type": "ImageObject",
                        "url": request.build_absolute_uri(settings.logo.url),
                    }

                news_article_schema = {
                    "@context": "https://schema.org",
                    "@type": "NewsArticle",
                    "headline": f"📰 {news.name}",
                    "mainEntityOfPage": {
                        "@type": "WebPage",
                        "@id": news_url,
                    },
                    "datePublished": news.published_date.isoformat(),
                    "dateModified": news.published_date.isoformat(),
                    "author": {
                        "@type": "Person",
                        "name": news.author.name if news.author and news.author.name else "Editor",
                    },
                    "publisher": publisher,
                    "articleSection": news.category.name if news.category else "Genel",
                    "url": news_url,
                }

                if image_url:
                    news_article_schema["image"] = [image_url]

                if settings.description:
                    news_article_schema["description"] = settings.description

                news_structured_data_json = json.dumps(news_article_schema, ensure_ascii=False)

    return {
        "site_structured_data": structured_data,
        "site_structured_data_json": json.dumps(structured_data, ensure_ascii=False),
        "news_structured_data_json": news_structured_data_json,
    }






# TCMB verilerini header ticker'ında göstermek için context processor. Veriler öncelikle TCMB'nin gunluk XML kaynagindan çekilir, eksik veya bulunamayan veriler için TradingView API'si fallback olarak kullanılır. Sonuçlar 30 dakika boyunca önbellekte tutulur. 
def _safe_float(value):
    if value is None:
        return None
    cleaned = str(value).strip().replace(',', '.')
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _format_number(value, digits=4):
    if value is None:
        return None
    text = f"{value:.{digits}f}"
    return text.replace('.', ',')


def _tv_scan_value(endpoint, symbol, columns):
    payload = {
        "symbols": {"tickers": [symbol], "query": {"types": []}},
        "columns": columns,
    }
    response = requests.post(
        f"https://scanner.tradingview.com/{endpoint}/scan",
        json=payload,
        timeout=8,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    data = response.json().get("data") or []
    if not data:
        return None
    values = data[0].get("d") or []
    if not values:
        return None
    return _safe_float(values[0])


def _extract_tcmb_rates():
    """TCMB gunluk XML kaynagindan USD, EUR ve XAU (ons) verilerini ceker."""
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    response = requests.get(url, timeout=8)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    wanted_codes = {"USD": "ABD Doları", "EUR": "Euro", "XAU": "Altın Ons"}
    parsed = {}

    for currency in root.findall("Currency"):
        code = (currency.attrib.get("CurrencyCode") or "").upper()
        if code not in wanted_codes:
            continue

        # XAU icin Forex* alanlari bos olabilir; CrossRateUSD kullanilir.
        raw_value = (
            currency.findtext("ForexSelling")
            or currency.findtext("ForexBuying")
            or currency.findtext("BanknoteSelling")
            or currency.findtext("BanknoteBuying")
            or currency.findtext("CrossRateUSD")
            or currency.findtext("CrossRateOther")
        )
        parsed[code] = _safe_float(raw_value)

    items = []
    for code in ("USD", "EUR", "XAU"):
        value = parsed.get(code)
        if value is not None:
            unit = "USD" if code == "XAU" else "TL"
            items.append({
                "code": code,
                "label": wanted_codes[code],
                "value": f"{_format_number(value, digits=4)} {unit}",
                "source": "TCMB",
            })
    return items


def _extract_optional_tcmb_indicators():
    """TCMB sayfalarinda bulunursa Politika Faizi ve BIST100 metriklerini yakalamayi dener."""
    optional_items = []
    search_urls = [
        "https://www.tcmb.gov.tr",
        "https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/Main+Menu/Temel+Faaliyetler/Para+Politikasi",
    ]

    policy_regex = re.compile(r"Politika\s*Faizi[^\d%]*(\d+[\.,]?\d*)\s*%", re.IGNORECASE)
    bist_regex = re.compile(r"BIST\s*100[^\d]*(\d{3,6}(?:[\.,]\d+)?)", re.IGNORECASE)

    for url in search_urls:
        try:
            response = requests.get(url, timeout=6)
            response.raise_for_status()
            text = response.text

            if not any(item.get("code") == "POLICY" for item in optional_items):
                policy_match = policy_regex.search(text)
                if policy_match:
                    optional_items.append({
                        "code": "POLICY",
                        "label": "Politika Faizi",
                        "value": f"{policy_match.group(1).replace('.', ',')}%",
                        "source": "TCMB",
                    })

            if not any(item.get("code") == "BIST100" for item in optional_items):
                bist_match = bist_regex.search(text)
                if bist_match:
                    optional_items.append({
                        "code": "BIST100",
                        "label": "BIST 100",
                        "value": bist_match.group(1).replace('.', ','),
                        "source": "TCMB",
                    })

            if len(optional_items) >= 2:
                break
        except Exception:
            continue

    return optional_items


def _extract_market_fallbacks(existing_codes):
    """TCMB kaynaginda bulunmayan XAU/BIST verilerini fallback olarak tamamlar."""
    items = []

    if "XAU" not in existing_codes:
        try:
            xau_value = _tv_scan_value("global", "OANDA:XAUUSD", ["close"])
            if xau_value is not None:
                items.append({
                    "code": "XAU",
                    "label": "Altın Ons",
                    "value": f"{_format_number(xau_value, digits=4)} USD",
                    "source": "TradingView",
                })
        except Exception:
            pass

    if "BIST100" not in existing_codes:
        try:
            bist_value = _tv_scan_value("turkey", "BIST:XU100", ["close"])
            if bist_value is not None:
                items.append({
                    "code": "BIST100",
                    "label": "BIST 100",
                    "value": f"{_format_number(bist_value, digits=2)}",
                    "source": "TradingView",
                })
        except Exception:
            pass

    return items


def tcmb_piyasa_verileri(request):
    """Header ticker icin TCMB kaynakli piyasa verilerini saglar."""
    cache_key = "tcmb_ticker_items"
    cached = cache.get(cache_key)
    if cached is not None:
        return {"tcmb_ticker_items": cached}

    items = []
    try:
        items.extend(_extract_tcmb_rates())
    except Exception:
        items = []

    # Politik faiz ve BIST100 sadece TCMB sayfasinda bulunursa eklenir.
    try:
        items.extend(_extract_optional_tcmb_indicators())
    except Exception:
        pass

    existing_codes = {item.get("code") for item in items}
    items.extend(_extract_market_fallbacks(existing_codes))

    # Gosterim sirasini sabitle.
    order = {"USD": 1, "EUR": 2, "XAU": 3, "POLICY": 4, "BIST100": 5}
    items.sort(key=lambda x: order.get(x.get("code"), 99))

    # Gecici hata durumunda cok uzun cache tutma.
    cache.set(cache_key, items, 60 * 30)
    return {"tcmb_ticker_items": items}

#  TCMB verilerini header ticker'ında göstermek için context processor.
########################################################################
 

# Borsadaki (BIST) belirli hisse senetlerinin anlık verilerini çeken context processor. Bu fonksiyon her sayfada verilerin (borsa.html içinde) ulaşılabilir olmasını sağlar. Öğrenme Amacıyla Detaylı Yorumlanmıştır:
def borsa_hisse_verileri(request):
  
    
    # 1. Önbellekte (Cache) veri var mı kontrol ediyoruz.
    # Her sayfa yüklendiğinde sürekli API'ye istek atmamak ve siteyi yavaşlatmamak için cache kullanıyoruz.
    # Cache anahtarına versiyon ekliyoruz.
    # Boylece onceki yapidan kalan eksik/yanlis cache verisi varsa yeni veriyle karismaz.
    cache_key = "borsa_hisse_verileri_v2"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        # Eğer veri daha önce çekilmiş ve süresi dolmamışsa direkt onu döndürüyoruz.
        return {"borsa_hisse_listesi": cached_data}

    # 2. Borsa İstanbul'daki tum hisse senetlerini çekiyoruz.
    # TradingView Scanner API'de 'markets: ["turkey"]' ve 'types: ["stock"]' dediğimizde
    # Türkiye pazarındaki hisse senedi enstrümanları listelenir.
    # 'columns' alanı ise her kayıt için hangi verileri istediğimizi belirler.
    payload = {
        "filter": [
            {
                "left": "market_cap_basic",
                "operation": "nempty",
            }
        ],
        "options": {"lang": "tr"},
        "markets": ["turkey"],
        "symbols": {"query": {"types": ["stock"]}, "tickers": []},
        "columns": ["name", "description", "close", "change", "volume"],
    }

    hisse_listesi = []

    try:
        # 3. HTTP POST isteği ile verileri çekiyoruz.
        # scanner.tradingview.com adresindeki Türkiye (turkey) pazarı taranıyor.
        url = "https://scanner.tradingview.com/turkey/scan"
        # User-Agent başlığı ekleyerek bot engellemelerini geçmek hedeflenir.
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # requests.post() ile isteği atıyoruz; json parametresi Python sözlüğünü otomatik olarak JSON'a çevirir.
        response = requests.post(url, json=payload, headers=headers, timeout=8)
        
        # Eğer bağlanamazsak veya 404/500 tarzı hata dönerse exception fırlatır, try-except blogu yakalar.
        response.raise_for_status()
        
        # 4. Gelen JSON formatındaki API yanıtını ayıklıyoruz.
        json_resp = response.json()
        
        # Veriler 'data' listesi altında gelir; her bir hisse için 'd' listesi,
        # payload içinde yazdığımız sutunlarla aynı sırada verileri taşır.
        data_list = json_resp.get("data", [])
        
        for item in data_list:
            # item["d"] sırasıyla [name, description, close, change, volume] verileridir.
            sutun_degerleri = item.get("d", [])
            
            if len(sutun_degerleri) >= 5:
                # İlgili değerleri kendi değişkenlerimize alıyoruz.
                sembol = (sutun_degerleri[0] or "").strip()

                # Bazi kayitlarda description bos gelebilir.
                # Bu durumda kullanicinin ekranda bos alan gormemesi icin sembolu da fallback olarak kullaniyoruz.
                sirket_adi = (sutun_degerleri[1] or "").strip() or sembol or "Bilinmeyen Sirket"
                son_fiyat = _safe_float(sutun_degerleri[2]) or 0.0
                degisim = _safe_float(sutun_degerleri[3]) or 0.0
                hacim = _safe_float(sutun_degerleri[4])
                
                # Değişimin yönüne göre CSS sınıfı ekliyoruz ki yeşil(artış), kırmızı(düşüş)
                # veya nötr (sıfıra yakın hareket) şeklinde gösterilebilsin.
                if degisim > 0:
                    durum_class = "text-success"
                elif degisim < 0:
                    durum_class = "text-danger"
                else:
                    durum_class = "text-muted"
                
                # HTML'de kullanılacak alanları hazırlıyoruz.
                # 'siralama_anahtari' sayesinde veriyi A'dan Z'ye Python tarafında sıralayabiliyoruz.
                hisse_listesi.append({
                    "sembol": sembol,
                    "sirket_adi": sirket_adi,
                    "gorunen_baslik": f"{sembol} - {sirket_adi}",
                    "fiyat": f"{son_fiyat:.2f}".replace('.', ','),
                    "degisim": f"{degisim:.2f}".replace('.', ','),
                    "durum_class": durum_class,
                    "hacim": _format_number(hacim, digits=0) if hacim is not None else "-",
                    "siralama_anahtari": f"{sembol} {sirket_adi}".upper(),
                })

        # 5. Kullanıcının istediği gibi verileri A harfinden Z harfine sıralıyoruz.
        # Önce sembol, sonra şirket adı dikkate alınır; böylece sayfada düzenli bir liste görünür.
        hisse_listesi.sort(key=lambda hisse: hisse.get("siralama_anahtari", ""))

        # Şablonda gereksiz veri taşımamak için yalnızca sıralama bittikten sonra bu geçici alanı siliyoruz.
        for hisse in hisse_listesi:
            hisse.pop("siralama_anahtari", None)

    except Exception as e:
        # Eğer bir hata oluşursa (int. yok, API değişmiş) sistemin çökmemesi için hatayı yutuyoruz ve boş listeye devam ediyoruz.
        print(f"Hisse Senedi Çekme Hatası: {e}")

    # 6. Veriyi Önbelleğe Alma (Cache)
    # Kullanıcının istediği gibi veriyi 30 dakika boyunca saklıyoruz.
    # Böylece her sayfa isteğinde yeniden harici API çağrısı yapılmaz.
    cache.set(cache_key, hisse_listesi, 60 * 30)

    # 7. Django şablonlarında {{ borsa_hisse_listesi }} değişkenine aktarıyoruz.
    return {"borsa_hisse_listesi": hisse_listesi}


# ############################# ##############
# HAVA DURUMU API'sinden veriyi çekip header'da göstermek için context processor
def hava_durumu(request):
    api_key = '6ccf66b2e07949e4946171749260104'
    city = 'Bursa'  # Dinamik hale getirilebilir
    url = f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&lang=tr'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        weather_data = {
            'city': data['location']['name'],
            'temp': int(data['current']['temp_c']),
            'description': data['current']['condition']['text'],
            'icon': data['current']['condition']['icon'],
            'last_updated': data['current']['last_updated'],
        }
    except:
        weather_data = None

    return {"weather": weather_data}


# Geriye donuk uyumluluk: ayarlarda weather_for_bursa kullaniliyorsa ayni veriyi don.
def weather_for_bursa(request):
    return hava_durumu(request)