"""«Faoliyat» 1-qism: Moliyaviy faoliyat, «Kelajakka qadam» markazi, Öquv-uslubiy hujjatlar — eski saytdagi barça
ichki sahifalar (52 ta, 4 tilda) kartalar bilan. PDF'lar fayl bölsa ulanadi, aks holda `manage.py seed_activity`."""
from django.db import migrations

from apps.pages.activity_seed import seed_files, seed_pages


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    seed_pages(Page, 1)
    seed_files(Page, apps.get_model('pages', 'PageAttachment'), apps.get_model('core', 'Media'), 1)


class Migration(migrations.Migration):
    dependencies = [('pages', '0035_application_page')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
