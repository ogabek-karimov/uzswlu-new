"""Sahifada bo'lim xodimlari (HEMIS bo'limi) + «Axborot-resurs markazi» matni (eski saytdan uz/ru/en, xitoychasi — tarjima;
o'zbekchasi yangi alifboda). Matn faqat sahifa hali qisqa/namunaviy bo'lsa yoziladi; xodimlar — HEMIS'dagi ARM bo'limidan."""
import json
from pathlib import Path

from django.db import migrations, models

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'arm_page.json'
PLACEHOLDER = ('namunaviy', 'примерный', 'sample text', '示例')


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='axborot-resurs-markazi').first()
    if not p or not SEED.exists():
        return
    seed = json.loads(SEED.read_text(encoding='utf-8'))
    body = dict(p.body or {})
    for lang, text in seed.items():
        old = body.get(lang) or ''
        if len(old) < 500 or any(w in old for w in PLACEHOLDER):
            body[lang] = text
    p.body = body
    # Nom bo'yicha: haqiqiy HEMIS'da ID boshqa — sayt nomni HEMIS ID'siga o'zi aylantiradi
    p.staff_department = p.staff_department or 'Axborot-resurs markazi'
    p.save(update_fields=['body', 'staff_department'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0011_uz_new_alphabet'), ('core', '0007_uz_new_alphabet')]
    operations = [
        migrations.AddField('page', 'staff_department', models.CharField(
            'Matndan oldin bo‘lim xodimlari (HEMIS bo‘limi)', max_length=64, blank=True,
            help_text='HEMIS bo‘limi ID — xodimlari saytga HEMIS orqali kirgach sahifada avtomatik chiqadi (Staff kabi)')),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
