from django.db import models


class HemisSnapshot(models.Model):
    """HEMIS'dan olingan oxirgi ma'lumot (bitta yozuv). `manage.py sync_hemis` har kuni yangilaydi;
    sayt va admin panel HEMIS API'ga har so'rovda murojaat qilmaydi — shu nusxadan o'qiydi."""

    data = models.JSONField('Ma’lumot', default=dict)
    synced_at = models.DateTimeField('Oxirgi sinxronlash', null=True, blank=True)
    error = models.TextField('Oxirgi xato', blank=True)

    class Meta:
        verbose_name = 'HEMIS nusxasi'
        verbose_name_plural = 'HEMIS nusxasi'

    def __str__(self):
        return f'HEMIS · {self.synced_at:%Y-%m-%d %H:%M}' if self.synced_at else 'HEMIS · hali sinxronlanmagan'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
