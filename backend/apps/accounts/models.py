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
        ('faculty', 'Fakultet admini'),
        ('pages', 'Sahifalar muharriri'),
        ('sdg', 'BRM menejeri'),  # faqat BRM bo'limi: 17 maqsad matni, rasmlari va PDF hisobotlari
    ]
    STATUSES = [('active', 'Faol'), ('invited', 'Taklif qilingan'), ('disabled', 'Yopilgan')]

    name = models.CharField('F.I.Sh.', max_length=200)
    role = models.CharField('Rol', max_length=12, choices=ROLES, default='editor')
    status = models.CharField('Holati', max_length=10, choices=STATUSES, default='active')
    position = models.CharField('Lavozim', max_length=200, blank=True)
    department = models.CharField('Bo‘lim', max_length=200, blank=True)
    scope = models.CharField('Ruxsat doirasi (fakultet)', max_length=100, blank=True)
    hemis_id = models.CharField('HEMIS ID', max_length=20, blank=True, db_index=True)
    avatar = models.ForeignKey('core.Media', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name='Rasm')
    # Kirishni bloklash: 5 marta noto'g'ri parol — 15 daqiqa (Payload'dagi kabi)
    login_attempts = models.PositiveSmallIntegerField('Noto‘g‘ri urinishlar', default=0, editable=False)
    lock_until = models.DateTimeField('Bloklangan vaqtgacha', null=True, blank=True)
    # Payload CMS'dan ko'chirilgan parol (birinchi kirishda Django usuliga o'tkaziladi va o'chiriladi)
    legacy_password = models.TextField(blank=True, editable=False)

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
