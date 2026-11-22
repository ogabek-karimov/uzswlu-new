"""Sahifa xodimlari kartasi (eski saytdagidek): admin kiritadigan telefon/e-pochta va qabul kunlari.
«Axborot-resurs markazi»: eski saytdagi qabul kunlari (4 tilda) va direktor telefoni nom bo'yicha emas — admin HEMIS ID bilan kiritadi."""
from django.db import migrations, models

import apps.core.fields

HOURS = {
    'uz': 'Duşanbadan jumagaça, har iş kuni soat 8:30 dan 16:30 gaça',
    'ru': 'С понедельника по пятницу, ежедневно с 8:30 до 16:30',
    'en': 'Monday to Friday, 8:30 a.m. – 4:30 p.m.',
    'zh': '周一至周五，每个工作日 8:30–16:30',
}


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='axborot-resurs-markazi').first()
    if p and not any((p.staff_hours or {}).values()):
        p.staff_hours = HOURS
        p.save(update_fields=['staff_hours'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0013_page_staff_extra')]
    operations = [
        migrations.AddField('page', 'staff_contacts', models.JSONField(
            'Xodimlar telefoni / e-pochtasi', default=dict, blank=True,
            help_text='{HEMIS ID: {"phone": "…", "email": "…"}} — kartada ko‘rinadi')),
        migrations.AddField('page', 'staff_hours', apps.core.fields.I18nField(verbose_name='Qabul kunlari (xodimlar kartasida)')),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
