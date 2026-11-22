"""«Universitet ta'lim siyosati»: eski saytdagi (uzswlu.uz/universitet-talim-siyosati) matn uz/ru/en tillarida, joylashuvi bilan
(markazdagi qatorlar — sarlavha, qalin yozuvlar saqlangan) va «Hujjat uslubi» (Times New Roman). Matn faqat sahifa hali qisqa
yoki namunaviy bo'lsa yoziladi — admin panelda to'ldirilgan bo'lsa tegilmaydi."""
import json
from pathlib import Path

from django.db import migrations

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'education_policy.json'


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='universitet-talim-siyosati').first()
    if not p or not SEED.exists():
        return
    body = dict(p.body or {})
    uz = body.get('uz') or ''
    if len(uz) < 500 or 'namunaviy matn' in uz:
        body.update(json.loads(SEED.read_text(encoding='utf-8')))
        p.body = body
    p.doc_style = True
    p.save(update_fields=['body', 'doc_style'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0008_page_show_units')]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
