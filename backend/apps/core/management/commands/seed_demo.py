"""Boshlang'ich ma'lumotlar: saytdagi hozirgi (frontend mock) kontent, menyu daraxti, BRM, fakultetlar, namunaviy postlar.

Har bir bo'lim faqat bo'sh bo'lsa to'ldiriladi — buyruqni qayta ishga tushirish xavfsiz.
"""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.content.models import (
    Category, DocCategory, Document, Leader, Partner, Post, Slide, StateSymbol, TaughtLanguage, Video, VideoCategory,
    VideoPage,
)
from apps.core.fields import LANGS
from apps.core.models import Media, SiteSettings
from apps.hemis import get_client
from apps.pages.models import (
    Page, PageAttachment, PageFact, PageTimeline, SdgCategory, SdgGoal, SdgGoalReport, SdgOverviewReport, SdgPage, SdgSection,
)
from apps.structure.models import (
    FORM_LABELS, AdmissionDate, AdmissionFaq, AdmissionSettings, Campus, ContactEmail, Faculty, Program, ProgramGroup,
    StaffProfile,
)

DATA = Path(settings.BASE_DIR) / 'seed_data'
FILES = DATA / 'files'

# Saytda o'z sahifasi (Nuxt) bor bo'limlar — mazmuni admin panelning boshqa bo'limida
SPECIAL = re.compile(
    r'^/(aloqa|bakalavriat|brm|brm-[\w-]+|fakultetlar-va-kafedralar|magistratura|meyoriy-hujjatlar|qabul-20262027|'
    r'rektorat|staff|video-darsliklar|yangiliklar|news|announcements|events)$'
)
UZ_FORM = {v['uz']: k for k, v in FORM_LABELS.items()}


def load(name: str):
    with open(DATA / name, encoding='utf-8') as fh:
        return json.load(fh)


def i18n(value) -> dict:
    """Mock ma'lumotdagi qiymat → {uz, ru, en, zh}. Tillarga bo'linmagan qiymat — hamma tilda bir xil."""
    if isinstance(value, dict) and set(value) <= set(LANGS):
        return {k: v for k, v in value.items() if v}
    return {'uz': str(value)} if value not in (None, '') else {}


def lang_lines(items) -> dict:
    """[str | {uz,ru,en,zh}] → {lang: 'qator\\nqator'}."""
    out = {}
    for lang in LANGS:
        vals = [x if isinstance(x, str) else x.get(lang) or x.get('uz', '') for x in items]
        out[lang] = '\n'.join(v for v in vals if v)
    return out


def upload(path: Path, folder: str, alt: dict | None = None) -> Media:
    with open(path, 'rb') as fh:
        media = Media(folder=folder, alt=alt or {}, file=File(fh, name=path.name))
        media.save()
    return media


