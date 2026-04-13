from django.contrib import admin
import re
from .models import SiteSettings, Reklam, RSSFeedSource
from django.utils.html import format_html

admin.site.site_header = "Site Yönetim Paneli"
admin.site.site_title = "Haber Site Yönetim Paneli"
admin.site.index_title = "Hoşgeldiniz"

class ReklamInline(admin.TabularInline):
    model = Reklam
    extra = 2
    fields = ("position", "image", "image_tag", "url", "is_active")
    readonly_fields = ("image_tag",)



@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "phone", "email")
    readonly_fields = ("map_tag", "favicon_tag", "logo_tag")
    inlines= [ReklamInline]
    
   

    fieldsets = (
        ("Genel Bilgiler", {
            "fields": ("site_name", "logo", "logo_tag", "favicon", "favicon_tag", "site_slogan", "description", "keywords")
        }),
        ("Google Ayarları", {
            "fields": ("google_analytics_id", "google_search_console_code", "google_adsense_client_id")
        }),
        ("İletişim Bilgileri", {
            "fields": ("whatsapp_number", "phone", "email", "address", "phone2", "email2")
        }),
        ("Sosyal Medya", {
            "fields": ("facebook", "instagram", "twitter", "linkedin", "youtube", "rss")
        }),
        ("Harita Ayarları", {
            "fields": ("google_map_iframe", "map_tag")
        }),
    )

    @admin.display(description="Harita Önizleme")
    def map_tag(self, obj):
        iframe_code = (obj.google_map_iframe or "").strip()
        if iframe_code:
            src_match = re.search(r'src=["\']([^"\']+)["\']', iframe_code, flags=re.IGNORECASE)
            map_src = src_match.group(1) if src_match else iframe_code

            if not (map_src.startswith("http://") or map_src.startswith("https://")):
                return "Harita kodu gecersiz. Lutfen gecerli bir iframe veya URL girin."

            return format_html("""
                <div style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius:8px; box-shadow: 0 0 8px rgba(0,0,0,0.2);">
                    <div style="position: absolute; top:0; left:0; width:100%; height:100%;">
                        <iframe
                            src="{}"
                            style="border:0; width:100%; height:100%;"
                            loading="lazy"
                            referrerpolicy="no-referrer-when-downgrade"
                            allowfullscreen>
                        </iframe>
                    </div>
                </div>
            """, map_src)
        return "Henüz harita eklenmedi."
    

    @admin.display(description="Logo Önizleme")
    def logo_tag(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:80px;">', obj.logo.url)
        return "Logo yok"
    

    @admin.display(description="Favicon Önizleme")   
    def favicon_tag(self, obj):
        if obj.favicon:
            return format_html('<img src="{}" style="max-height:32px;">', obj.favicon.url)
        return "Favicon yok"


@admin.register(RSSFeedSource)
class RSSFeedSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "feed_url", "is_active", "order", "item_limit")
    list_filter = ("is_active",)
    search_fields = ("title", "feed_url")
    list_editable = ("is_active", "order", "item_limit")






