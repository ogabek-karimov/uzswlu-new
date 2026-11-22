"""«Mavjud qulayliklar»: eski saytda sahifa faqat 5 ta buklet rasmidan (inglizcha matn rasm ichida) iborat edi — matn qayta
yozildi va 4 tilga o'girildi (uz — yangi alifboda): talabalar turar joyi (xona turlari, qulayliklar, xavfsizlik, xizmatlar,
yashash qoidalari), yashash muddati va to'lov, kampusdagi ovqatlanish, sport, axborot-resurs markazi — kartali bloklar bilan.
Faqat sahifa hali namunaviy/qisqa va bloklar bo'sh bo'lsa (seed_data/facilities_page.json)."""
import json
from pathlib import Path

from django.db import migrations

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'facilities_page.json'
PLACEHOLDER = ('namunaviy', 'примерный', 'sample text', 'are added in the admin', '示例')


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='mavjud-qulayliklar').first()
    if not p or not SEED.exists() or p.showcase:
        return
    uz = (p.body or {}).get('uz') or ''
    if len(uz) >= 500 and not any(w in uz for w in PLACEHOLDER):
        return
    seed = json.loads(SEED.read_text(encoding='utf-8'))
    p.body = {**(p.body or {}), **seed['body']}
    p.showcase = seed['showcase']
    p.save(update_fields=['body', 'showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0020_youth_union_title_center')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