class Command(BaseCommand):
    help = 'Boshlang‘ich ma’lumotlarni yuklaydi (bo‘sh bo‘limlarga)'

    def add_arguments(self, parser):
        parser.add_argument('--first-run', action='store_true',
                            help='Faqat bo‘sh bazada (hali bitta ham foydalanuvchi yo‘q): admin biror bo‘limni o‘chirsa, keyingi ishga tushishda demo qaytib kelmasin')

    def handle(self, *args, first_run=False, **options):
        if first_run and User.objects.exists():
            self.stdout.write('Baza allaqachon ishlatilgan — namuna ma’lumot qayta yuklanmadi')
            return
        for step in (
            self.admin, self.site_settings, self.posts, self.content, self.pages, self.structure, self.sdg, self.staff,
        ):
            with transaction.atomic():
                step()
        self.stdout.write(self.style.SUCCESS('Tayyor'))

    def say(self, text: str):
        self.stdout.write(f'  {text}')

    # ─── Superadmin va sozlamalar ────────────────────────────────────────────

    def admin(self):
        if User.objects.exists():
            return
        username = os.environ.get('SUPERADMIN_USERNAME', 'superadmin')
        password = os.environ.get('SUPERADMIN_PASSWORD')
        if not password:
            self.stdout.write(self.style.WARNING('SUPERADMIN_PASSWORD .env faylida yo‘q — superadmin yaratilmadi'))
            return
        from django.conf import settings
        from apps.core.checks import WEAK_PASSWORDS
        if not settings.DEBUG and (password.lower() in WEAK_PASSWORDS or len(password) < 12):
            self.stdout.write(self.style.ERROR('SUPERADMIN_PASSWORD oddiy yoki 12 belgidan qisqa — productionda superadmin yaratilmadi. .env da kuchli parol qo‘ying.'))
            return
        User.objects.create_superuser(username=username, password=password, name=os.environ.get('SUPERADMIN_NAME', 'Superadmin'), role='superadmin')
        self.say(f'Superadmin yaratildi: {username}')

    def site_settings(self):
        s = SiteSettings.load()
        if s.name:
            return
        mock = load('mock-data.json')
        s.name = {
            'uz': 'Özbekiston davlat jahon tillari universiteti',
            'ru': 'Узбекский государственный университет мировых языков',
            'en': 'Uzbekistan State University of World Languages',
            'zh': '乌兹别克斯坦国立世界语言大学',
        }
        s.abbr = {'uz': 'ÖzDJTU', 'ru': 'УзГУМЯ', 'en': 'UzSWLU', 'zh': '世界语言大学'}
        s.address = i18n(mock['site']['campuses'][0]['address'])
        s.reception = {lang: mock['contact']['reception'] for lang in LANGS}
        s.support_text = {'uz': 'Texnik yordam', 'ru': 'Техподдержка', 'en': 'Tech support', 'zh': '技术支持'}
        s.x_url = next((x['url'] for x in mock['site']['socials'] if x['network'] == 'x'), '')
        s.instagram = next((x['url'] for x in mock['site']['socials'] if x['network'] == 'instagram'), '')
        s.facebook = next((x['url'] for x in mock['site']['socials'] if x['network'] == 'facebook'), '')
        # HEMIS ulanguncha saytdagi hozirgi raqamlar; ulangach — "HEMIS'dan avtomatik"ni yoqing
        s.numbers_auto = False
        for item in mock['home']['stats']:
            setattr(s, item['key'], item['value'])
        s.save()
        self.say('Sayt sozlamalari yuklandi')

    # ─── Postlar ─────────────────────────────────────────────────────────────

    def posts(self):
        if Post.objects.exists():
            return
        data = load('posts-seed.json')
        cats = {}
        for key, name in data['cats'].items():
            cats[name['uz']] = Category.objects.get_or_create(key=key, defaults={'name': name})[0]
        italian = data['italianBody']
        now = timezone.now()
        for i, s in enumerate(data['posts']):
            raw = s['date']
            at = datetime.fromisoformat(raw if 'T' in raw else f'{raw}T{9 + (i * 7) % 10:02d}:{(i * 23) % 60:02d}:00+05:00')
            paragraphs = s.get('body') or (italian if s['slug'] == 'italyan-tili-anjumani' else None)
            body = {lang: ''.join(f'<p>{p}</p>' for p in paragraphs.get(lang, [])) for lang in LANGS} if paragraphs else {}
            is_event = s['type'] == 'events'
            # tadbir e'loni bir hafta oldin chiqqan (lekin kelajakda emas)
            published = min(at - timedelta(days=7), now - timedelta(hours=1)) if is_event else at
            Post.objects.create(
                type=s['type'], slug=s['slug'], title=s['title'], excerpt=s.get('excerpt') or {}, body=body,
                tags={lang: '\n'.join(v) for lang, v in (s.get('tags') or {}).items()},
                location=s.get('location') or {}, category=cats[s['category']['uz']], sdg=s.get('sdg', 0),
                status='published', published_at=published, starts_at=at if is_event else None,
            )
        self.say(f'Namunaviy postlar yuklandi: {len(data["posts"])}')

    # ─── Karusel, rektorat, hujjatlar, videolar, ramzlar, hamkorlar ──────────

    def content(self):
        data = load('content-seed.json')
        mock = load('mock-data.json')

        if not Slide.objects.exists():
            for i, s in enumerate(data['slides'], start=1):
                alt = s['alt']
                media = upload(FILES / Path(s['image']).name, 'carousel', alt)
                Slide.objects.create(name=alt['uz'][:60], image=media, alt=alt, order=i)
            self.say('Karusel yuklandi')

        if not Leader.objects.exists():
            for i, d in enumerate(data['leaders'], start=1):
                Leader.objects.create(
                    kind=d['kind'], staff_id=d.get('staffId') or '', name=d['name'], role=d['role'], hours=d.get('hours') or {},
                    phone=d.get('phone') or '', ext=d.get('ext') or '', email=d.get('email') or '',
                    reception=d['kind'] != 'press', order=i,
                )
            self.say('Rektorat yuklandi')

        if not DocCategory.objects.exists():
            cats = {}
            for i, (key, title) in enumerate(data['docCategories'].items(), start=1):
                cats[key] = DocCategory.objects.create(title=title, order=i)
            # PDF fayllar hali yuklanmagan — eski saytdagi sahifaga havola bo'lib turadi (admin PDF yuklaguncha)
            for i, d in enumerate(data['docs'], start=1):
                Document.objects.create(title=d['title'], category=cats[d['category']], url=d['url'], display='open', order=i)
            self.say('Hujjatlar yuklandi')

        if not VideoCategory.objects.exists():
            cats = {}
            for i, c in enumerate(data['videoCategories'], start=1):
                cats[c['id']] = VideoCategory.objects.create(key=c['id'], title=c['title'], greeting=c['greeting'], order=i)
            # Darslar — NAMUNA (kanalga havola); admin haqiqiy YouTube videolari bilan almashtiradi
            for i, v in enumerate(data['lessons'], start=1):
                Video.objects.create(url=data['channel'], title=v['title'], category=cats[v['cat']], order=i)
            page = VideoPage.load()
            page.channel_url, page.live_url = data['channel'], f"{data['channel']}/live"
            page.save()
            self.say('Video darsliklar yuklandi')

        if not StateSymbol.objects.exists():
            alt = {
                'flag': {'uz': 'Özbekiston bayroği', 'ru': 'Флаг Узбекистана', 'en': 'Flag of Uzbekistan', 'zh': '乌兹别克斯坦国旗'},
                'emblem': {'uz': 'Özbekiston gerbi', 'ru': 'Герб Узбекистана', 'en': 'Emblem of Uzbekistan', 'zh': '乌兹别克斯坦国徽'},
            }
            specs = [
                ('flag', {'uz': 'Özbekiston Respublikasi davlat bayroği', 'ru': 'Государственный флаг Республики Узбекистан', 'en': 'State Flag of the Republic of Uzbekistan', 'zh': '乌兹别克斯坦共和国国旗'}, 'https://archive.uz/ozbekiston-respublikasining-davlat-bayrogi', 'archive.uz'),
                ('emblem', {'uz': 'Özbekiston Respublikasi davlat gerbi', 'ru': 'Государственный герб Республики Узбекистан', 'en': 'State Emblem of the Republic of Uzbekistan', 'zh': '乌兹别克斯坦共和国国徽'}, 'https://archive.uz/ozbekiston-respublikasi-davlat-gerbi', 'archive.uz'),
                ('anthem', {'uz': 'Özbekiston Respublikasi davlat madhiyasi', 'ru': 'Государственный гимн Республики Узбекистан', 'en': 'State Anthem of the Republic of Uzbekistan', 'zh': '乌兹别克斯坦共和国国歌'}, 'https://www.youtube.com/watch?v=rdOw_VSXbU4', 'YouTube'),
            ]
            for key, title, link, source in specs:
                image = upload(FILES / f'{key}.webp', 'logos', alt[key]) if key in alt else None
                StateSymbol.objects.create(key=key, title=title, link=link, source=source, image=image)
            self.say('Ramzlar yuklandi')

        if not TaughtLanguage.objects.exists():
            for i, lang in enumerate(mock['home']['languages'], start=1):
                TaughtLanguage.objects.create(code=lang['code'], native=lang['native'], order=i)

        if not Partner.objects.exists():
            for i, p in enumerate(mock['home']['partners'], start=1):
                logo = upload(FILES / 'partners' / Path(p['logo']).name, 'logos', i18n(p['name']))
                Partner.objects.create(name=i18n(p['name']), logo=logo, url=p.get('url') or '', order=i)
            self.say('Hamkorlar yuklandi')

    # ─── Sahifalar daraxti (menyu) ───────────────────────────────────────────

    def pages(self):
        if Page.objects.exists():
            return
        data = load('pages-seed.json')
        contents, sample, seen = data['pages'], data['sample'], set()
        for gi, g in enumerate(data['menu'], start=1):
            group = Page.objects.create(
                template='group', title=g['t'], group_key=g['id'], description=g.get('d') or {}, url=g.get('url') or '',
                overview=g.get('overview') or '', order=gi,
            )
            for li, link in enumerate(g['links'], start=1):
                url, slug = link['url'], link['url'].lstrip('/')
                base = {'title': link['t'], 'parent': group, 'order': li, 'highlight': bool(link.get('highlight')), 'sdg': link.get('sdg')}
                if re.match(r'^https?:', url):
                    Page.objects.create(**base, template='link', url=url)
                elif SPECIAL.match(url) or slug in seen:
                    Page.objects.create(**base, template='special', url=url)
                else:
                    seen.add(slug)
                    c = contents.get(slug, {})
                    page = Page.objects.create(**base, template='text', slug=slug, lead=c.get('lead') or {}, body=c.get('body') or sample)
                    for k, (value, label) in enumerate(c.get('facts') or [], start=1):
                        PageFact.objects.create(page=page, value=value, label=label, order=k)
                    for k, row in enumerate(c.get('timeline') or [], start=1):
                        PageTimeline.objects.create(page=page, label=row[0], text=row[1], highlight=bool(row[2]) if len(row) > 2 else False, order=k)
                    for k, a in enumerate(c.get('attachments') or [], start=1):
                        PageAttachment.objects.create(page=page, url=a['url'], title=a['title'], meta=a.get('meta') or {}, display='open', order=k)
        self.say('Sahifalar daraxti yuklandi')

    # ─── Fakultetlar, yo'nalishlar, qabul, aloqa ─────────────────────────────

    def structure(self):
        mock = load('mock-data.json')
        client = get_client()

        if not Faculty.objects.exists():
            for f in client.faculties():
                logo = upload(FILES / 'faculties' / Path(f['logo']).name, 'logos', f['name']) if f.get('logo') else None
                Faculty.objects.create(slug=f['slug'], name=f['name'], logo=logo, order=f['order'])
            self.say('Fakultetlar yuklandi')

        if not Program.objects.exists():
            langs = {x.code: x for x in TaughtLanguage.objects.all()}
            for level in ('bachelor', 'master'):
                block = mock['programs'][level]
                groups = {
                    g['id']: ProgramGroup.objects.create(key=g['id'], level=level, title=i18n(g['title']), order=i)
                    for i, g in enumerate(block['groups'], start=1)
                }
                for i, p in enumerate(block['items'], start=1):
                    Program.objects.create(
                        code=p['code'], title=i18n(p['title']), level=level, group=groups.get(p['group']),
                        language=langs.get((p.get('language') or {}).get('code')), form=UZ_FORM.get(i18n(p['form']).get('uz'), 'day'),
                        years=p['years'], order=i,
                    )
            # Qabul sahifasidagi yo'nalishlar: mavjud yozuv belgilanadi, yo'q bo'lsa (masalan PhD) yangi yaratiladi
            faculties = {f.name.get('uz'): f for f in Faculty.objects.all()}
            for i, p in enumerate(mock['admission']['programs'], start=1):
                form = UZ_FORM.get(i18n(p['form']).get('uz'), 'day')
                found = Program.objects.filter(code=p['code'], level=p['level'], form=form).first()
                if not found:
                    found = Program(code=p['code'], title=i18n(p['title']), level=p['level'], form=form, years=p['years'], order=100 + i)
                found.faculty = faculties.get(i18n(p['faculty']).get('uz'))
                found.in_admission = True
                found.price = i18n(p.get('price'))
                found.save()
            self.say('Ta’lim yo‘nalishlari yuklandi')

        adm = AdmissionSettings.load()
        if not adm.dates.exists():
            a = mock['admission']
            adm.year, adm.apply_url = a['year'], a['applyUrl']
            adm.documents = lang_lines(a['documents'])
            adm.documents_url = a.get('documentsUrl') or ''
            adm.address, adm.hours = i18n(a['contact']['address']), i18n(a['contact']['hours'])
            adm.phone, adm.telegram = a['contact']['phone'], a['contact']['telegram']
            adm.save()
            for i, d in enumerate(a['dates'], start=1):
                AdmissionDate.objects.create(admission=adm, title=i18n(d['title']), period=i18n(d['period']), current=bool(d.get('current')), order=i)
            for i, x in enumerate(a['faq'], start=1):
                AdmissionFaq.objects.create(admission=adm, question=i18n(x['q']), answer=i18n(x['a']), order=i)
            self.say('Qabul sahifasi yuklandi')

        if not Campus.objects.exists():
            for i, c in enumerate(mock['contact']['campuses'], start=1):
                Campus.objects.create(key=c['id'], name=i18n(c['name']), address=i18n(c['address']), phone=c.get('phone') or '', map_url=c.get('mapUrl') or '', order=i)
            for i, e in enumerate(mock['contact']['emails'], start=1):
                ContactEmail.objects.create(title=i18n(e['title']), value=e['value'], extra=lang_lines(e['extra']), order=i)
            self.say('Aloqa ma’lumotlari yuklandi')

    # ─── BRM ─────────────────────────────────────────────────────────────────

    def sdg(self):
        data = load('sdg-seed.json')
        mock = load('mock-data.json')['sdg']

        if not SdgGoal.objects.exists():
            for g in data['goals']:
                h = g.get('highlight') or {}
                goal = SdgGoal.objects.create(
                    n=g['n'], url=g['url'], title=g['title'], subtitle=g['subtitle'], impact_rank=g.get('impactRank') or '',
                    impact_score=g.get('impactScore') or '', highlight_label=h.get('label', ''), highlight_value=h.get('value') or {},
                )
                for i, s in enumerate(g['sections'], start=1):
                    SdgSection.objects.create(goal=goal, key=s.get('key') or '', title=s['title'], body=s.get('body') or {}, order=i)
                for i, r in enumerate(g['reports'], start=1):
                    SdgGoalReport.objects.create(goal=goal, url=r['url'], title=i18n(r['title']), meta=i18n(r.get('meta')), display='open', order=i)
            self.say('BRM maqsadlari yuklandi')

        page = SdgPage.load()
        if not page.categories.exists():
            gm = mock['greenmetric']
            page.impact_year = data['impactYear']
            page.gm_year = gm['year']
            page.gm_world_rank, page.gm_world_change = gm['world']['rank'], gm['world']['change']
            page.gm_asia_rank, page.gm_asia_change = gm['asia']['rank'], gm['asia']['change']
            page.gm_country_rank, page.gm_country_change = gm['country']['rank'], gm['country']['change']
            page.gm_highlight_text, page.gm_highlight_url = i18n(gm['highlight']['text']), gm['highlight']['url']
            edu = mock['education']
            page.education_title, page.education_text = i18n(edu['title']), i18n(edu['text'])
            page.education_tags, page.education_url = lang_lines(edu['tags']), edu['url']
            page.save()
            for i, c in enumerate(mock['categories'], start=1):
                SdgCategory.objects.create(page=page, code=c['code'], title=i18n(c['title']), subtitle=c.get('subtitle') or '', badge=i18n(c.get('badge')), url=c['url'], order=i)
            for i, r in enumerate(mock['reports'], start=1):
                SdgOverviewReport.objects.create(page=page, url=r['url'], title=i18n(r['title']), display='open', order=i)
            self.say('BRM bosh sahifasi yuklandi')

    # ─── Xodim profillari (kabinetda to'ldirilgan namunalar) ─────────────────

    def staff(self):
        if StaffProfile.objects.exists():
            return
        extras = load('staff-extras.json')
        names = {str(p['id']): p['name'] for p in get_client().staff('uz')}
        for hemis_id, e in extras.items():
            # Namunadagi shaxsiy mobil/WhatsApp raqamlar yuklanmaydi (ular haqiqiy emas)
            contacts = [c for c in e.get('contacts', []) if c['type'] not in ('mobile', 'whatsapp')]
            StaffProfile.objects.create(
                hemis_id=hemis_id, name=names.get(hemis_id, ''), about=e.get('about') or {}, contacts=contacts,
                socials=e.get('socials') or [], science=e.get('science') or [],
            )
        self.say('Xodim profillari yuklandi')
