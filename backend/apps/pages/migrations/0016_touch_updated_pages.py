"""Matni migratsiya orqali yangilangan sahifalarning «Oxirgi yangilanish» sanasi — shu migratsiya ishlagan kun.
(Oldingi migratsiyalar save(update_fields=[...]) bilan saqlagan — auto_now sana o'zgarmagan edi.)"""
from django.db import migrations
from django.utils import timezone

SLUGS = ('axborot-resurs-markazi', 'universitet-talim-siyosati', 'universitet-tarixi')


def touch(apps, schema_editor):
    apps.get_model('pages', 'Page').objects.filter(slug__in=SLUGS).update(updated_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('pages', '0015_page_cta')]
    operations = [migrations.RunPython(touch, migrations.RunPython.noop)]
