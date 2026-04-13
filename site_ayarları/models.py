from django.db import models
from django.utils.html import format_html
from django.contrib import admin


       

class SiteSettings(models.Model):
    site_name = models.CharField("Site adı",max_length=150, default="Benim Sitem")
    site_slogan = models.CharField("Slogan",max_length=250, blank=True, null=True)
    description = models.TextField("Site Açıklaması", blank=True, null=True)
    keywords = models.CharField("Anahtar Kelimeler", max_length=250, blank=True, null=True)
    google_analytics_id = models.CharField("Google Analytics ID", max_length=50, blank=True, null=True)
    google_search_console_code = models.CharField("Google Search Console Doğrulama Kodu", max_length=100, blank=True, null=True)
    google_adsense_client_id = models.CharField("Google AdSense Client ID", max_length=50, blank=True, null=True)
    # Medya
    logo = models.ImageField(upload_to="site/logo/", blank=True, null=True)
    favicon = models.ImageField(upload_to="site/favicon/", blank=True, null=True)


    # İletişim bilgileri
    whatsapp_number = models.CharField("WhatsApp Numarası", max_length=20, blank=True, null=True)   
    phone = models.CharField("Telefon", max_length=50, blank=True, null=True)
    phone2 = models.CharField("Telefon-2", max_length=50, blank=True, null=True)
    email = models.EmailField("E-posta", blank=True, null=True)
    email2 = models.EmailField("E-posta-2", blank=True, null=True)
    address = models.TextField("Adres", blank=True, null=True)

    

    # Sosyal medya
    facebook = models.URLField("Facebook", blank=True, null=True )
    instagram = models.URLField("Instagram", blank=True, null=True  )
    twitter = models.URLField("Twitter", blank=True, null=True )
    linkedin = models.URLField("LinkedIn", blank=True, null=True )
    youtube = models.URLField("YouTube", blank=True, null=True )
    rss = models.URLField("RSS", blank=True, null=True)

    # Harita iframe kodu
    google_map_iframe = models.TextField("Google Maps Embed Kodu", blank=True, null=True)

    def __str__(self):
        return self.site_name

    class Meta:
        verbose_name = "Site Ayarı"
        verbose_name_plural = "Site Ayarları"

     




# Reklam resimleri modeli
class Reklam(models.Model):
    reklamlar = [
        ("Seciniz", " Reklam Alanı Seçiniz"),
        ("banner", "Banner Reklam"),
        ("haber_detay", "Haber Detay Sayfası"),
        ("yazar_detay", "Yazar Detay Sayfası"),
        
    ]

    name = models.ForeignKey(SiteSettings, on_delete=models.CASCADE, related_name="reklamlar",null=True, blank=True)
    position = models.CharField("Reklam Yeri", max_length=50, choices=reklamlar, default="Seciniz")
    image = models.ImageField("Reklam Görseli", upload_to="Reklamlar/", blank=True, null=True)
    url = models.URLField("Reklam Linki", help_text="Reklama tıklandığında gidilecek URL",blank=True, null=True )
    is_active = models.BooleanField("Aktif", default=True)

    def __str__(self):
        return self.position or (self.name.site_name if self.name else "")


    @admin.display(description="Reklam Görseli")
    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" style="max-height:60px;" />', self.image.url)
        return "Görsel yok"

# RSS Feed  modeli (SİGNALS ile cache temizlencek)
class RSSFeedSource(models.Model):
    title = models.CharField("Baslik", max_length=120)
    feed_url = models.URLField("RSS Feed URL", unique=True)
    is_active = models.BooleanField("Aktif", default=True)
    order = models.PositiveIntegerField("Sira", default=0)
    item_limit = models.PositiveSmallIntegerField("Kayit Limiti", default=5)

    class Meta:
        verbose_name = "Icerik Bolumu (RSS)"
        verbose_name_plural = "Icerik Bolumleri (RSS)"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title
