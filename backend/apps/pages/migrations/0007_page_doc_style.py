"""Matnli sahifa uchun «Hujjat uslubi» (Times New Roman, sarlavhalar markazda). «Universitet tarixi»da yoqiladi va matn boshiga
eski saytdagidek markazdagi sarlavha qaytariladi (agar matn h2 bilan boshlanmasa)."""
import json
from pathlib import Path

from django.db import migrations, models

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'university_history.json'


def apply(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='universitet-tarixi').first()
    if not p:
        return
    p.doc_style = True
    body = dict(p.body or {})
    if SEED.exists():
        seed = json.loads(SEED.read_text(encoding='utf-8'))
        for lang, html in seed.items():
            cur = body.get(lang) or ''
            if cur and not cur.lstrip().startswith('<h2>') and html.startswith('<h2>'):
                body[lang] = html.split('\n', 1)[0] + '\n' + cur
    p.body = body
    p.save(update_fields=['doc_style', 'body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0006_page_show_rector')]
    operations = [
        migrations.AddField(model_name='page', name='doc_style', field=models.BooleanField(default=False, help_text='Matn Times New Roman shriftida, sarlavhalar markazda (rasmiy hujjat ko‘rinishi)', verbose_name='Hujjat uslubi')),
        migrations.RunPython(apply, migrations.RunPython.noop),
    ]
