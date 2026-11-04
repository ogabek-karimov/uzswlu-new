import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.fields import I18nField
from apps.core.html import clean_html, slugify
from apps.core.models import SingletonModel

DISPLAYS = [
    ('embed', 'Ichi ko‘rinadi'), ('open', 'Bosib ochiladi'),
    ('download', 'Yuklab olish'), ('link', 'Matn-havola'),
]


def youtube_id(url: str | None) -> str | None:
    m = re.search(r'(?:youtu\.be/|v=|/shorts/|/embed/|/live/)([\w-]{11})', url or '')
    return m.group(1) if m else None


class AttachmentBase(models.Model):
    """Biriktirilgan PDF yoki havola (post, sahifa, BRM hisoboti uchun umumiy qolip)."""

    file = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='PDF fayl')
    url = models.CharField('Havola (PDF o‘rniga)', max_length=500, blank=True)
    title = I18nField('Nomi')
    meta = I18nField('Izoh (sana, til)')
    display = models.CharField('Saytda ko‘rinishi', max_length=10, choices=DISPLAYS, default='open')
    height = models.PositiveIntegerField('Ramka balandligi (px)', default=680)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        abstract = True
        ordering = ['order', 'id']

    def clean(self):
        if not self.file_id and not self.url:
            raise ValidationError('PDF fayl yoki havola kiritilishi kerak')


class Category(models.Model):
    """Post kategoriyalari ("Xalqaro hamkorlik", "Talabalar hayoti" …) — 4 tilda."""

    key = models.CharField('Kalit', max_length=60, unique=True)
    name = I18nField('Nomi', required_uz=True)

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['key']

    def __str__(self):
        return self.name.get('uz') or self.key


class Post(models.Model):
    """Yangiliklar, e'lonlar va tadbirlar — bitta to'plam.

    Saytda ko'rinishi: status=published, hidden emas va published_at <= hozir (kelajak vaqt = rejalashtirilgan).
    """

    TYPES = [('news', 'Yangilik'), ('announcements', 'E’lon'), ('events', 'Tadbir')]
    STATUSES = [('draft', 'Qoralama'), ('published', 'Nashr qilingan')]

    type = models.CharField('Turi', max_length=14, choices=TYPES, default='news', db_index=True)
    title = I18nField('Sarlavha', required_uz=True)
    excerpt = I18nField('Qisqa tavsif', multiline=True)
    body = I18nField('Matn (HTML)', multiline=True)
    slug = models.CharField('Manzil', max_length=120, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='posts', verbose_name='Kategoriya')
    sdg = models.PositiveSmallIntegerField('BRM maqsadi (0 — kirmaydi)', default=0, db_index=True)
    cover = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Asosiy rasm')
    cover_ru = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Rasm (ruscha)')
    cover_en = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Rasm (inglizcha)')
    cover_zh = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Rasm (xitoycha)')
    tags = I18nField('Teglar (har qatorda bittadan)', multiline=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='posts', verbose_name='Muallif')
    published_at = models.DateTimeField('Nashr vaqti', null=True, blank=True, db_index=True)
    status = models.CharField('Holati', max_length=10, choices=STATUSES, default='draft', db_index=True)
    hidden = models.BooleanField('Saytdan vaqtincha yashirilgan', default=False, db_index=True)
    starts_at = models.DateTimeField('Boshlanish (tadbir)', null=True, blank=True, db_index=True)
    ends_at = models.DateTimeField('Tugash (tadbir)', null=True, blank=True)
    location = I18nField('O‘tkaziladigan joy')
    views = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Postlar'
        ordering = ['-published_at', '-id']
        constraints = [models.UniqueConstraint(fields=['type', 'slug'], name='post_type_slug_uniq')]

    def __str__(self):
        return self.title.get('uz') or f'Post #{self.pk}'

    def clean(self):
        if self.type == 'events' and self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValidationError({'ends_at': 'Tugash vaqti boshlanishdan oldin bo‘lishi mumkin emas'})
        if not 0 <= self.sdg <= 17:
            raise ValidationError({'sdg': '0 dan 17 gacha'})

    def _unique_slug(self, base: str) -> str:
        slug = base
        for i in range(2, 200):
            taken = Post.objects.filter(type=self.type, slug=slug).exclude(pk=self.pk)
            if not taken.exists():
                return slug
            slug = f'{base}-{i}'
        return f'{base}-{timezone.now():%H%M%S}'

    def save(self, *args, **kwargs):
        # HTML matnni tozalash (XSS'dan himoya)
        self.body = {k: clean_html(v) for k, v in (self.body or {}).items() if isinstance(v, str)}
        if not self.slug and self.title.get('uz'):
            self.slug = self._unique_slug(slugify(self.title['uz']))
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def visible(cls, lang: str = 'uz'):
        """Saytda ko'rinadigan postlar (tilga qarab)."""
        qs = cls.objects.filter(status='published', hidden=False, published_at__lte=timezone.now())
        if settings.HIDE_UNTRANSLATED_POSTS:
            qs = qs.filter(**{f'title__{lang}__isnull': False}).exclude(**{f'title__{lang}': ''})
        return qs


