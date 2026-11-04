from django.core.exceptions import ValidationError
from django.db import models

from apps.content.models import AttachmentBase
from apps.core.fields import I18nField
from apps.core.html import clean_page_html, slugify
from apps.core.models import SingletonModel


class Page(models.Model):
    """Saytdagi sahifalar daraxti. Yuqori daraja — menyu bo'limlari, ichidagilari — sahifalar. Menyu shu daraxtdan quriladi.

    group   — menyu bo'limi (mega-menyu ustuni)
    text    — matnli sahifa (kirish, matn, raqamlar, vaqt chizig'i, PDF'lar)
    special — saytning maxsus sahifasi (Rektorat, BRM maqsadi, Hujjatlar …) — mazmuni o'z bo'limida
    link    — tashqi havola yoki PDF fayl
    """

    TEMPLATES = [('group', 'Menyu bo‘limi'), ('text', 'Matnli sahifa'), ('special', 'Maxsus sahifa'), ('link', 'Havola / PDF')]

    title = I18nField('Nomi', required_uz=True)
    template = models.CharField('Shablon', max_length=8, choices=TEMPLATES, default='text')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='children', verbose_name='Ota sahifa')
    slug = models.SlugField('Manzil', max_length=120, null=True, blank=True, unique=True)
    url = models.CharField('Havola / yo‘l', max_length=500, blank=True, help_text='Maxsus sahifa va havola uchun to‘liq yo‘l (masalan /rektorat)')
    file = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='PDF fayl')
    group_key = models.CharField('Bo‘lim kaliti (belgi uchun)', max_length=40, blank=True, help_text='university, applicants, activity, news, sdg, programs, video, contact')
    description = I18nField('Bo‘lim tavsifi', multiline=True)
    overview = models.CharField('Bo‘limning umumiy sahifasi', max_length=200, blank=True)
    sdg = models.PositiveSmallIntegerField('BRM maqsadi', null=True, blank=True)
    in_menu = models.BooleanField('Menyuda ko‘rsatish', default=True)
    published = models.BooleanField('Nashr qilingan', default=True, db_index=True)
    highlight = models.BooleanField('Ajratib ko‘rsatish', default=False)
    lead = I18nField('Kirish matni', multiline=True)
    body = I18nField('Matn (HTML)', multiline=True, help_text='Vaqt chizig‘i joyi: <!-- timeline -->')
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sahifa'
        verbose_name_plural = 'Sahifalar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title.get('uz') or f'Sahifa #{self.pk}'

    def clean(self):
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({'parent': 'Sahifa o‘zining ichiga qo‘yilmaydi'})
        if self.sdg is not None and not 1 <= self.sdg <= 17:
            raise ValidationError({'sdg': '1 dan 17 gacha'})

    def save(self, *args, **kwargs):
        self.body = {k: clean_page_html(v) for k, v in (self.body or {}).items() if isinstance(v, str)}
        auto = self.template == 'text' and not self.slug and self.title.get('uz')
        self.slug = slugify(self.title['uz'] if auto else self.slug) if (auto or self.slug) else None
        if auto:
            base, i = self.slug, 2
            while Page.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug, i = f'{base}-{i}', i + 1
        super().save(*args, **kwargs)

    @property
    def site_url(self) -> str:
        """Sahifaning saytdagi manzili (tilsiz)."""
        if self.template == 'text':
            return f'/{self.slug}'
        if self.template == 'link':
            return (self.file.url if self.file_id else None) or self.url or '#'
        return self.url or (f'/{self.slug}' if self.slug else '#')


class PageFact(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='facts')
    value = models.CharField('Qiymat', max_length=40)
    label = I18nField('Izoh')
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Raqam'
        verbose_name_plural = 'Raqamlar'
        ordering = ['order', 'id']


class PageTimeline(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='timeline')
    label = I18nField('Yil / sarlavha')
    text = I18nField('Matn', multiline=True)
    highlight = models.BooleanField('Ajratib ko‘rsatish', default=False)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Vaqt chizig‘i'
        verbose_name_plural = 'Vaqt chizig‘i'
        ordering = ['order', 'id']


class PageAttachment(AttachmentBase):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='attachments')

    class Meta(AttachmentBase.Meta):
        verbose_name = 'PDF hujjat'
        verbose_name_plural = 'PDF hujjatlar'


