"""Universitet nizomi: menyudagi PDF endi o'zimizda (eski saytga havola emas). Fayl Git'dan tashqarida
(seed_data/files-large/docs/ozdjtu-nizomi.pdf) — bo'lmasa keyin `manage.py seed_activity --part 3`."""
from django.db import migrations

from apps.pages.activity_seed import seed_nizom


def forward(apps, schema_editor):
    seed_nizom(apps.get_model('pages', 'Page'), apps.get_model('core', 'Media'))


class Migration(migrations.Migration):
    dependencies = [('pages', '0042_online_cameras')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
