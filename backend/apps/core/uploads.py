"""Foydalanuvchi yuklagan fayllarni tekshirish: kengaytma, hajm va tarkib (magic bytes), avatar tayyorlash."""
import io
import os

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

_OLE = (b'\xd0\xcf\x11\xe0',)
_ZIP = (b'PK\x03\x04',)
MAGIC = {
    '.pdf': (b'%PDF',),
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.png': (b'\x89PNG\r\n\x1a\n',),
    '.doc': _OLE,
    '.ppt': _OLE,
    '.docx': _ZIP,
    '.pptx': _ZIP,
}


def check_upload(file, exts: set[str] | tuple[str, ...], max_bytes: int) -> str:
    """Faylni tekshiradi va kengaytmasini qaytaradi (masalan '.pdf'). Noto'g'ri bo'lsa ValidationError."""
    ext = os.path.splitext(getattr(file, 'name', '') or '')[1].lower()
    if ext not in exts or ext not in MAGIC:
        raise ValidationError('Fayl turi ruxsat etilmagan')
    if file.size > max_bytes:
        raise ValidationError(f'Fayl {max_bytes // 1024 // 1024} MB dan katta')
    head = file.read(8)
    file.seek(0)
    if not any(head.startswith(m) for m in MAGIC[ext]):
        raise ValidationError('Fayl tarkibi kengaytmasiga mos emas')
    return ext


def square_avatar(file, max_bytes: int = 10 * 1024 * 1024, side: int = 600) -> ContentFile:
    """JPG/PNG/WEBP → EXIF bo'yicha aylantirilgan, kvadrat qilib kesilgan WebP (~600 px)."""
    from PIL import Image, ImageOps

    if file.size > max_bytes:
        raise ValidationError('Rasm 10 MB dan katta')
    try:
        probe = Image.open(file)
        if probe.format not in ('JPEG', 'PNG', 'WEBP'):
            raise ValidationError('JPG, PNG yoki WEBP yuklang')
        probe.verify()
        file.seek(0)
        img = ImageOps.exif_transpose(Image.open(file))
        img.load()
    except ValidationError:
        raise
    except Exception as exc:  # noqa: BLE001 — buzilgan yoki juda katta rasm
        raise ValidationError('Rasm buzilgan yoki o‘qib bo‘lmadi') from exc
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'A' in img.mode or img.info.get('transparency') else 'RGB')
    size = min(side, img.width, img.height)
    img = ImageOps.fit(img, (size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=85)
    return ContentFile(buf.getvalue(), name='avatar.webp')
