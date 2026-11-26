"""Qabul bo'limi eski saytdan: «Qabul bo'yicha ma'lumotlar» va 7 ta ichki sahifa (Qabul fanlari, kvota, ijodiy imtihonlar,
super kontrakt, eslatma…) 4 tilda, PDF'lar sayt ichida. Katta fayllar Git'dan tashqarida (seed_data/files-large/applicants-qabul) —
bo'lmasa keyin `manage.py seed_admission`. Batafsil: apps/pages/admission_seed.py."""
from django.db import migrations

from apps.pages.admission_seed import seed_admission


def forward(apps, schema_editor):
    seed_admission(apps.get_model('pages', 'Page'), apps.get_model('pages', 'PageAttachment'), apps.get_model('core', 'Media'))


class Migration(migrations.Migration):
    dependencies = [('pages', '0043_university_charter_pdf')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