class PostAttachment(AttachmentBase):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')

    class Meta(AttachmentBase.Meta):
        verbose_name = 'Fayl (PDF)'
        verbose_name_plural = 'Fayllar (PDF)'


class PostGalleryImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='gallery')
    image = models.ForeignKey('core.Media', on_delete=models.PROTECT, related_name='+', verbose_name='Rasm')
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Galereya rasmi'
        verbose_name_plural = 'Galereya'
        ordering = ['order', 'id']


class Slide(models.Model):
    """Bosh sahifa karuseli (xodim sahifalari pastida ham shu slaydlar chiqadi)."""

    name = models.CharField('Nomi (faqat admin uchun)', max_length=200)
    image = models.ForeignKey('core.Media', on_delete=models.PROTECT, related_name='+', verbose_name='Rasm (16:9, 1920×1080)')
    alt = I18nField('Rasm tavsifi')
    link = models.CharField('Bosilganda ochiladi', max_length=500, blank=True)
    starts_at = models.DateTimeField('Ko‘rsatish boshlanadi', null=True, blank=True)
    ends_at = models.DateTimeField('Tugaydi', null=True, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)

    class Meta:
        verbose_name = 'Slayd'
        verbose_name_plural = 'Karusel'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    @classmethod
    def active(cls):
        now = timezone.now()
        return cls.objects.filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now), Q(ends_at__isnull=True) | Q(ends_at__gt=now)).select_related('image')


class Leader(models.Model):
    """Rektorat: rektor, prorektorlar va matbuot kotibi."""

    KINDS = [('rector', 'Rektor'), ('prorector', 'Prorektor'), ('press', 'Matbuot kotibi / maslahatchi')]
    kind = models.CharField('Turi', max_length=10, choices=KINDS, default='prorector')
    name = models.CharField('F.I.Sh.', max_length=200)
    staff_id = models.CharField('Xodim ID (HEMIS)', max_length=20, blank=True)
    photo = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Rasm')
    role = I18nField('Lavozim', multiline=True, required_uz=True)
    hours = I18nField('Qabul kuni va vaqti')
    phone = models.CharField('Telefon', max_length=40, blank=True)
    ext = models.CharField('Ichki raqam', max_length=20, blank=True)
    email = models.EmailField('E-pochta', blank=True)
    reception = models.BooleanField('“Virtual qabulxona” formasida ko‘rsatish', default=True)
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)

    class Meta:
        verbose_name = 'Rahbar'
        verbose_name_plural = 'Rahbariyat'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class DocCategory(models.Model):
    title = I18nField('Nomi', required_uz=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Hujjat toifasi'
        verbose_name_plural = 'Hujjat toifalari'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title.get('uz') or f'Toifa #{self.pk}'


class Document(models.Model):
    """Me'yoriy hujjat: har bir tilda alohida PDF (o'zbekchasi majburiy) yoki tashqi havola (lex.uz)."""

    title = I18nField('Nomi', required_uz=True)
    category = models.ForeignKey(DocCategory, on_delete=models.PROTECT, related_name='documents', verbose_name='Toifa')
    number = models.CharField('Hujjat raqami va sanasi', max_length=200, blank=True)
    file_uz = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='PDF (o‘zbekcha)')
    file_ru = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='PDF (ruscha)')
    file_en = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='PDF (inglizcha)')
    file_zh = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='PDF (xitoycha)')
    url = models.CharField('Tashqi havola (PDF o‘rniga)', max_length=500, blank=True)
    display = models.CharField('Saytda ko‘rinishi', max_length=10, choices=DISPLAYS[:3], default='open')
    height = models.PositiveIntegerField('Ramka balandligi', default=680)
    pages = models.CharField('Qaysi sahifalarda (manzillar, vergul bilan)', max_length=300, default='meyoriy-hujjatlar')
    downloads = models.PositiveIntegerField('Yuklab olindi', default=0, editable=False)
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)

    class Meta:
        verbose_name = 'Hujjat'
        verbose_name_plural = 'Hujjatlar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title.get('uz') or f'Hujjat #{self.pk}'

    def clean(self):
        if not (self.file_uz_id or self.url):
            raise ValidationError('O‘zbekcha PDF yoki tashqi havola kiritilishi kerak')

    def file_for(self, lang: str):
        return getattr(self, f'file_{lang}', None) or self.file_uz

    @property
    def page_list(self) -> list[str]:
        return [p.strip() for p in self.pages.split(',') if p.strip()]


