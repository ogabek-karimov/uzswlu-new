from django.db import models


class HemisSnapshot(models.Model):
    """HEMIS'dan olingan oxirgi ma'lumot (bitta yozuv). `manage.py sync_hemis` har kuni yangilaydi;
    sayt va admin panel HEMIS API'ga har so'rovda murojaat qilmaydi — shu nusxadan o'qiydi."""

    data = models.JSONField('Ma’lumot', default=dict)
    synced_at = models.DateTimeField('Oxirgi sinxronlash', null=True, blank=True)
    error = models.TextField('Oxirgi xato', blank=True)
    running_since = models.DateTimeField('Sinxronlash boshlangan', null=True, blank=True)  # qulf: ikki jarayon bir vaqtda HEMIS'ga chiqmasin

    class Meta:
        verbose_name = 'HEMIS nusxasi'
        verbose_name_plural = 'HEMIS nusxasi'

    def __str__(self):
        return f'HEMIS · {self.synced_at:%Y-%m-%d %H:%M}' if self.synced_at else 'HEMIS · hali sinxronlanmagan'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    LOCK_HOURS = 3  # qulf shuncha soatdan keyin eskirgan hisoblanadi (jarayon yiqilib qulfni bo'shatmagan bo'lsa)

    @classmethod
    def acquire(cls) -> bool:
        """Sinxronlash qulfini atomik olish: bitta UPDATE — poyga yo'q."""
        from datetime import timedelta

        from django.utils import timezone
        cls.load()
        now = timezone.now()
        stale = models.Q(running_since__isnull=True) | models.Q(running_since__lt=now - timedelta(hours=cls.LOCK_HOURS))
        return cls.objects.filter(pk=1).filter(stale).update(running_since=now) == 1

    @classmethod
    def release(cls) -> None:
        cls.objects.filter(pk=1).update(running_since=None)
