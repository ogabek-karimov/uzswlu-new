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
            if s['root']:  # bölim sahifasi (menyuda) seed'da yaratiladi — bu yerda faqat mavjudi yangilanadi
                continue
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


# ─── BRM 1–17 (seed_data/brm_goals.json): ichki bölimlar (tablar) va hujjatlar ───────────────────
BRM_FILES = DATA / 'files-large' / 'brm'
SDG_PLACEHOLDER = 'namunaviy matn'


def brm_specs() -> list[dict]:
    path = DATA / 'brm_goals.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []


def seed_goals(SdgGoal, SdgSection) -> None:
    """Faqat hali namunaviy holatdagi maqsadlar yangilanadi (admin kiritgan matnga tegilmaydi)."""
    for s in brm_specs():
        g = SdgGoal.objects.filter(n=s['n']).first()
        if not g:
            continue
        secs = list(g.sections.all())
        if any(SDG_PLACEHOLDER not in str((x.body or {}).get('uz', '')) for x in secs):
            continue
        if g.reports.exclude(file__isnull=True).exists() or g.reports.exclude(url__startswith='https://uzswlu.uz/brm').exists():
            continue
        g.sections.all().delete()
        g.reports.all().delete()
        for i, x in enumerate(s['sections']):
            SdgSection.objects.create(goal=g, key=x['key'], title=x['title'], body=x['body'], order=i)


def seed_goal_files(SdgGoal, SdgGoalReport, Media, files: Path = BRM_FILES) -> int:
    added = 0
    for s in brm_specs():
        g = SdgGoal.objects.filter(n=s['n']).first()
        if not g or not set(g.sections.values_list('key', flat=True)) >= {x['key'] for x in s['sections']}:
            continue
        items = [(x['key'], d) for x in s['sections'] for d in x['docs']] + [('', d) for d in s['docs']]
        for n, (key, (fname, title)) in enumerate(items, start=1):
            src = files / fname
            if not src.exists() or g.reports.filter(order=n).exists():
                continue
            name = f'brm-{s["n"]}-{n}.pdf'
            with src.open('rb') as fh:
                size = src.stat().st_size
                m = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                m.file.save(name, File(fh, name=name), save=False)
                m.save()
            SdgGoalReport.objects.create(goal=g, file=m, url='', title=title, meta={}, display='open', order=n, section=key)
            added += 1
    return added


# ─── Universitet nizomi: menyudagi havola eski saytdagi PDF'ga olib borardi — fayl o'zimizga ───────────────
NIZOM = DATA / 'files-large' / 'docs' / 'ozdjtu-nizomi.pdf'


def seed_nizom(Page, Media, path: Path = NIZOM) -> bool:
    p = Page.objects.filter(template='link', file__isnull=True, url__icontains='nizomi.pdf').first()
    if not p or not path.exists():
        return False
    with path.open('rb') as fh:
        size = path.stat().st_size
        m = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
        m.file.save('ozdjtu-nizomi.pdf', File(fh, name='ozdjtu-nizomi.pdf'), save=False)
        m.save()
    p.file, p.url = m, ''
    p.save(update_fields=['file', 'url'])
    return True
