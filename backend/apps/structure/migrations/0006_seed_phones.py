"""Telefonlar ma'lumotnomasini eski saytdagi (uzswlu.uz/aloqa) jadvaldan to'ldirish — faqat jadval bo'sh bo'lsa.
Manba: seed_data/phones.json (bo'lim sarlavhalari va xodim qatorlari, asl tartibda). Keyin admin panelda tahrirlanadi."""
import json
from pathlib import Path

from django.db import migrations

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'phones.json'


def seed(apps, schema_editor):
    PhoneEntry = apps.get_model('structure', 'PhoneEntry')
    if PhoneEntry.objects.exists() or not SEED.exists():
        return
    rows = json.loads(SEED.read_text(encoding='utf-8'))
    PhoneEntry.objects.bulk_create([
        PhoneEntry(is_section=True, position={'uz': r['section']}, order=i) if 'section' in r else
        PhoneEntry(name=r.get('name', ''), position={'uz': r.get('position') or ''}, ext=r.get('ext', ''), phone=r.get('phone', ''), order=i)
        for i, r in enumerate(rows, start=1)
        if r.get('section') or r.get('position') or r.get('name')
    ])


class Migration(migrations.Migration):
    dependencies = [('structure', '0005_phone_entry')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
