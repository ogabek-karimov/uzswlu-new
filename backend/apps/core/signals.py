from django.core.files.storage import default_storage
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Media


@receiver(post_delete, sender=Media)
def remove_media_files(sender, instance: Media, **kwargs):
    """Yozuv o'chsa, fayl va uning kichik o'lchamlari ham diskdan o'chadi."""
    names = list((instance.sizes or {}).values())
    if instance.file:
        names.append(instance.file.name)
    for name in names:
        try:
            default_storage.delete(name)
        except Exception:  # noqa: BLE001 — fayl allaqachon yo'q bo'lsa ham o'chirish davom etadi
            pass
