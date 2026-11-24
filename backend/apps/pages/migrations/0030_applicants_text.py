"""Abituriyentlar (3-bosqich): Qo'shma ta'lim dasturlari — matn 4 tilda, imkoniyatlar/afzalliklar, hamkor universitetlar va
«Dastur qanday ishlaydi» kartalarda, 4 ta PDF (hujjat tanlagich), «Ariza topshirish» bloki; Rektor tabrigi — matn 4 tilda +
rektor kartasi (Rahbariyat'dan avtomatik); Hamkorlarimiz — rasm. Faqat sahifa hali namunaviy/bo'sh bo'lsa
(seed_data/applicants_text.json, seed_data/files/applicants*)."""
import json
from pathlib import Path

from django.core.files import File
from django.db import migrations

DATA = Path(__file__).resolve().parents[3] / 'seed_data'
PLACEHOLDER = ('namunaviy', 'примерный', 'демонстрационный', 'sample text', 'are added in the admin', '示例')


def _empty(body) -> bool:
    uz = (body or {}).get('uz') or ''
    return len(uz) < 200 or any(w in uz for w in PLACEHOLDER)


def forward(apps, schema_editor):
    from apps.core.models import Media  # rasm — WebP + o'lchamlar (admin yuklagandagi kabi)
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    HMedia = apps.get_model('core', 'Media')
    path = DATA / 'applicants_text.json'
    if not path.exists():
        return
    seed = json.loads(path.read_text(encoding='utf-8'))

    p = Page.objects.filter(slug='qoshma-talim-dasturlari', template='text').first()
    q = seed['qoshma-talim-dasturlari']
    if p and _empty(p.body) and not p.showcase:
        p.body, p.showcase = q['body'], q['showcase']
        if not p.cta_url:
            for k, v in q['cta'].items():
                setattr(p, k, v)
        p.save()
        if not PageAttachment.objects.filter(page=p).exists():
            for n, d in enumerate(q['docs'], start=1):
                src = DATA / 'files' / 'applicants' / d['file']
                if not src.exists():
                    continue
                with src.open('rb') as fh:
                    size = src.stat().st_size
                    m = HMedia(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                    m.file.save(f'qoshma-talim-{n}.pdf', File(fh, name=f'qoshma-talim-{n}.pdf'), save=False)
                    m.save()
                PageAttachment.objects.create(page=p, file=m, title=d['title'], meta={}, display='embed', order=n)

    p = Page.objects.filter(slug='rektor-tabrigi', template='text').first()
    if p and _empty(p.body):
        p.body = seed['rektor-tabrigi']['body']
        p.show_rector = True
        p.save(update_fields=['body', 'show_rector', 'updated_at'])

    p = Page.objects.filter(slug='hamkorlarimiz', template='text').first()
    h = seed['hamkorlarimiz']
    src = DATA / 'files' / 'applicants-img' / h['photo']
    if p and not p.showcase and src.exists():
        with src.open('rb') as fh:
            m = Media(folder='posts', alt=h['alt'], file=File(fh, name=src.name))
            m.save()
        p.showcase = {'blocks': [{'intro': {}, 'stats': {}, 'columns': [], 'outro': {}, 'photos': [m.pk]}]}
        p.body = {k: (v or '') + '<p>[[kartalar-1]]</p>' for k, v in (p.body or {}).items()}
        p.save(update_fields=['showcase', 'body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0029_applicants_sliders'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
