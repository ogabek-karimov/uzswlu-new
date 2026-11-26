"""«Tuzilma» sahifasi eski saytdan: kirish matni (4 tilda) va 2 ta PDF (universitet tuzilmasi, rahbariyat va fakultetlar) sayt ichida.
Batafsil: apps/pages/structure_seed.py."""
from django.db import migrations

from apps.pages.structure_seed import seed_structure


def forward(apps, schema_editor):
    seed_structure(apps.get_model('pages', 'Page'), apps.get_model('pages', 'PageAttachment'), apps.get_model('core', 'Media'))


class Migration(migrations.Migration):
    dependencies = [('pages', '0044_admission_pages')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
