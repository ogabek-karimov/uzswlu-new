"""Menyudan olib tashlangan «Toshkent haqida» va «Kontingent» sahifalarini mavjud bazalardan ham o'chiradi.

Boshlang'ich ma'lumot (`pages-seed.json`) faqat bo'sh bazaga yuklanadi, shuning uchun avvaldan o'rnatilgan
bazalarda bu sahifalar menyuda qolib ketardi. Migratsiya bir marta ishlaydi; bo'sh bazada hech narsa qilmaydi.
Ostida bolalari bor sahifa o'chirilmaydi (ota sahifa himoyalangan).
"""
from django.db import migrations

SLUGS = ('toshkent-haqida', 'kontingent')


def remove(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Page.objects.filter(slug__in=SLUGS, children__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [('pages', '0001_initial')]
    operations = [migrations.RunPython(remove, migrations.RunPython.noop)]
