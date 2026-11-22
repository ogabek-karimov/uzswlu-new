"""Bo'limlar sahifasi (/bolimlar) kartalari: eski saytdagi (uzswlu.uz/bolimlar) bo'lim rahbarlari — faqat jadval bo'sh bo'lsa.
Suratlar admin panelda yuklanadi (eski saytdan ko'chirilmaydi)."""
import json
from pathlib import Path

import django.db.models.deletion
from django.db import migrations, models

import apps.core.fields

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'unit_heads.json'


def seed(apps, schema_editor):
    UnitHead = apps.get_model('content', 'UnitHead')
    if UnitHead.objects.exists() or not SEED.exists():
        return
    rows = json.loads(SEED.read_text(encoding='utf-8'))
    UnitHead.objects.bulk_create([
        UnitHead(name=r['name'], position={'uz': r['position']}, phone=r.get('phone', ''), ext=r.get('ext', ''), url=r.get('url', ''), order=i)
        for i, r in enumerate(rows, start=1)
    ])


class Migration(migrations.Migration):
    dependencies = [('content', '0008_quick_link_glossary'), ('core', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='UnitHead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='F.I.Sh.')),
                ('position', apps.core.fields.I18nField(multiline=True, required_uz=True, verbose_name='Lavozimi (bo‘lim nomi bilan)')),
                ('phone', models.CharField(blank=True, max_length=40, verbose_name='Telefon')),
                ('ext', models.CharField(blank=True, max_length=20, verbose_name='Ichki raqam')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-pochta')),
                ('url', models.CharField(blank=True, help_text='Sayt ichida: /xalqaro-aloqalar-bolimi — tashqi: https://…', max_length=500, verbose_name='Bo‘lim sahifasi')),
                ('order', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Tartib')),
                ('visible', models.BooleanField(default=True, verbose_name='Saytda ko‘rinadi')),
                ('photo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='core.media', verbose_name='Rasm')),
            ],
            options={'verbose_name': 'Bo‘lim rahbari', 'verbose_name_plural': 'Bo‘limlar', 'ordering': ['order', 'id']},
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
