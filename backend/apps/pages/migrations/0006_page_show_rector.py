"""Matnli sahifaga «rektor kartasi» (admin → Rahbariyat'dan). «Universitet tarixi»: eski saytdagi (uzswlu.uz/universitet-tarixi) matn
uz/ru/en tillarida (joriy rektor haqidagi paragraflarsiz — ular kartada) va karta yoqiladi. Matn faqat sahifa hali qisqa bo'lsa yoziladi
(admin panelda to'ldirilgan bo'lsa tegilmaydi)."""
import json
from pathlib import Path

from django.db import migrations, models

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'university_history.json'


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='universitet-tarixi').first()
    if not p or not SEED.exists():
        return
    body = dict(p.body or {})
    if len(body.get('uz') or '') < 500:
        body.update(json.loads(SEED.read_text(encoding='utf-8')))
        p.body = body
    p.show_rector = True
    p.save(update_fields=['body', 'show_rector'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0005_hide_alumni_club')]
    operations = [
        migrations.AddField(model_name='page', name='show_rector', field=models.BooleanField(default=False, help_text='Rektor surati va ma’lumoti — admin → Rahbariyat’dan avtomatik (rektor almashsa sahifa o‘zi yangilanadi)', verbose_name='Matndan keyin rektor kartasi')),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
