"""Binolarning xaritadagi nuqtalari aniqlashtirildi (Yandex Xaritalar, 2026-11-25).

Eski (seed) koordinatalar 40–215 m chetda edi: xarita belgisi binoga emas, qo'shni hovli yoki ko'chaga tushardi.
Faqat hali eski seed qiymati turgan yozuvlar yangilanadi — admin panelda qo'lda o'zgartirilgan joyga tegilmaydi.
"""
from django.db import migrations

# kalit: (eski seed qiymati, aniq nuqta)
FIX = {
    'main': ('41.286038, 69.194908', '41.286035, 69.193875'),        # Kichik halqa yo'li, G9-A, 21A (bosh bino)
    'philology': ('41.307347, 69.188426', '41.309207, 69.187803'),   # Zakovat ko'chasi, 4
    'journalism': ('41.297568, 69.204987', '41.297953, 69.205513'),  # Lutfiy ko'chasi, 8
    'russian': ('41.286907, 69.231657', '41.287104, 69.232063'),     # Muqimiy ko'chasi, 104
}


def forward(apps, schema_editor):
    Campus = apps.get_model('structure', 'Campus')
    for key, (old, new) in FIX.items():
        Campus.objects.filter(key=key, coords__in=(old, '')).update(coords=new)


def backward(apps, schema_editor):
    Campus = apps.get_model('structure', 'Campus')
    for key, (old, new) in FIX.items():
        Campus.objects.filter(key=key, coords=new).update(coords=old)


class Migration(migrations.Migration):
    dependencies = [('structure', '0011_applications')]
    operations = [migrations.RunPython(forward, backward)]
