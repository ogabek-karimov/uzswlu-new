"""«Faoliyat» sahifalari matnidagi rasmlar (eski saytdan, 38 ta, WebP: frontend/public/images/activity/). Faqat rasmi bor va
matni hali rasmsiz sahifalar yangilanadi (admin qöşgan rasmlar ustidan yozilmaydi)."""
from django.db import migrations

from apps.pages.activity_seed import specs


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for part in (1, 2):
        for s in specs(part):
            if '/images/activity/' not in str(s['body']):
                continue
            p = Page.objects.filter(slug=s['slug']).first()
            if p and '<img' not in str(p.body):
                p.body = s['body']
                p.save(update_fields=['body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0037_activity_part2')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
