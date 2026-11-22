"""Qabul sahifasi manzili yildan mustaqil: /qabul-20262027 → /qabul (eski manzil saytda /qabul ga yo'naltiriladi)."""
from django.db import migrations

OLD, NEW = '/qabul-20262027', '/qabul'


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Page.objects.filter(url=OLD).update(url=NEW)
    Page.objects.filter(overview=OLD).update(overview=NEW)


def backward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Page.objects.filter(url=NEW).update(url=OLD)
    Page.objects.filter(overview=NEW).update(overview=OLD)


class Migration(migrations.Migration):
    dependencies = [('pages', '0003_graduates_text_page')]
    operations = [migrations.RunPython(forward, backward)]
