"""Abituriyentlar bo'limi (1-bosqich): PhD dasturlari (10 ta), Stipendiyalar (3 ta + «Grantlar» Telegram bloki), To'lov-kontrakt
miqdori (2 ta; Excel — PDF'ga o'girilgan), Ta'lim grantlari soni, Hamkorlarimiz, Sharoitlar — eski saytdagi hujjatlar sayt ichida
(«Ichi ko'rinadi»; bir nechtasi — hujjat tanlagich), Vakansiya — foydali havolalar kartalari. Nomlar va kirish gaplari 4 tilda.
Matn — faqat sahifa hali namunaviy/bo'sh bo'lsa; hujjatlar — faqat sahifada hali hujjat bo'lmasa
(seed_data/applicants_pages.json, seed_data/files/applicants/)."""
import json
from pathlib import Path

from django.core.files import File
from django.db import migrations

DATA = Path(__file__).resolve().parents[3] / 'seed_data'
FILES = DATA / 'files' / 'applicants'
PLACEHOLDER = ('namunaviy', 'примерный', 'демонстрационный', 'sample text', 'are added in the admin', '示例')


def _placeholder(body) -> bool:
    uz = (body or {}).get('uz') or ''
    return len(uz) < 200 or any(w in uz for w in PLACEHOLDER)


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    path = DATA / 'applicants_pages.json'
    if not path.exists():
        return
    for slug, spec in json.loads(path.read_text(encoding='utf-8')).items():
        p = Page.objects.filter(slug=slug, template='text').first()
        if not p:
            continue
        fields = []
        if _placeholder(p.body):
            p.body = {**(p.body or {}), **spec['body']}
            fields.append('body')
        cta = spec.get('cta')
        if cta and not p.cta_url:
            for k, v in cta.items():
                setattr(p, k, v)
            fields += list(cta)
        if not PageAttachment.objects.filter(page=p).exists():
            for n, d in enumerate(spec.get('docs') or [], start=1):
                media = None
                if d.get('file'):
                    src = FILES / d['file']
                    if not src.exists():
                        continue
                    with src.open('rb') as fh:
                        size = src.stat().st_size
                        media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                        media.file.save(f'{slug}-{n}.pdf', File(fh, name=f'{slug}-{n}.pdf'), save=False)
                        media.save()
                PageAttachment.objects.create(page=p, file=media, url=d.get('url') or '', title=d['title'], meta=d.get('meta') or {},
                                              display=d.get('display') or 'embed', order=n)
            fields.append('updated_at')
        if fields:
            p.save(update_fields=sorted(set(fields) | {'updated_at'}))


class Migration(migrations.Migration):
    dependencies = [('pages', '0027_conditions_text_page'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
