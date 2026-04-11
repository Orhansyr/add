from django.db import models
from django.urls import reverse
from django.contrib import admin
from tinymce.models import HTMLField
from django.utils.html import format_html
from django.utils.text import slugify
from urllib.parse import urlparse, parse_qs
import re


# Yazar modeli
class Author(models.Model):
    name = models.CharField("Yazar Adı", max_length=100)
    slug = models.SlugField(
        unique=True,
    )
    image = models.ImageField(
        "Yazar Resmi", upload_to="author_images/", blank=True, null=True
    )
    bio = models.TextField("Biyografi", blank=True, null=True)
    facebook_url = models.URLField("Facebook URL", blank=True, null=True)
    twitter_url = models.URLField("Twitter URL", blank=True, null=True)
    linkedin_url = models.URLField("LinkedIn URL", blank=True, null=True)
    instagram_url = models.URLField("İnstagram URL", blank=True, null=True)


    def __str__(self):
        return self.name or "Bölge Gazetesi"  # Yazar adı boşsa varsayılan olarak "Bölge Gazetesi" döndür      
        

    class Meta:
        verbose_name = "Yazar"
        verbose_name_plural = "Yazarlar"

    def get_absolute_url(self):
        return reverse("pages:authors", args=[self.slug])

    @admin.display(description="Yazar Resmi")
    def image_tag(self):
        if self.image:
            return format_html(
                '<img src="{}" width="170" height="170" />', self.image.url
            )
        return "Görsel yok"


# Kategori modeli
class Category(models.Model):
    name = models.CharField("Kategori Adı", max_length=100)
    slug = models.SlugField(
        unique=True,
    )
    url = models.CharField(max_length=255, blank=True, null=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    order = models.PositiveIntegerField("Sıralama", default=0)  # Sıralama için

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"

    def __str__(self):
        prefix = f"{self.parent.name} > " if self.parent else ""
        return f"{prefix}{self.name}"

    # alt kategoriler için yardımcı özellikler
    @property
    def has_children(self) -> bool:
        return self.children.exists()  # type: ignore[attr-defined]

    def get_full_path(self):
        """
        Parent zincirine bakarak tam path oluşturur.
        Örn: /ana-menu/alt-menu-1/alt-menu-1-1/
        """
        parts = []
        current = self
        while current:
            parts.insert(0, slugify(current.name))
            current = current.parent
        return "/" + "/".join(parts) + "/"

    def save(self, *args, **kwargs):
        # Eğer url boşsa veya otomatik path oluşturmak istiyorsak
        self.url = self.get_full_path()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("pages:category_list", args=[self.slug])


# Haber modeli
class News(models.Model):
    name = models.CharField("başlık", max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="categories",verbose_name='kategori'
    )
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="authors", blank=True, null=True, verbose_name='yazar')
    slug = models.SlugField("slug", max_length=100, unique=True)
    content = HTMLField("içerik")
    published_date = models.DateTimeField(
        "yayımlanma tarihi", auto_now_add=True, editable=False
    )
    is_active = models.BooleanField("Haber Yayında", default=True)
    order = models.PositiveIntegerField(verbose_name="Haber Sırası", default=0)

    def __str__(self):
        return self.name or "Başlıksız Haber"

    class Meta:
        verbose_name = "Haber "
        verbose_name_plural = "Haberler"
        ordering = ["order", "-published_date"]

    def get_absolute_url(self):
        return reverse("pages:news_detail", args=[self.slug])


# HABER Resimleri modeli
class NewsImage(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("resim", upload_to="haber_resimleri/")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.news.name or "Başlıksız Haber Resmi"

    """
    def image_tag(self):
        if self.image:
            return format_html('<img src="{}" width="170" height="170" />', self.image.url)
        return "No Image" 
    image_tag.short_description = 'Resim Önizlemesi' # type: ignore
    """

    @admin.display(description="Resim Önizlemesi")
    def image_tag(self):
        if self.image:
            return format_html(
                '<img src="{}" width="170" height="170" />', self.image.url
            )
        return "Görsel yok"

    class Meta:
        ordering = ["order"]
        verbose_name = "Haber Resmi"
        verbose_name_plural = "Haber Resimleri"


#  - HABER VİDEOLARI MODELİ ------------------------------------
class NewsVideo(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="videos")
    name = models.CharField("video adı", max_length=200, blank=True, null=True)
    video_file = models.FileField(upload_to="news_videos/", blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.news.name or "Başlıksız Haber Videosu"

    def _safe_video_file_url(self):
        try:
            return self.video_file.url if self.video_file else ""
        except ValueError:
            return ""

    def _get_youtube_video_id(self):
        url = (self.youtube_url or "").strip()
        if not url:
            return ""

        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""

        if "youtu.be" in host:
            return path.strip("/").split("/")[0]
        if "youtube.com" in host:
            if path == "/watch":
                return parse_qs(parsed.query).get("v", [""])[0]
            if path.startswith("/shorts/"):
                return path.split("/shorts/", 1)[1].split("/")[0]
            if path.startswith("/embed/"):
                return path.split("/embed/", 1)[1].split("/")[0]
            if path.startswith("/live/"):
                return path.split("/live/", 1)[1].split("/")[0]
            if path.startswith("/v/"):
                return path.split("/v/", 1)[1].split("/")[0]

        # Last-resort parser for uncommon but valid YouTube URL variants.
        match = re.search(r"(?:v=|/)([A-Za-z0-9_-]{11})(?:[?&/]|$)", url)
        if match:
            return match.group(1)
        return ""

    # site içinde gömülü oynatma için embed URL'si oluşturur(index.html'deki "tüm haberler" ve "video haberler" kısmında kullanılıyor)
    def get_embed_url(self):
        url = (self.youtube_url or "").strip()
        if not url:
            return self._safe_video_file_url()

        video_id = self._get_youtube_video_id()

        return f"https://www.youtube.com/embed/{video_id}" if video_id else url

    # YouTube’a yönlendirme için normal URL'si oluşturur
    # sadece index.html'deki Video Haberler bölümündeki YouTube butonunda kullanılıyor
    def get_watch_url(self):
        url = (self.youtube_url or "").strip()
        if not url:
            return ""

        video_id = self._get_youtube_video_id()
        return f"https://www.youtube.com/watch?v={video_id}" if video_id else url

    @admin.display(description=" Video Önizlemesi")
    def video_tag(self):
        file_url = self._safe_video_file_url()

        if file_url:
            return format_html(
                '<video width="170" height="170" controls><source src="{}" type="video/mp4"></video>',
                file_url,
            )

        elif self.youtube_url:
            return format_html(
                '<iframe width="170" height="170" src="{}" frameborder="0" allowfullscreen></iframe>',
                self.get_embed_url(),
            )
        else:
            return "Görsel yok"
        

    class Meta:
        ordering = ["order"]
        verbose_name = "Haber Videosu"
        verbose_name_plural = "Haber Videoları"
