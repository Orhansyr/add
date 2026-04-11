from typing import Any

from django.contrib import admin
from .models import News, NewsImage, NewsVideo, Category, Author
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin





class NewsImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NewsImage
    extra = 2
    readonly_fields = ("image_tag",)
    sortable_field_name = ("order","name")


class NewsVideoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NewsVideo
    extra = 1
    readonly_fields = ("video_tag",)
    sortable_field_name = "order"





@admin.register(News)
class NewsAdmin(SortableAdminMixin, admin.ModelAdmin):  # type: ignore
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "category", "is_active", "order", "published_date")
    inlines = [NewsImageInline, NewsVideoInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name","order",)
    


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name",)
    readonly_fields = ("image_tag",)

    # AuthorAdmin'de image_tag alanını readonly_fields olarak ekleyerek, yazarın resim önizlemesini admin panelinde görüntüleyebiliriz. get_readonly_fields metodunu override ederek, yeni bir yazar eklerken image_tag alanının readonly olmasını sağlarız, böylece sadece mevcut yazarların resimlerini görebiliriz, 
    def get_readonly_fields(self, request, obj=None) -> list[str] | tuple[Any, ...]:
        if obj is None:
            return ()
        return tuple(self.readonly_fields)
