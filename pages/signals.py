import os
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
from django.dispatch import receiver
from .models import NewsImage, NewsVideo, News, Category, Author
from PIL import Image
from django.conf import settings
from django.db import transaction

# from easy_thumbnails.files import get_thumbnailer


# Temizleme fonksiyonu
def clear_site_cache():
    # Tüm cache'i temizlemek en güvenlisidir ancak istersen
    # sadece belirli anahtarları (home_page, category_list) silebilirsin.
    cache.clear()
    print("Sistem: İçerik değişti, Redis cache temizlendi.")


# Tüm modeller için toplu sinyal bağlama
@receiver([post_save, post_delete], sender=News)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Author)
@receiver([post_save, post_delete], sender=NewsImage)
@receiver([post_save, post_delete], sender=NewsVideo)
def invalidate_cache_on_change(sender, instance, **kwargs):
    clear_site_cache()


# Resim yüklendiğinde WebP'ye çeviren ve model silindiğinde fiziksel dosyayı temizleyen mantığı     #  kuruyoruz.
@receiver(post_save, sender=NewsImage)
def optimized_image_processing(sender, instance, created, **kwargs):
    """
    İşlemi bir transaction sonrası (on_commit) çalıştırarak
    veri tabanı tutarlılığını koruyoruz.
    """
    if created and instance.image:
        transaction.on_commit(lambda: process_image_to_webp(instance.id))


def process_image_to_webp(instance_id):
    # Bu fonksiyon normalde bir Celery task'ı olmalıdır.
    # Şimdilik basitçe logic'i buraya koyuyoruz.

    try:
        obj = NewsImage.objects.get(id=instance_id)
        img_path = obj.image.path
        if os.path.exists(img_path) and not img_path.endswith(".webp"):
            img = Image.open(img_path)
            new_path = os.path.splitext(img_path)[0] + ".webp"
            img.save(new_path, "WEBP", quality=85)

            # Eski dosyayı güvenli sil
            if os.path.exists(img_path):
                os.remove(img_path)

            # Update_fields kullanarak recursive sinyal tetiklenmesini engelle
            obj.image.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
            obj.save(update_fields=["image"])
    except NewsImage.DoesNotExist:
        pass


# eski resimleri ve video silme sinyalleri
@receiver(post_delete, sender=NewsImage)
def auto_delete_image_on_delete(sender, instance, **kwargs):
    """NewsImage silindiğinde fiziksel dosyayı temizler"""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
            # Easy-thumbnails tarafından oluşturulanları da temizlemek için:
            # instance.image.delete_thumbnails()

# video dosyaları için de benzer bir mantık uygulayalım
# video dosyaları silindiğinde fiziksel dosyayı temizler
@receiver(post_delete, sender=NewsVideo)
def auto_delete_video_on_delete(sender, instance, **kwargs):
    """NewsVideo silindiğinde fiziksel dosyayı temizler"""
    if instance.video_file and instance.video_file.name:
        try:
            if os.path.isfile(instance.video_file.path):
                os.remove(instance.video_file.path)
        except ValueError:
            pass

# haber resimleri güncellenirken eski dosyaların silinmesi için sinyaller

@receiver(post_save, sender=NewsImage)
def auto_delete_old_image_on_change(sender, instance, **kwargs):
    """NewsImage güncellendiğinde eski resmi sistemden temizler"""
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

# video dosyaları güncellenirken eski dosyaların silinmesi için sinyaller
@receiver(post_save, sender=NewsVideo)
def auto_delete_old_video_on_change(sender, instance, **kwargs):
    """NewsVideo güncellendiğinde eski videoyu sistemden temizler"""
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).video_file
    except sender.DoesNotExist:
        return False

    if not old_file or not old_file.name:
        return

    new_file = instance.video_file
    if not old_file == new_file:
        try:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)
        except ValueError:
            pass


# #################
"""
#haber resimleri silinirken thumbnail dosyalarının da silinmesi için sinyaller
@receiver(post_delete, sender=NewsImage)
def thumb_temizle(sender, instance, **kwargs):
    if instance.image: # Modelindeki resim alanının adı
        try:
            # get_thumbnailer, o resme bağlı tüm versiyonları bulur
            thumbnailer = get_thumbnailer(instance.image)
            # Disk üzerindeki tüm türetilmiş resimleri siler
            thumbnailer.delete_thumbnails() # type: ignore
        except Exception as e:
            print(f"Thumbnail silinirken hata oluştu: {e}")
"""
# ###########

"""
# haber resimleri silinirken dosyaların da silinmesi için sinyaller
@receiver(post_delete, sender=NewsImage)
def delete_image_file(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

# haber resimleri güncellenirken eski dosyaların silinmesi için sinyaller
@receiver(pre_save, sender=NewsImage)
def delete_old_image_file(sender, instance, **kwargs):
    if not instance.pk:
        return False
    try:
        old_file = NewsImage.objects.get(pk=instance.pk).image
    except NewsImage.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
"""
