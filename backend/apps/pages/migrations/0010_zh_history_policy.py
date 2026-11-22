"""«Universitet tarixi» va «Universitet ta'lim siyosati» sahifalariga xitoycha (zh) akademik tarjima. Faqat zh matni hali
namunaviy yoki qisqa bo'lsa yoziladi — admin panelda to'ldirilgan bo'lsa tegilmaydi."""
import json
from pathlib import Path

from django.db import migrations

SEED = Path(__file__).resolve().parents[3] / 'seed_data'
PAGES = {'universitet-tarixi': 'university_history.json', 'universitet-talim-siyosati': 'education_policy.json'}


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for slug, name in PAGES.items():
        p = Page.objects.filter(slug=slug).first()
        if not p or not (SEED / name).exists():
            continue
        body = dict(p.body or {})
        zh = body.get('zh') or ''
        if len(zh) < 300 or '示例' in zh:
            body['zh'] = json.loads((SEED / name).read_text(encoding='utf-8'))['zh']
            p.body = body
            p.save(update_fields=['body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0009_education_policy_text')]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
