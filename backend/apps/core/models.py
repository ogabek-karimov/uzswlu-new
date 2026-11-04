import io
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone
from django.utils.text import slugify as dj_slugify

from .fields import I18nField
from .utils import abs_url

IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'}
MAX_UPLOAD = 50 * 1024 * 1024
MAX_WIDTH = 2560
IMAGE_SIZES = {'thumb': 400, 'card': 900, 'hero': 1920}


def upload_path(instance, filename: str) -> str:
    stem, ext = os.path.splitext(os.path.basename(filename))
    return f"{instance.folder}/{timezone.now():%Y/%m}/{dj_slugify(stem)[:60] or 'file'}-{uuid.uuid4().hex[:8]}{ext.lower()}"


def validate_upload(file) -> None:
    """Ruxsat etilgan turlar: rasm, PDF, MP3. Tarkibi (magic bytes) ham tekshiriladi."""
    ext = os.path.splitext(file.name)[1].lower()
    if file.size > MAX_UPLOAD:
        raise ValidationError('Fayl 50 MB dan katta')
    head = file.read(16)
    file.seek(0)
    if ext == '.pdf':
        if not head.startswith(b'%PDF'):
            raise ValidationError('PDF fayl buzilgan')
    elif ext == '.mp3':
        if not (head.startswith(b'ID3') or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)):
            raise ValidationError('MP3 fayl buzilgan')
    elif ext in IMAGE_EXT:
        from PIL import Image
        try:
            Image.open(file).verify()
        except Exception as exc:
            raise ValidationError('Rasm buzilgan yoki noto‘g‘ri format') from exc
        finally:
            file.seek(0)
    else:
        raise ValidationError('Faqat rasm, PDF yoki MP3 yuklash mumkin')


class Media(models.Model):
    """Rasm, PDF va audio. Rasmlar yuklanganda WebP'ga o'giriladi va kichik o'lchamlari yaratiladi."""

    FOLDERS = [
        ('posts', 'Yangiliklar'), ('carousel', 'Karusel'), ('docs', 'Hujjatlar'),
        ('staff', 'Xodimlar'), ('logos', 'Logotiplar'), ('audio', 'Audio'),
    ]
    KINDS = [('image', 'Rasm'), ('pdf', 'PDF'), ('audio', 'Audio')]

    file = models.FileField('Fayl', upload_to=upload_path, max_length=300, validators=[validate_upload])
    kind = models.CharField(max_length=10, choices=KINDS, editable=False, default='image')
    folder = models.CharField('Papka', max_length=20, choices=FOLDERS, default='posts', db_index=True)
    alt = I18nField('Tavsif (ko‘zi ojizlar uchun)')
    width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    filesize = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    original_size = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    sizes = models.JSONField(default=dict, editable=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, editable=False, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fayl'
        verbose_name_plural = 'Media'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return os.path.basename(self.file.name) if self.file else f'Media #{self.pk}'

    # --- yuklash ---
    def _process_upload(self):
        f = self.file
        f.seek(0)
        raw = f.read()
        self.original_size = len(raw)
        ext = os.path.splitext(f.name)[1].lower()
        if ext == '.pdf':
            self.kind = 'pdf'
            self.filesize = len(raw)
            f.seek(0)
            return
        if ext == '.mp3':
            self.kind = 'audio'
            self.filesize = len(raw)
            f.seek(0)
            return
        from PIL import Image, ImageOps
        self.kind = 'image'
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if 'A' in img.mode or img.info.get('transparency') else 'RGB')
        if img.width > MAX_WIDTH:
            img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)

        def webp(image) -> bytes:
            buf = io.BytesIO()
            image.save(buf, format='WEBP', quality=82)
            return buf.getvalue()

        main = webp(img)
        self.width, self.height, self.filesize = img.width, img.height, len(main)
        stem = os.path.splitext(os.path.basename(f.name))[0]
        self.file = ContentFile(main, name=f'{stem}.webp')
        self._pending_sizes = {
            name: webp(img.resize((w, round(img.height * w / img.width)), Image.LANCZOS))
            for name, w in IMAGE_SIZES.items() if img.width > w
        }

    def save(self, *args, **kwargs):
        self._pending_sizes = {}
        if self.file and not self.file._committed:
            self._process_upload()
        super().save(*args, **kwargs)
        pending = getattr(self, '_pending_sizes', {})
        if pending:
            base = os.path.splitext(os.path.basename(self.file.name))[0]
            self.sizes = {
                name: default_storage.save(f'{self.folder}/sizes/{name}/{base}.webp', ContentFile(data))
                for name, data in pending.items()
            }
            super().save(update_fields=['sizes'])

    # --- manzillar ---
    @property
    def url(self) -> str | None:
        return abs_url(self.file.url) if self.file else None

    def size_url(self, size: str = 'card') -> str | None:
        path = (self.sizes or {}).get(size)
        return abs_url(default_storage.url(path)) if path else self.url