class SdgGoal(models.Model):
    """BRM — BMTning 17 ta barqaror rivojlanish maqsadi. Maqsadga bog'langan yangiliklar Post.sdg'dan avtomatik olinadi."""

    n = models.PositiveSmallIntegerField('Raqami', unique=True)
    title = I18nField('Nomi', required_uz=True)
    subtitle = I18nField('Maqsad tavsifi', multiline=True)
    url = models.CharField('Sahifa manzili', max_length=200)
    impact_rank = models.CharField('THE Impact: o‘rni', max_length=20, blank=True)
    impact_score = models.CharField('THE Impact: ball', max_length=20, blank=True)
    highlight_label = models.CharField('Ajratilgan natija: sarlavha', max_length=120, blank=True)
    highlight_value = I18nField('Ajratilgan natija: qiymati')

    class Meta:
        verbose_name = 'BRM maqsadi'
        verbose_name_plural = 'BRM maqsadlari'
        ordering = ['n']

    def __str__(self):
        return f"BRM {self.n} — {self.title.get('uz', '')}"

    def clean(self):
        if not 1 <= (self.n or 0) <= 17:
            raise ValidationError({'n': '1 dan 17 gacha'})


class SdgSection(models.Model):
    """Maqsad sahifasidagi ichki bo'lim (sayt tabi)."""

    goal = models.ForeignKey(SdgGoal, on_delete=models.CASCADE, related_name='sections')
    key = models.CharField('Kalit', max_length=40, blank=True)
    title = I18nField('Nomi', required_uz=True)
    body = I18nField('Matni (HTML)', multiline=True)
    images = models.ManyToManyField('core.Media', blank=True, related_name='+', verbose_name='Rasmlar')
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Ichki bo‘lim'
        verbose_name_plural = 'Ichki bo‘limlar'
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        from apps.core.html import clean_html
        self.body = {k: clean_html(v) for k, v in (self.body or {}).items() if isinstance(v, str)}
        super().save(*args, **kwargs)


class SdgGoalReport(AttachmentBase):
    goal = models.ForeignKey(SdgGoal, on_delete=models.CASCADE, related_name='reports')

    class Meta(AttachmentBase.Meta):
        verbose_name = 'Hisobot'
        verbose_name_plural = 'Hisobotlar'


class SdgPage(SingletonModel):
    """BRM bosh sahifasi (/brm): GreenMetric, THE Impact natijalari, hisobotlar, ta'lim bloki."""

    impact_year = models.PositiveSmallIntegerField('THE Impact Rankings yili', default=2025)
    gm_year = models.PositiveSmallIntegerField('GreenMetric yili', default=2026)
    gm_world_rank = models.CharField('Dunyoda (masalan #512)', max_length=12, blank=True)
    gm_world_change = models.IntegerField('Dunyoda: o‘tgan yilga nisbatan', null=True, blank=True)
    gm_asia_rank = models.CharField('Osiyoda', max_length=12, blank=True)
    gm_asia_change = models.IntegerField('Osiyoda: o‘tgan yilga nisbatan', null=True, blank=True)
    gm_country_rank = models.CharField('O‘zbekistonda', max_length=12, blank=True)
    gm_country_change = models.IntegerField('O‘zbekistonda: o‘tgan yilga nisbatan', null=True, blank=True)
    gm_highlight_text = I18nField('Ajratilgan natija matni')
    gm_highlight_url = models.CharField('Ajratilgan natija havolasi', max_length=200, blank=True)
    education_title = I18nField('Ta’lim bloki: sarlavha')
    education_text = I18nField('Ta’lim bloki: matn', multiline=True)
    education_tags = I18nField('Ta’lim bloki: teglar (har qatorda bittadan)', multiline=True)
    education_url = models.CharField('Ta’lim bloki: havola', max_length=200, blank=True)

    class Meta:
        verbose_name = 'BRM sahifasi'
        verbose_name_plural = 'BRM sahifasi'

    def __str__(self):
        return 'BRM sahifasi'


class SdgCategory(models.Model):
    """GreenMetric 6 yo'nalishi."""

    page = models.ForeignKey(SdgPage, on_delete=models.CASCADE, related_name='categories')
    code = models.CharField('Kod (SI, EC, WS, WR, TR, ED)', max_length=4)
    title = I18nField('Nomi', required_uz=True)
    subtitle = models.CharField('Inglizcha nomi', max_length=80, blank=True)
    badge = I18nField('Belgi (masalan, O‘zbekistonda #1)')
    url = models.CharField('Havola', max_length=200)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'GreenMetric yo‘nalishi'
        verbose_name_plural = 'GreenMetric yo‘nalishlari'
        ordering = ['order', 'id']


class SdgOverviewReport(AttachmentBase):
    page = models.ForeignKey(SdgPage, on_delete=models.CASCADE, related_name='reports')

    class Meta(AttachmentBase.Meta):
        verbose_name = 'Hisobot'
        verbose_name_plural = 'Hisobotlar'
