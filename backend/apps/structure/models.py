import os
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.fields import I18nField
from apps.core.models import SingletonModel
from apps.core.storage import private_storage

FORMS = [('day', 'Kunduzgi'), ('evening', 'Kechki'), ('distance', 'Sirtqi')]
FORM_LABELS = {
    'day': {'uz': 'Kunduzgi', 'ru': 'Очная', 'en': 'Full-time', 'zh': '全日制'},
    'evening': {'uz': 'Kechki', 'ru': 'Вечерняя', 'en': 'Evening', 'zh': '夜校'},
    'distance': {'uz': 'Sirtqi', 'ru': 'Заочная', 'en': 'Distance', 'zh': '函授'},
}


class Faculty(models.Model):
    """Fakultet: admin to'ldiradigan qism. Dekan, statistika, dekanat va kafedralar HEMIS'dan keladi."""

    slug = models.SlugField('Manzil (/faculty/<manzil>)', max_length=80, unique=True)
    hemis_id = models.CharField('HEMIS ID (fakultet)', max_length=40, blank=True, db_index=True, help_text='HEMIS sinxronlash shu orqali bog‘laydi')
    name = I18nField('Nomi', required_uz=True)
    logo = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Logo (kvadrat, ≥240×240)')
    cover = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Muqova')
    about = I18nField('Fakultet haqida', multiline=True)
    phone = models.CharField('Telefon', max_length=40, blank=True)
    email = models.CharField('E-pochta', max_length=120, blank=True)
    address = I18nField('Manzil / xona')
    map_url = models.URLField('Xarita havolasi', blank=True, max_length=600)
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)

    class Meta:
        verbose_name = 'Fakultet'
        verbose_name_plural = 'Fakultetlar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name.get('uz') or self.slug


class Department(models.Model):
    """Kafedra: o'zbekcha nomi HEMIS'dan; ru/en/zh tarjimalari va rasm shu yerda."""

    hemis_id = models.CharField('HEMIS ID', max_length=120, unique=True)
    faculty_slug = models.CharField('Fakultet (manzil)', max_length=80, blank=True, db_index=True)
    name = I18nField('Nomi')
    image = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.PROTECT, related_name='+', verbose_name='Kafedra rasmi')
    about = I18nField('Kafedra haqida', multiline=True)
    room = models.CharField('Xona', max_length=60, blank=True)
    ext = models.CharField('Ichki telefon', max_length=20, blank=True)
    show_staff = models.BooleanField('Xodimlar ro‘yxatini sahifada ko‘rsatish', default=True)

    class Meta:
        verbose_name = 'Kafedra'
        verbose_name_plural = 'Kafedralar'
        ordering = ['hemis_id']

    def __str__(self):
        return self.name.get('uz') or self.hemis_id


