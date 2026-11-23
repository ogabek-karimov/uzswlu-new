import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.core.utils import sha256


class User(AbstractUser):
    """Admin panel foydalanuvchilari. Superadmin login-parol bilan kiradi; muharrirlar keyinchalik HEMIS orqali ham kirishi mumkin."""

    ROLES = [
        ('superadmin', 'Superadmin'),
        ('editor', 'Kontent muharriri'),
        ('pages', 'Sahifalar muharriri'),
        ('sdg', 'BRM menejeri'),  # faqat BRM bo'limi: 17 maqsad matni, rasmlari va PDF hisobotlari
    ]
    STATUSES = [('active', 'Faol'), ('invited', 'Taklif qilingan'), ('disabled', 'Yopilgan')]

    name = models.CharField('F.I.Sh.', max_length=200)
    # Rol — `Role.slug` (superadmin admin panelda yangi rollar yaratadi); tizim rollari `ROLES` ro'yxatida
    role = models.CharField('Rol', max_length=40, default='editor', db_index=True)
    status = models.CharField('Holati', max_length=10, choices=STATUSES, default='active')
    position = models.CharField('Lavozim', max_length=200, blank=True)
    department = models.CharField('Bo‘lim', max_length=200, blank=True)
    scope = models.CharField('Ruxsat doirasi (fakultet)', max_length=100, blank=True)
    hemis_id = models.CharField('HEMIS ID', max_length=20, blank=True, db_index=True)
    avatar = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name='Rasm')
    # Kirishni bloklash: 5 marta noto'g'ri parol — 15 daqiqa (Payload'dagi kabi)
    login_attempts = models.PositiveSmallIntegerField('Noto‘g‘ri urinishlar', default=0, editable=False)
    lock_until = models.DateTimeField('Bloklangan vaqtgacha', null=True, blank=True)
    # Ikki bosqichli tasdiq (TOTP, RFC 6238): Google Authenticator, Microsoft Authenticator, 1Password va h.k.
    totp_secret = models.CharField(max_length=40, blank=True, editable=False)
    totp_enabled = models.BooleanField('2FA yoqilgan', default=False, editable=False)
    totp_last_step = models.BigIntegerField(default=0, editable=False)  # bir kod ikki marta ishlatilmasin (replay)
    recovery_hashes = models.JSONField(default=list, blank=True, editable=False)  # zaxira kodlarning sha256 xeshlari
    # Payload CMS'dan ko'chirilgan parol (birinchi kirishda Django usuliga o'tkaziladi va o'chiriladi)
    legacy_password = models.TextField(blank=True, editable=False)
    # HEMIS lavozimidan avtomatik yaratilgan hisob: har kirishda rol/doira HEMIS bo'yicha yangilanadi, lavozim bog'lanishi o'chsa yopiladi
    hemis_auto = models.BooleanField('HEMIS bo‘yicha avtomatik', default=False, editable=False)

    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return self.name or self.username

    def save(self, *args, **kwargs):
        # Rol Django huquqlariga o'tkaziladi: panelga kirish va superadmin
        self.is_superuser = self.is_superuser or self.role == 'superadmin'
        if self.is_superuser:
            self.role = 'superadmin'
        self.is_staff = True
        self.is_active = self.status != 'disabled'
        super().save(*args, **kwargs)


class Role(models.Model):
    """Admin panel roli: qaysi menyu bo'limlarida nima qila olishi (`permissions`: {bo'lim: 'read' | 'write'}).
    Faqat superadmin roli tizim roli (o'zgartirilmaydi va o'chirilmaydi); qolgan hamma rolni (editor, pages, sdg ham) superadmin tahrirlaydi yoki o'chiradi."""
    slug = models.SlugField('Kalit', max_length=40, unique=True)
    name = models.CharField('Nomi', max_length=120)
    description = models.CharField('Izoh', max_length=300, blank=True)
    permissions = models.JSONField('Bo‘limlar bo‘yicha ruxsat', default=dict, blank=True)
    scoped = models.BooleanField('Faqat o‘z fakulteti doirasida (User.scope)', default=False)
    edit_all = models.BooleanField('Boshqalarning postlarini ham tahrirlaydi', default=False)
    system = models.BooleanField('Tizim roli', default=False, editable=False)
    # HEMIS lavozimi shu rolga avtomatik bog'lanadi: HEMIS orqali kirgan dekan/mudir/o'qituvchiga hisob o'zi yaratiladi (bo'sh — o'chiq)
    hemis_role = models.CharField('HEMIS roli', max_length=12, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Rollar'
        ordering = ['-system', 'name']

    def __str__(self):
        return self.name


class StaffSession(models.Model):
    """Saytga HEMIS (my.gov) orqali kirgan xodim sessiyasi (kabinet). Token bazada faqat hash ko'rinishida."""

    hemis_id = models.CharField(max_length=20, db_index=True)
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Xodim sessiyasi'
        verbose_name_plural = 'Xodim sessiyalari'

    def __str__(self):
        return f'{self.hemis_id} → {self.expires_at:%Y-%m-%d %H:%M}'

    @classmethod
    def issue(cls, hemis_id: str, hours: int | None = None) -> str:
        """Yangi sessiya yaratadi va tokenni qaytaradi (faqat bir marta ko'rinadi)."""
        token = secrets.token_urlsafe(32)
        cls.objects.create(
            hemis_id=str(hemis_id),
            token_hash=sha256(token),
            expires_at=timezone.now() + timedelta(hours=hours or settings.STAFF_SESSION_TTL_HOURS),
        )
        return token


class StaffTask(models.Model):
    """Xodim kabinetidagi vazifa: dekan/kafedra mudiri o'z qo'l ostidagilarga beradi, hamma o'ziga ham yozishi mumkin."""
    STATUSES = [('open', 'Bajarilmoqda'), ('done', 'Bajarildi')]

    title = models.CharField('Vazifa', max_length=200)
    note = models.TextField('Izoh', blank=True, max_length=2000)
    assignee_id = models.CharField('Ijrochi (HEMIS ID)', max_length=40, db_index=True)
    assignee_name = models.CharField('Ijrochi', max_length=200, blank=True)
    author_id = models.CharField('Bergan (HEMIS ID)', max_length=40, db_index=True)
    author_name = models.CharField('Bergan', max_length=200, blank=True)
    due = models.DateField('Muddat', null=True, blank=True)
    status = models.CharField('Holat', max_length=8, choices=STATUSES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['status', 'due', '-created_at']
        verbose_name = 'Xodim vazifasi'
        verbose_name_plural = 'Xodim vazifalari'

    def __str__(self):
        return f'{self.title} → {self.assignee_id}'


def check_any_password(user, raw: str) -> bool:
    """Parolni tekshirish: Django usuli, bo'lmasa Payload'dan ko'chirilgan parol (to'g'ri bo'lsa — darhol yangilanadi)."""
    if user.check_password(raw):
        return True
    if user.legacy_password:
        from .hashers import PayloadPBKDF2Hasher
        if PayloadPBKDF2Hasher().verify(raw, user.legacy_password):
            user.set_password(raw)
            user.legacy_password = ''
            user.save(update_fields=['password', 'legacy_password'])
            return True
    return False
