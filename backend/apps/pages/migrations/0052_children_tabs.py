"""Ichki sahifalar uchun tugmali menyu (tab) belgisi; «Xalqaro akkreditatsiya» sahifasida yoqiladi."""

from django.db import migrations, models


def forward(apps, schema_editor):
    apps.get_model('pages', 'Page').objects.filter(slug='xalqaro-akkreditatsiya').update(children_tabs=True)


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0051_accounting_page'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='children_tabs',
            field=models.BooleanField(default=False, help_text='Ichki sahifalar tugmalari sahifa tepasida; bosilganda tanlangan sahifa matni va hujjatlari pastda ochiladi (sahifadan chiqmasdan). Ichma-ich sahifalar ham shu tarzda ochiladi', verbose_name='Ichki sahifalar — tugmali menyu (tab)'),
        ),
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