class StaffProfile(models.Model):
    """Xodimning saytdagi qo'shimcha profili. Ism, surat, bo'lim va lavozim HEMIS'dan; qolgani — xodim kabinetidan."""

    hemis_id = models.CharField('HEMIS ID', max_length=20, unique=True)
    name = models.CharField('F.I.Sh. (HEMIS’dan, qidiruv uchun)', max_length=200, blank=True)
    about = I18nField('Xodim haqida', multiline=True)
    contacts = models.JSONField('Aloqa', default=list, blank=True, help_text='[{"type":"email","value":"..."}]')
    socials = models.JSONField('Ijtimoiy tarmoqlar', default=list, blank=True, help_text='[{"network":"instagram","url":"https://..."}]')
    science = models.JSONField('Ilmiy profillar', default=list, blank=True, help_text='[{"network":"orcid","url":"https://..."}]')
    own_photo = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name='O‘z surati')
    hidden = models.BooleanField('Saytda yashirilgan', default=False, db_index=True)
    show_cv = models.BooleanField('CV Staff’da ko‘rinadi', default=True)
    show_books = models.BooleanField('Kitoblar Staff’da ko‘rinadi', default=True)
    show_articles = models.BooleanField('Maqolalar Staff’da ko‘rinadi', default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Xodim profili'
        verbose_name_plural = 'Xodim profillari'

    def __str__(self):
        return self.name or self.hemis_id


def appeal_path(instance, filename: str) -> str:
    """Murojaat fayli: yopiq saqlash, nom tasodifiy (mijoz nomi saqlanmaydi, manzilni taxmin qilib bo'lmaydi)."""
    return f"appeals/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}"


def staff_doc_path(instance, filename: str) -> str:
    return f"cabinet/{instance.hemis_id}/{timezone.now():%Y%m}/{uuid.uuid4().hex[:12]}{os.path.splitext(filename)[1].lower()}"


class StaffDocument(models.Model):
    """Kabinetdagi hujjatlar: CV, kitoblar, maqolalar, taqdimotlar (fayl) va videolar (havola)."""

    SECTIONS = [('cv', 'CV'), ('books', 'Kitoblar'), ('presentations', 'Taqdimotlar'), ('articles', 'Maqolalar'), ('videos', 'Videolar')]
    hemis_id = models.CharField('HEMIS ID', max_length=20, db_index=True)
    section = models.CharField('Bo‘lim', max_length=14, choices=SECTIONS)
    title = I18nField('Nomi', required_uz=True)
    file = models.FileField('Fayl', upload_to=staff_doc_path, blank=True, max_length=300)
    url = models.URLField('Havola (videolar)', blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Xodim hujjati'
        verbose_name_plural = 'Xodim hujjatlari'
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['hemis_id', 'section'])]

    def __str__(self):
        return f"{self.hemis_id}: {self.title.get('uz', '')}"

    def clean(self):
        if not self.file and not self.url:
            raise ValidationError('Fayl yoki havola kerak')


