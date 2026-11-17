"""«Virtual qabulxona» va «Korporativ poçta» kartalari endi saytning o'z ichki sahifalariga olib boradi."""
from django.db import migrations

MOVES = {'/site/reception': '/virtual-qabulxona', '/services/mail': '/korporativ-pochta'}


def forward(apps, schema_editor):
    QuickLink = apps.get_model('content', 'QuickLink')
    for old, new in MOVES.items():
        QuickLink.objects.filter(url=old).update(url=new)


def backward(apps, schema_editor):
    QuickLink = apps.get_model('content', 'QuickLink')
    for old, new in MOVES.items():
        QuickLink.objects.filter(url=new).update(url=old)


class Migration(migrations.Migration):
    dependencies = [('content', '0006_seed_quick_links')]
    operations = [migrations.RunPython(forward, backward)]
