"""Eski saytdan (uzswlu.uz) «Xalqaro akkreditatsiya» bo'limi hujjatlarini import qilish.

    python manage.py import_accreditation            # yuklab, sahifalarga biriktiradi
    python manage.py import_accreditation --dry-run  # faqat ro'yxat: qaysi sahifada nechta hujjat, qaysilari yo'q (404)
    python manage.py import_accreditation --mirror /tmp/acc  # internet o'rniga oldindan yuklangan nusxadan

Server eski saytga chiqa olmasa: sahifalar va fayllar boshqa kompyuterda papkaga yuklanadi (nomi — `mirror_name(url)`,
masalan `ru_curriculum`, `backend_web_uploads_pagepdf_icon_123.pdf`), papka serverga ko'chiriladi va `--mirror` bilan beriladi.

Bo'lim daraxtidagi har bir sahifa (slug eski saytdagi bilan bir xil) uz/ru/en tillarda ochiladi, «PDF lar» ro'yxatidagi
hujjatlar (PDF, Word, Excel) olinadi: fayl `Media` (papka «Hujjatlar») ga yuklanadi, sahifaga 4 tilda nomi bilan
biriktiriladi (xitoychasi — inglizcha nomi). Takror ishga tushirish xavfsiz: shu eski fayl sahifaga avval yuklangan bo'lsa o'tkaziladi.
Eski saytda ochilmaydigan (404) fayllar o'tkazib yuboriladi va oxirida ro'yxati chiqadi.
"""
import html
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify as dj_slugify

from apps.core.alphabet import to_new_alphabet as N
from apps.core.models import DOC_EXT, Media
from apps.pages.models import Page, PageAttachment

BASE = 'https://uzswlu.uz'
ROOT = 'xalqaro-akkreditatsiya'
UA = 'Mozilla/5.0 (compatible; uzswlu-import/1.0)'
# Eski sayt «PDF lar» bloki: <div class="notify-item"> … <h6>Nomi</h6> … <a href="…/pagepdf/icon/123.pdf">
DOC_RE = re.compile(r'<h6[^>]*>(.*?)</h6>.*?href="([^"]*pagepdf/icon/([^"/]+))"', re.S)
TAG_RE = re.compile(r'<[^>]+>')
MAX_BYTES = 120 * 1024 * 1024


MIRROR: Path | None = None


def mirror_name(url: str) -> str:
    """Nusxa papkasidagi fayl nomi: manzil yo'li, belgilar «_» bilan (https://uzswlu.uz/ru/curriculum → ru_curriculum)."""
    path = urllib.parse.unquote(url.removeprefix(BASE).lstrip('/'))
    return re.sub(r'[^A-Za-z0-9._-]', '_', path)[:200]


def fetch(url: str, timeout: int = 60) -> bytes:
    if MIRROR is not None:
        f = MIRROR / mirror_name(url)
        if not f.exists():
            raise urllib.error.URLError('nusxada yo‘q')
        return f.read_bytes()
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — manzil doimiy (uzswlu.uz)
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('fayl juda katta')
    return data


def page_docs(slug: str, lang: str) -> list[tuple[str, str]]:
    """Eski sahifadagi hujjatlar: [(nomi, fayl nomi)], sahifadagi tartibda."""
    try:
        text = fetch(f'{BASE}/{lang}/{urllib.parse.quote(slug)}', timeout=40).decode('utf-8', 'replace')
    except (urllib.error.URLError, TimeoutError, ValueError):
        return []
    start = text.find('col-lg-9 col-md-12')
    text = text[start:] if start >= 0 else text
    out = []
    for title, _href, name in DOC_RE.findall(text):
        title = re.sub(r'\s+', ' ', html.unescape(TAG_RE.sub('', title))).strip()
        out.append((title, urllib.parse.unquote(name)))
    return out


class Command(BaseCommand):
    help = "Eski saytdan «Xalqaro akkreditatsiya» bo'limi hujjatlarini (PDF, Word, Excel) sahifalarga import qiladi"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Yuklamasdan faqat ro‘yxatni ko‘rsatish')
        parser.add_argument('--root', default=ROOT, help='Bo‘lim ildiz sahifasi (slug)')
        parser.add_argument('--mirror', help='Internet o‘rniga oldindan yuklangan nusxa papkasi')

    def handle(self, *args, dry_run=False, root=ROOT, mirror=None, **opts):
        global MIRROR
        MIRROR = Path(mirror) if mirror else None
        top = Page.objects.filter(slug=root).first()
        if not top:
            self.stderr.write(f'«{root}» sahifasi topilmadi')
            return
        pages, queue = [], [top]
        while queue:
            p = queue.pop(0)
            pages.append(p)
            queue.extend(p.children.exclude(slug=None).order_by('order', 'id'))

        added = skipped = 0
        missing: list[str] = []
        for page in pages:
            uz = page_docs(page.slug, 'uz')
            if not uz:
                continue
            ru, en = page_docs(page.slug, 'ru'), page_docs(page.slug, 'en')
            # Avval import qilingan fayllar (Media nomi «<slug>-<eski fayl>-<uuid>.ext» — eski fayl nomi bo'yicha tekshiriladi)
            have = {a.file.file.name.rsplit('/', 1)[-1].rsplit('-', 1)[0] for a in page.attachments.select_related('file') if a.file_id}
            order = page.attachments.count()
            self.stdout.write(f'{page.slug}: {len(uz)} ta hujjat')
            for i, (title_uz, name) in enumerate(uz):
                title = {
                    'uz': N(title_uz),
                    'ru': ru[i][0] if len(ru) == len(uz) else title_uz,
                    'en': en[i][0] if len(en) == len(uz) else title_uz,
                }
                title['zh'] = title['en']
                key = dj_slugify(f'{page.slug[:40]}-{name.rsplit(".", 1)[0]}')[:60]
                if key in have:
                    skipped += 1
                    continue
                ext = ('.' + name.rsplit('.', 1)[-1].lower()) if '.' in name else ''
                if ext != '.pdf' and ext not in DOC_EXT:
                    missing.append(f'{page.slug}: {title_uz} ({name}) — fayl turi qo‘llanmaydi')
                    continue
                if dry_run:
                    added += 1
                    continue
                try:
                    data = fetch(f'{BASE}/backend/web/uploads/pagepdf/icon/{urllib.parse.quote(name)}', timeout=300)
                except (urllib.error.URLError, TimeoutError, ValueError) as e:
                    missing.append(f'{page.slug}: {title_uz} ({name}) — {getattr(e, "code", e)}')
                    continue
                media = Media(folder='docs', kind='pdf' if ext == '.pdf' else 'doc', filesize=len(data),
                              original_size=len(data), alt={}, sizes={})
                media.file.save(f'{page.slug[:40]}-{name}', ContentFile(data), save=False)
                media.save()
                order += 1
                PageAttachment.objects.create(page=page, file=media, url='', title=title, meta={},
                                              display='open', order=order)
                have.add(key)
                added += 1
                if MIRROR is None:
                    time.sleep(0.2)  # eski serverni zo'riqtirmaslik uchun
        verb = 'qo‘shiladi' if dry_run else 'qo‘shildi'
        self.stdout.write(self.style.SUCCESS(f'Hujjatlar: {added} ta {verb}, {skipped} ta avval bor edi, {len(missing)} ta olinmadi'))
        for line in missing:
            self.stdout.write(f'  ✗ {line}')