class ProgramGroup(models.Model):
    KEY_LEVELS = [('bachelor', 'Bakalavriat'), ('master', 'Magistratura')]
    key = models.CharField('Kalit', max_length=30)
    level = models.CharField('Daraja', max_length=10, choices=KEY_LEVELS)
    title = I18nField('Nomi', required_uz=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Yo‘nalishlar guruhi'
        verbose_name_plural = 'Yo‘nalishlar guruhlari'
        ordering = ['level', 'order', 'id']
        constraints = [models.UniqueConstraint(fields=['level', 'key'], name='program_group_uniq')]

    def __str__(self):
        return f"{self.get_level_display()}: {self.title.get('uz', self.key)}"


class Program(models.Model):
    """Ta'lim yo'nalishi (bakalavriat, magistratura, PhD). in_admission — qabul sahifasida chiqadi."""

    LEVELS = [('bachelor', 'Bakalavriat'), ('master', 'Magistratura'), ('phd', 'PhD')]
    code = models.CharField('Shifr', max_length=20)
    title = I18nField('Nomi', required_uz=True)
    level = models.CharField('Daraja', max_length=10, choices=LEVELS, default='bachelor', db_index=True)
    group = models.ForeignKey(ProgramGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name='programs', verbose_name='Guruh')
    language = models.ForeignKey('content.TaughtLanguage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name='O‘qitiladigan til (bo‘sh — o‘zbek tili)')
    form = models.CharField('Ta’lim shakli', max_length=10, choices=FORMS, default='day')
    years = models.PositiveSmallIntegerField('Muddat (yil)', default=4)
    faculty = models.ForeignKey(Faculty, null=True, blank=True, on_delete=models.SET_NULL, related_name='programs', verbose_name='Fakultet')
    in_admission = models.BooleanField('Qabul sahifasida ko‘rsatish', default=False)
    price = I18nField('Kontrakt narxi')
    order = models.PositiveIntegerField('Tartib', default=0, db_index=True)

    class Meta:
        verbose_name = 'Ta’lim yo‘nalishi'
        verbose_name_plural = 'Ta’lim yo‘nalishlari'
        ordering = ['level', 'order', 'id']

    def __str__(self):
        return f"{self.code} — {self.title.get('uz', '')}"


class AdmissionSettings(SingletonModel):
    """Qabul sahifasi (/qabul-20262027)."""

    year = models.CharField('O‘quv yili', max_length=9, default='2026/2027')
    apply_url = models.URLField('Ariza topshirish havolasi', default='https://my.uzbmb.uz')
    documents = I18nField('Kerakli hujjatlar (har qatorda bittadan)', multiline=True)
    documents_url = models.URLField('Hujjatlar ro‘yxati havolasi', blank=True)
    address = I18nField('Qabul komissiyasi manzili')
    hours = I18nField('Ish vaqti')
    phone = models.CharField('Telefon', max_length=40, default='+998 71 230 13 73')
    telegram = models.URLField('Telegram', default='https://t.me/UzSWLU')

    class Meta:
        verbose_name = 'Qabul sozlamalari'
        verbose_name_plural = 'Qabul sozlamalari'

    def __str__(self):
        return f'Qabul {self.year}'


class AdmissionDate(models.Model):
    admission = models.ForeignKey(AdmissionSettings, on_delete=models.CASCADE, related_name='dates')
    title = I18nField('Bosqich', required_uz=True)
    period = I18nField('Muddat')
    current = models.BooleanField('Hozirgi bosqich', default=False)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Muhim sana'
        verbose_name_plural = 'Muhim sanalar'
        ordering = ['order', 'id']


class AdmissionFaq(models.Model):
    admission = models.ForeignKey(AdmissionSettings, on_delete=models.CASCADE, related_name='faq')
    question = I18nField('Savol', required_uz=True)
    answer = I18nField('Javob', multiline=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Ko‘p so‘raladigan savol'
        verbose_name_plural = 'Ko‘p so‘raladigan savollar'
        ordering = ['order', 'id']


class Campus(models.Model):
    key = models.SlugField('Kalit', max_length=30, unique=True)
    name = I18nField('Nomi', required_uz=True)
    address = I18nField('Manzil', required_uz=True)
    phone = models.CharField('Telefon', max_length=40, blank=True)
    map_url = models.URLField('Xarita havolasi', blank=True, max_length=600)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Bino / kampus'
        verbose_name_plural = 'Binolar va kampuslar'
        ordering = ['order', 'id']

    def __str__(self):
        return self.name.get('uz') or self.key


class ContactEmail(models.Model):
    title = I18nField('Nomi', required_uz=True)
    value = models.EmailField('E-pochta')
    extra = I18nField('Qo‘shimcha (har qatorda bittadan)', multiline=True)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'E-pochta (aloqa)'
        verbose_name_plural = 'E-pochtalar (aloqa)'
        ordering = ['order', 'id']

    def __str__(self):
        return self.value


class Appeal(models.Model):
    """Virtual qabulxona murojaati."""

    STATUSES = [('new', 'Yangi'), ('in_progress', 'Ko‘rib chiqilmoqda'), ('done', 'Javob berildi')]
    number = models.CharField('Raqami', max_length=20, blank=True, db_index=True)
    name = models.CharField('F.I.Sh.', max_length=200)
    phone = models.CharField('Telefon', max_length=30)
    email = models.EmailField('E-pochta')
    recipient = models.CharField('Kimga', max_length=40)
    recipient_title = models.CharField('Kimga (nomi)', max_length=300, blank=True)
    message = models.TextField('Murojaat matni')
    file = models.FileField('Biriktirilgan fayl', upload_to=appeal_path, storage=private_storage, blank=True, max_length=300)
    status = models.CharField('Holati', max_length=12, choices=STATUSES, default='new', db_index=True)
    ip = models.CharField(max_length=45, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Murojaat'
        verbose_name_plural = 'Murojaatlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.number} — {self.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f'VQ-{timezone.now().year}-{self.pk:05d}'
            super().save(update_fields=['number'])
