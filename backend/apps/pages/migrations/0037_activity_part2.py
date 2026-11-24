"""«Faoliyat» 2-qism: Ilmiy faoliyat, Xalqaro akkreditatsiya, Korrupsiyaga qarşi kuraşiş, Madaniy-ma’rifiy faoliyat, Xalqaro aloqalar, Yaşil universitet — eski saytdagi barça
ichki sahifalar (4 tilda, matnlari bilan) kartalar bilan. PDF'lar fayl bölsa ulanadi, aks holda `manage.py seed_activity`."""
from django.db import migrations

from apps.pages.activity_seed import seed_files, seed_pages


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    seed_pages(Page, 2)
    seed_files(Page, apps.get_model('pages', 'PageAttachment'), apps.get_model('core', 'Media'), 2)


class Migration(migrations.Migration):
    dependencies = [('pages', '0036_activity_part1')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
