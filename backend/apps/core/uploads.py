"""Foydalanuvchi yuklagan fayllar: umumiy kirish nuqtalari. Chuqur tekshiruv — `filesafe.py` da (faqat Python)."""
import io

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from .filesafe import clean_upload, open_image, read_all

__all__ = ['check_upload', 'clean_upload', 'square_avatar']


def check_upload(file, exts, max_bytes: int) -> str:
    """Faqat tekshiradi (nusxa qaytarmaydi) va kengaytmani qaytaradi. Saqlash uchun `clean_upload` ishlating."""
    return clean_upload(file, exts, max_bytes)[1]


def square_avatar(file, max_bytes: int = 10 * 1024 * 1024, side: int = 600) -> ContentFile:
    """JPG/PNG/WEBP → EXIF bo'yicha aylantirilgan, kvadrat qilib kesilgan WebP (~600 px). Metadata saqlanmaydi."""
    from PIL import Image, ImageOps

    data = read_all(file, max_bytes)
    img = open_image(data)
    if img.format not in ('JPEG', 'PNG', 'WEBP'):
        raise ValidationError('JPG, PNG yoki WEBP yuklang')
    img = ImageOps.exif_transpose(img)
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'A' in img.mode or img.info.get('transparency') else 'RGB')
    size = min(side, img.width, img.height)
    img = ImageOps.fit(img, (size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=85)
    return ContentFile(buf.getvalue(), name='avatar.webp')