class VideoCategory(models.Model):
    key = models.CharField('Til kodi', max_length=20, unique=True)
    title = I18nField('Nomi', required_uz=True)
    greeting = models.CharField('Bezak so‘z ("Hello", "你好")', max_length=60, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Video toifasi'
        verbose_name_plural = 'Video toifalari'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title.get('uz') or self.key


class Video(models.Model):
    """Videolar YouTube'da turadi — saytda faqat havola, nom va muqova."""

    url = models.URLField('YouTube havolasi', max_length=500)
    title = I18nField('Nomi', required_uz=True)
    category = models.ForeignKey(VideoCategory, on_delete=models.CASCADE, related_name='videos', verbose_name='Toifa')
    teacher = models.CharField('O‘qituvchi', max_length=200, blank=True)
    duration = models.CharField('Davomiyligi', max_length=12, blank=True)
    thumbnail = models.URLField('Muqova', max_length=500, blank=True)
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)

    class Meta:
        verbose_name = 'Video'
        verbose_name_plural = 'Videolar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title.get('uz') or self.url

    def save(self, *args, **kwargs):
        vid = youtube_id(self.url)
        if vid and not self.thumbnail:
            self.thumbnail = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
        super().save(*args, **kwargs)


class VideoPage(SingletonModel):
    """Video sahifasi: jonli efir va YouTube kanal."""

    live = models.BooleanField('Hozir jonli efirda', default=False)
    live_url = models.URLField('Efir havolasi', blank=True)
    next_title = I18nField('Keyingi efir nomi')
    next_at = models.DateTimeField('Keyingi efir vaqti', null=True, blank=True)
    channel_url = models.URLField('YouTube kanal', default='https://www.youtube.com/c/Ozbekistondavlatjahontillariuniversiteti')

    class Meta:
        verbose_name = 'Video sahifasi'
        verbose_name_plural = 'Video sahifasi'

    def __str__(self):
        return 'Video sahifasi'


class StateSymbol(models.Model):
    """Davlat ramzlari: bayroq, gerb va madhiya (bosh sahifadagi blok)."""

    KEYS = [('flag', 'Davlat bayrog‘i'), ('emblem', 'Davlat gerbi'), ('anthem', 'Davlat madhiyasi')]
    key = models.CharField('Turi', max_length=10, choices=KEYS, unique=True)
    image = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Rasm')
    audio = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Audio (madhiya, MP3)')
    title = I18nField('Sarlavha', required_uz=True)
    description = I18nField('Tavsif', multiline=True)
    link = models.URLField('Rasmiy manba havolasi', blank=True)
    source = models.CharField('Manba nomi', max_length=60, blank=True)

    class Meta:
        verbose_name = 'Davlat ramzi'
        verbose_name_plural = 'Ramzlar'
        ordering = ['id']

    def __str__(self):
        return self.get_key_display()


class Partner(models.Model):
    name = I18nField('Nomi', required_uz=True)
    logo = models.ForeignKey('core.Media', on_delete=models.PROTECT, related_name='+', verbose_name='Logo (shaffof/oq fonli, ≥400px)')
    url = models.URLField('Sayt', blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Hamkor'
        verbose_name_plural = 'Hamkorlar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name.get('uz') or f'Hamkor #{self.pk}'


class TaughtLanguage(models.Model):
    """Universitetda o'qitiladigan tillar (bosh sahifa)."""

    code = models.CharField('ISO 639-1 kodi', max_length=5, unique=True)
    native = models.CharField('Tilning o‘z yozuvidagi nomi', max_length=60)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'O‘qitiladigan til'
        verbose_name_plural = 'O‘qitiladigan tillar'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.native} ({self.code})'
