"""Qabul bo'limi eski saytdan (uzswlu.uz/qabul-20262027): «Qabul bo'yicha ma'lumotlar» sahifasi va uning ichki sahifalari —
Qabul fanlari, Qabul kvotasi, Ijodiy imtihonlar dasturi va jadvali, Ko'zi ojizlar uchun dasturlar, Super kontrakt, Eslatma (4 tilda).

Matn va jadvallar: seed_data/admission_pages.json. PDF'lar — sayt ichida («Ichi ko'rinadi»):
seed_data/files/applicants-qabul/ (Git'da) va katta fayllar seed_data/files-large/applicants-qabul/ (Git'da yo'q;
serverda bo'lmasa keyin `python manage.py seed_admission` ulaydi — takror ishlatish xavfsiz, bor hujjat qayta qo'shilmaydi).
Eski saytdagi xls/doc fayllar sahifa ichida jadval qilib berilgan (Super kontrakt, Qabul fanlari).
"""
import json
from pathlib import Path

from django.core.files import File

DATA = Path(__file__).resolve().parents[2] / 'seed_data'
DIRS = (DATA / 'files' / 'applicants-qabul', DATA / 'files-large' / 'applicants-qabul')


def _spec() -> dict:
    path = DATA / 'admission_pages.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def _file(name: str) -> Path | None:
    return next((d / name for d in DIRS if (d / name).exists()), None)


def seed_admission(Page, PageAttachment, Media) -> int:
    """Sahifalarni yaratadi (bor bo'lsa — tegmaydi) va yetishmagan hujjatlarni ulaydi. Qaytadi: ulangan PDF soni."""
    spec = _spec()
    group = Page.objects.filter(template='group', group_key='applicants').first()
    if not spec or not group:
        return 0
    g = spec['guide']
    guide = Page.objects.filter(slug=g['slug']).first() or Page.objects.create(
        slug=g['slug'], title=g['title'], body=g['body'], template='text', parent=group, in_menu=False,
        show_children=True, icon='clipboard-list', order=90)
    added = 0
    for order, (slug, s) in enumerate(spec['pages'].items(), start=1):
        p = Page.objects.filter(slug=slug).first() or Page.objects.create(
            slug=slug, title=s['title'], body=s['body'], template='text', parent=guide, in_menu=False, icon=s.get('icon', ''), order=order)
        have = {(a.title or {}).get('uz') for a in PageAttachment.objects.filter(page=p)}
        for n, d in enumerate(s['docs'], start=1):
            src = _file(d['file'])
            if d['title']['uz'] in have or not src:
                continue
            with src.open('rb') as fh:
                size = src.stat().st_size
                media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                media.file.save(f'{slug[:60]}-{n}.pdf', File(fh, name=f'{slug[:60]}-{n}.pdf'), save=False)
                media.save()
            PageAttachment.objects.create(page=p, file=media, url='', title=d['title'], meta=d.get('meta') or {},
                                          display=d.get('display') or 'embed', order=n)
            added += 1
    return added
