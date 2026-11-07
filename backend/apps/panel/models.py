from django.conf import settings
from django.db import models


class LoginEvent(models.Model):
    """Admin panelga har bir kirish urinishi: vaqt, IP, qurilma, brauzer va natija."""

    METHODS = [('password', 'Login va parol'), ('hemis', 'HEMIS')]
    RESULTS = [('success', 'Muvaffaqiyatli'), ('bad_password', 'Noto‘g‘ri parol'), ('locked', 'Bloklangan'), ('denied', 'Ruxsat yo‘q')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name='Foydalanuvchi')
    username = models.CharField('Kiritilgan login', max_length=100, blank=True)
    method = models.CharField('Usul', max_length=10, choices=METHODS, default='password')
    result = models.CharField('Natija', max_length=14, choices=RESULTS, db_index=True)
    ip = models.CharField('IP', max_length=45, blank=True)
    network = models.CharField('Tarmoq', max_length=40, blank=True)
    browser = models.CharField('Brauzer', max_length=60, blank=True)
    os = models.CharField('Operatsion tizim', max_length=60, blank=True)
    device = models.CharField('Qurilma', max_length=20, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    created_at = models.DateTimeField('Vaqt', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Kirish urinishi'
        verbose_name_plural = 'Kirish tarixi'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.username} · {self.get_result_display()}'


class Version(models.Model):
    """Saqlangan holat (post, sahifa, sozlamalar) — "Asl holiga qaytarish" va o'zgarishlar tarixi uchun."""

    entity = models.CharField('Bo‘lim', max_length=40, db_index=True)
    entity_id = models.CharField(max_length=40, blank=True, db_index=True)
    data = models.JSONField('Holat', default=dict)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Versiya'
        verbose_name_plural = 'Versiyalar'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.entity} #{self.entity_id} · {self.created_at:%Y-%m-%d %H:%M}'


class RevokedToken(models.Model):
    """Chiqishda (logout) yoki yangilashda bekor qilingan JWT'lar (jti). Muddati o'tgach yozuv o'zi o'chiriladi.
    Bazada saqlanadi (kesh emas): kesh tozalansa ham bekor qilingan token qayta yaroqli bo'lib qolmasin."""

    jti = models.CharField(max_length=32, unique=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = 'Bekor qilingan token'
        verbose_name_plural = 'Bekor qilingan tokenlar'