class SingletonModel(models.Model):
    """Bitta yozuvli sozlama (pk=1)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(SingletonModel):
    """Sayt sozlamalari: nom, aloqa, ijtimoiy tarmoqlar, texnik yordam, bosh sahifa raqamlari."""

    name = I18nField('Universitet nomi', required_uz=True)
    abbr = I18nField('Qisqartma')
    description = I18nField('Sayt tavsifi', multiline=True)

    phone = models.CharField('Ishonch telefoni', max_length=40, default='+998 71 230 13 73')
    phone_ext = models.CharField('Ichki raqamlar', max_length=60, blank=True, default='1061–1064')
    email = models.EmailField('Umumiy e-pochta', blank=True, default='uzdjtu@uzswlu.uz')
    address = I18nField('Manzil')
    reception = I18nField('Qabul vaqti / qabulxona matni', multiline=True)
    telegram = models.URLField('Telegram', blank=True, default='https://t.me/UzSWLU')
    instagram = models.URLField('Instagram', blank=True)
    facebook = models.URLField('Facebook', blank=True)
    youtube = models.URLField('YouTube', blank=True, default='https://www.youtube.com/c/Ozbekistondavlatjahontillariuniversiteti')
    x_url = models.URLField('X (Twitter)', blank=True)

    support_telegram = models.URLField('Texnik yordam: Telegram', blank=True, default='https://t.me/Uzswlu_rttm')
    support_text = I18nField('Texnik yordam: tugma matni')
    support_show_in_admin = models.BooleanField('Admin panelda ko‘rsatish', default=True)
    support_show_on_site = models.BooleanField('Saytda ko‘rsatish', default=False)
    support_pages = models.CharField('Qaysi sahifalarda (vergul bilan)', max_length=200, blank=True, default='home,contact,staff')
    support_place = models.CharField('Sahifaning qayerida', max_length=10, default='float', choices=[
        ('float', 'O‘ng pastki burchakda'), ('end', 'Sahifa oxirida'), ('footer', 'Footer ichida'), ('header', 'Sarlavha qatorida'),
    ])

    numbers_auto = models.BooleanField('Bosh sahifa raqamlari HEMIS’dan avtomatik', default=True)
    students = models.PositiveIntegerField('Talabalar', null=True, blank=True)
    staff = models.PositiveIntegerField('Xodimlar', null=True, blank=True)
    faculties = models.PositiveIntegerField('Fakultetlar', null=True, blank=True)
    departments = models.PositiveIntegerField('Kafedralar', null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sayt sozlamalari'
        verbose_name_plural = 'Sayt sozlamalari'

    def __str__(self):
        return 'Sayt sozlamalari'


class Activity(models.Model):
    """Faollik jurnali: kim, nimani, qachon o'zgartirgan."""

    ACTIONS = [
        ('create', 'Yaratildi'), ('edit', 'O‘zgartirildi'), ('publish', 'Nashr qilindi'), ('hide', 'Yashirildi'),
        ('show', 'Ko‘rsatildi'), ('delete', 'O‘chirildi'), ('role', 'Rol'), ('settings', 'Sozlamalar'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    user_name = models.CharField('Kim', max_length=200, blank=True)
    action = models.CharField('Amal', max_length=12, choices=ACTIONS, db_index=True)
    entity = models.CharField('Bo‘lim', max_length=60, db_index=True)
    entity_id = models.CharField(max_length=40, blank=True)
    label = models.CharField('Nomi', max_length=300, blank=True)
    changes = models.JSONField('O‘zgarishlar', default=dict, blank=True)
    ip = models.CharField(max_length=45, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Faollik'
        verbose_name_plural = 'Faollik jurnali'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user_name}: {self.get_action_display()} — {self.entity} {self.label}'


class Hit(models.Model):
    """Sayt statistikasi — cookie'siz va shaxsiy ma'lumotsiz. IP saqlanmaydi: tashrifchi kodi = hash(kunlik tuz + IP + brauzer)."""

    ts = models.DateTimeField(auto_now_add=True, db_index=True)
    visitor = models.CharField(max_length=24)
    kind = models.CharField(max_length=10, db_index=True)  # pageview | event | search
    path = models.CharField(max_length=300, blank=True)
    lang = models.CharField(max_length=2, blank=True)
    referrer = models.CharField(max_length=200, blank=True)
    device = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=2, blank=True)
    name = models.CharField(max_length=200, blank=True)
    value = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = 'Tashrif'
        verbose_name_plural = 'Statistika'
        ordering = ['-ts']
        indexes = [models.Index(fields=['kind', 'ts'])]

    def __str__(self):
        return f'{self.kind} {self.path or self.name}'
