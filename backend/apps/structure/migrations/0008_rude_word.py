"""Haqoratli so'zlar jadvali; boshlang'ich ro'yxat seed_data/rude_words.json dan (faqat jadval bo'sh bo'lsa)."""
import json
from pathlib import Path

from django.db import migrations, models

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'rude_words.json'


def seed(apps, schema_editor):
    RudeWord = apps.get_model('structure', 'RudeWord')
    if RudeWord.objects.exists() or not SEED.exists():
        return
    rows = json.loads(SEED.read_text(encoding='utf-8'))
    RudeWord.objects.bulk_create([RudeWord(word=r['word'], lang=r['lang']) for r in rows], ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [('structure', '0007_appeal_passport')]
    operations = [
        migrations.CreateModel(
            name='RudeWord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=60, unique=True, verbose_name='So‘z')),
                ('lang', models.CharField(choices=[('uz', 'O‘zbekcha'), ('ru', 'Ruscha'), ('en', 'Inglizcha'), ('zh', 'Xitoycha')], db_index=True, default='uz', max_length=2, verbose_name='Til')),
                ('active', models.BooleanField(default=True, verbose_name='Faol')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Haqoratli so‘z', 'verbose_name_plural': 'Haqoratli so‘zlar', 'ordering': ['lang', 'word']},
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
