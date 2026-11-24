"""«Faoliyat» bölimi sahifalari eski saytdan (seed_data/activity_pages_*.json): sahifalar, kartalar va PDF hujjatlar.

Sahifalar va kartalar migratsiya bilan yaratiladi. PDF'lar (~1 GB) Git'da yöq — seed_data/files-large/activity/ papkasida turadi:
fayl bölsa ulanadi, bölmasa keyin `python manage.py seed_activity` bilan ulanadi (takror işlatiş xavfsiz).
"""
import json
from pathlib import Path

from django.core.files import File

DATA = Path(__file__).resolve().parents[2] / 'seed_data'
FILES = DATA / 'files-large' / 'activity'
PLACEHOLDER = 'admin panel orqali kiritiladi'  # boşlanğiç namunaviy matn — faqat şunday sahifalar yangilanadi


def specs(part: int) -> list[dict]:
    path = DATA / f'activity_pages_{part}.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []


def seed_pages(Page, part: int) -> None:
    for order, s in enumerate(specs(part), start=1):
        p = Page.objects.filter(slug=s['slug']).first()
        fields = {'body': s['body'], 'showcase': {'blocks': s['showcase']}}
        if p is None:
            parent = Page.objects.filter(slug=s['parent']).first() if s['parent'] else None
            if s['parent'] and not parent:
                continue
            Page.objects.create(slug=s['slug'], title=s['title'], template='text', parent=parent, in_menu=False, order=order, **fields)
        elif s['root'] and PLACEHOLDER in str((p.body or {}).get('uz', '')) and not (p.showcase or {}).get('blocks'):
            for k, v in fields.items():
                setattr(p, k, v)
            p.save(update_fields=[*fields, 'updated_at'])


def seed_files(Page, PageAttachment, Media, part: int, files: Path = FILES) -> int:
    added = 0
    for s in specs(part):
        p = Page.objects.filter(slug=s['slug']).first()
        if not p or not s['docs']:
            continue
        for n, (fname, title) in enumerate(s['docs'], start=1):
            src = files / fname
            if not src.exists() or p.attachments.filter(order=n).exists():
                continue
            name = f"{s['slug']}-{n}.pdf"
            with src.open('rb') as fh:
                size = src.stat().st_size
                m = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                m.file.save(name, File(fh, name=name), save=False)
                m.save()
            PageAttachment.objects.create(page=p, file=m, url='', title=title, meta={}, display=s['display'], order=n)
            added += 1
    return added
