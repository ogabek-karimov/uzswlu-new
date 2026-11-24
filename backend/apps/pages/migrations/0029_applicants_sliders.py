"""Abituriyentlar bo'limi (2-bosqich): eski saytda faqat buklet rasmlaridan iborat sahifalar — «Nima uchun bu universitet» (16),
«Magistrlik dasturlari» (4) — rasm slayderida (bittadan, ← 1 2 3 →, bosilsa
kattalashadi). Rasmlar seed_data/files/applicants-img/ (1800px JPG; saytda WebP). Faqat sahifa hali namunaviy va bloklar bo'sh bo'lsa."""
from pathlib import Path

from django.core.files import File
from django.db import migrations

FILES = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'applicants-img'
# «Xalqaro talabalar …» — slayder emas, havolali kartalar (pages.0031)
SLUGS = ('nima-uchun-bu-universitet',)
PLACEHOLDER = ('namunaviy', 'примерный', 'демонстрационный', 'sample text', 'are added in the admin', '示例')
SUFFIX = {'uz': '{n}-sahifa', 'ru': 'страница {n}', 'en': 'page {n}', 'zh': '第{n}页'}


def forward(apps, schema_editor):
    from apps.core.models import Media  # haqiqiy model: WebP + o'lchamlar (admin yuklagandagi kabi)
    Page = apps.get_model('pages', 'Page')
    for slug in SLUGS:
        p = Page.objects.filter(slug=slug, template='text').first()
        folder = FILES / slug
        if not p or p.showcase or not folder.exists():
            continue
        uz = (p.body or {}).get('uz') or ''
        if len(uz) >= 200 and not any(w in uz for w in PLACEHOLDER):
            continue
        photos = []
        for n, path in enumerate(sorted(folder.glob('*.jpg')), start=1):
            alt = {k: f"{(p.title or {}).get(k) or p.title.get('uz', '')} — {v.format(n=n)}" for k, v in SUFFIX.items()}
            with path.open('rb') as fh:
                m = Media(folder='posts', alt=alt, file=File(fh, name=f'{slug}-{path.name}'))
                m.save()
            photos.append(m.pk)
        p.showcase = {'blocks': [{'intro': {}, 'stats': {}, 'columns': [], 'outro': {}, 'photos': photos, 'slider': True}]}
        p.body = {k: '<p>[[kartalar-1]]</p>' for k in ('uz', 'ru', 'en', 'zh')}
        p.save(update_fields=['showcase', 'body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0028_applicants_docs'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
