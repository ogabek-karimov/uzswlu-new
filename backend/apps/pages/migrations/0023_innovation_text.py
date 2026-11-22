"""«Innovatsion yechimlar»: eski saytda sahifa faqat 3 ta inglizcha infografika rasmi edi — ma'lumot 4 tilda matn va kartali
bloklarga o'tkazildi: 152 universitet / 22 tashkilot / 30 davlat, mintaqalar va davlatlar bo'yicha hamkorlar, hamkor tashkilotlar
(logotiplar bilan), davlatlar bo'yicha universitetlar (17 ta karta). Suratlar infografikadan kesib olingan (seed_data/files/innovation/).
Faqat sahifa hali namunaviy va bloklar bo'sh bo'lsa (seed_data/innovation_page.json)."""
import json
from pathlib import Path

from django.core.files import File
from django.db import migrations

DATA = Path(__file__).resolve().parents[3] / 'seed_data'
FILES = DATA / 'files' / 'innovation'
PLACEHOLDER = ('namunaviy', 'примерный', 'sample text', 'are added in the admin', '示例')
ALT = {
    'hamkorlik': {'uz': 'Xalqaro hamkorlik', 'ru': 'Международное сотрудничество', 'en': 'International cooperation', 'zh': '国际合作'},
    'tashkilotlar-logolar': {'uz': 'Hamkor tashkilotlar logotiplari', 'ru': 'Логотипы организаций-партнёров', 'en': 'Partner organization logos', 'zh': '合作组织标志'},
}


def _media(name: str):
    from apps.core.models import Media  # haqiqiy model: WebP + o'lchamlar (admin yuklagandagi kabi)
    path = FILES / f'{name}.jpg'
    if not path.exists():
        return None
    with path.open('rb') as fh:
        m = Media(folder='posts', alt=ALT['tashkilotlar-logolar' if name.startswith('tashkilotlar') else 'hamkorlik'], file=File(fh, name=path.name))
        m.save()
    return m.pk


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='innovatsion-yechimlar').first()
    seed_path = DATA / 'innovation_page.json'
    if not p or not seed_path.exists() or p.showcase:
        return
    uz = (p.body or {}).get('uz') or ''
    if len(uz) >= 500 and not any(w in uz for w in PLACEHOLDER):
        return
    seed = json.loads(seed_path.read_text(encoding='utf-8'))
    blocks = seed['showcase']['blocks']
    for b in blocks:
        b['photos'] = [pk for pk in (_media(n) for n in b.get('photos') or []) if pk]
    p.body = {**(p.body or {}), **seed['body']}
    p.showcase = {'blocks': blocks}
    p.save(update_fields=['body', 'showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0022_facilities_photos'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
