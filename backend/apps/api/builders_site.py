"""Ochiq sayt API'si javoblarini yig'ish (frontend/docs/openapi.yaml shartnomasi)."""
import re
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.content.models import (
    Document, DocCategory, Leader, Partner, Post, Slide, StateSymbol, TaughtLanguage, Video, VideoCategory, VideoPage,
)
from apps.core.fields import pick, tr
from apps.core.html import restore_timeline, text_of
from apps.core.models import SiteSettings
from apps.core.utils import local_date, size_label
from apps.hemis import get_client
from apps.pages.models import Page, SdgGoal, SdgPage
from apps.structure.models import (
    FORM_LABELS, AdmissionSettings, Campus, ContactEmail, Faculty, Program, ProgramGroup,
)

from .builders import (
    POST_RELATED, announcement_item, event_item, latest_posts, news_item, post_summary, upcoming_events,
)
from .common import attachments_out, img, iso, lines

TASHKENT = ZoneInfo('Asia/Tashkent')


# ─── Bosh sahifa va umumiy ma'lumot ──────────────────────────────────────────

def slides_out(lang: str) -> list[dict]:
    out = []
    for s in Slide.active():
        image = img(s.image, 'hero')
        if image:
            out.append({'id': str(s.pk), 'image': image, 'alt': tr(s.alt, lang), 'link': s.link or None})
    return out


STAT_KEYS = ('faculties', 'staff', 'departments', 'students')


def stats_out() -> list[dict]:
    s = SiteSettings.load()
    manual = {k: getattr(s, k) for k in STAT_KEYS}
    auto: dict = {}
    if s.numbers_auto or any(v is None for v in manual.values()):
        client = get_client()
        summary = client.summary()
        auto = {
            'faculties': summary['faculties'],
            'departments': summary['departments'],
            'students': sum(f['stats']['students'] for f in client.faculties()),
            'staff': len(client.staff('uz')),
        }
    return [
        {'key': k, 'value': int(auto[k] if (s.numbers_auto or manual[k] is None) else manual[k])}
        for k in STAT_KEYS
    ]


def faculties_brief(lang: str) -> list[dict]:
    return [
        {'id': str(f.pk), 'slug': f.slug, 'name': tr(f.name, lang), 'logo': img(f.logo, 'thumb')}
        for f in Faculty.objects.select_related('logo')
    ]


def languages_out() -> list[dict]:
    """O'qitiladigan tillar; har biri uchun shu tilda o'qitiladigan yo'nalishlar va ularni olib boruvchi fakultetlar soni."""
    counts = {
        r['language_id']: r
        for r in Program.objects.filter(language__isnull=False)
        .values('language_id')
        .annotate(programs=Count('id'), faculties=Count('faculty', distinct=True))
    }
    return [
        {
            'code': x.code,
            'native': x.native,
            'programs': counts.get(x.pk, {}).get('programs', 0),
            'faculties': counts.get(x.pk, {}).get('faculties', 0),
        }
        for x in TaughtLanguage.objects.all()
    ]


def home_out(lang: str) -> dict:
    synced = get_client().synced_at()
    if synced and timezone.is_naive(synced):
        synced = timezone.make_aware(synced, TASHKENT)
    return {
        'slides': slides_out(lang),
        'stats': stats_out(),
        'faculties': faculties_brief(lang),
        'news': [news_item(p, lang) for p in latest_posts(lang, 'news', 4)],
        'announcements': [announcement_item(p, lang) for p in latest_posts(lang, 'announcements', 4)],
        'events': [event_item(p, lang) for p in upcoming_events(lang, 3)],
        'languages': languages_out(),
        'partners': [
            {'id': str(p.pk), 'name': tr(p.name, lang), 'logo': img(p.logo, 'card'), 'url': p.url or None}
            for p in Partner.objects.select_related('logo')
        ],
        'updatedAt': iso(synced or timezone.now()),
    }


def menu_out(lang: str) -> list[dict]:
    pages = list(Page.objects.filter(published=True, in_menu=True).select_related('file').order_by('order', 'id'))
    children: dict = defaultdict(list)
    for p in pages:
        children[p.parent_id].append(p)

    def flatten(pid) -> list[Page]:
        out: list[Page] = []
        for p in children.get(pid, []):
            out.append(p)
            out.extend(flatten(p.pk))
        return out

    menu = []
    for g in children.get(None, []):
        if g.template != 'group':
            continue
        links = []
        for p in flatten(g.pk):
            if p.template == 'group':
                continue
            url = p.site_url
            links.append({
                'title': tr(p.title, lang),
                'url': url,
                'file': 'pdf' if p.template == 'link' and (p.file_id or re.search(r'\.pdf($|\?)', url, re.I)) else None,
                'highlight': p.highlight,
                'sdg': p.sdg or None,
            })
        menu.append({
            'id': g.group_key or g.slug or str(g.pk),
            'title': tr(g.title, lang),
            'description': tr(g.description, lang) or None,
            'url': g.url or None,
            'overview': g.overview or None,
            'links': links,
        })
    return menu


def symbols_out(lang: str) -> list[dict]:
    order = {'flag': 0, 'emblem': 1, 'anthem': 2}
    items = sorted(StateSymbol.objects.select_related('image', 'audio'), key=lambda s: order.get(s.key, 9))
    return [
        {
            'key': s.key,
            'title': tr(s.title, lang),
            'description': tr(s.description, lang) or None,
            'image': img(s.image, 'thumb'),
            'audio': s.audio.url if s.key == 'anthem' and s.audio_id else None,
            'href': s.link or None,
            'source': s.source or None,
        }
        for s in items
    ]


def site_out(lang: str) -> dict:
    s = SiteSettings.load()
    socials = [
        {'network': net, 'url': url}
        for net, url in (('telegram', s.telegram), ('instagram', s.instagram), ('facebook', s.facebook), ('youtube', s.youtube), ('x', s.x_url))
        if url
    ]
    return {
        'menu': menu_out(lang),
        'phone': s.phone,
        'phoneExt': s.phone_ext,
        'emails': [e.value for e in ContactEmail.objects.all()],
        'campuses': [{'id': c.key, 'name': tr(c.name, lang), 'address': tr(c.address, lang)} for c in Campus.objects.all()],
        'socials': socials,
        'symbols': symbols_out(lang) or None,
    }


def settings_out(lang: str) -> dict:
    """Payload bilan mos: /site/settings (texnik yordam tugmasi va aloqa)."""
    s = SiteSettings.load()
    return {
        'support': {
            'url': s.support_telegram or None,
            'text': pick(s.support_text, lang),
            'showOnSite': s.support_show_on_site,
            'pages': [x.strip() for x in s.support_pages.split(',') if x.strip()],
            'place': s.support_place,
        },
        'contact': {'phone': s.phone or None, 'email': None, 'address': pick(s.address, lang)},
    }


# ─── Matnli sahifalar ────────────────────────────────────────────────────────

def page_out(p: Page, lang: str) -> dict:
    return {
        'slug': p.slug,
        'title': tr(p.title, lang),
        'lead': tr(p.lead, lang) or None,
        'facts': [{'value': f.value, 'label': tr(f.label, lang)} for f in p.facts.all()],
        'body': restore_timeline(tr(p.body, lang)),
        'timeline': [{'label': tr(t.label, lang), 'text': tr(t.text, lang), 'highlight': t.highlight} for t in p.timeline.all()],
        'attachments': attachments_out(p.attachments.select_related('file'), lang),
        'updatedAt': iso(p.updated_at),
    }


# ─── Postlar ─────────────────────────────────────────────────────────────────

POST_TYPES = ('news', 'announcements', 'events')


def month_range(month: str) -> tuple[datetime, datetime]:
    y, m = int(month[:4]), int(month[5:7])
    start = datetime(y, m, 1, tzinfo=TASHKENT)
    end = datetime(y + (m == 12), 1 if m == 12 else m + 1, 1, tzinfo=TASHKENT)
    return start, end


def current_month() -> str:
    return timezone.localtime().strftime('%Y-%m')


def posts_list_out(lang: str, *, type_: str, q: str, month: str | None, sdg: int, page: int, per_page: int) -> dict:
    from django.db.models import Q

    base = Post.visible(lang)
    if q:
        base = base.filter(Q(**{f'title__{lang}__icontains': q}) | Q(**{f'excerpt__{lang}__icontains': q}) | Q(**{f'body__{lang}__icontains': q}))
    if 1 <= sdg <= 17:
        base = base.filter(sdg=sdg)
    if month and re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month):
        start, end = month_range(month)
        base = base.filter(published_at__gte=start, published_at__lt=end)

    counts = {t: base.filter(type=t).count() for t in POST_TYPES}
    rows = base.filter(type=type_).select_related(*POST_RELATED).order_by('-published_at', '-id')
    offset = (page - 1) * per_page

    months_qs = (
        Post.visible(lang).filter(type=type_).order_by().annotate(m=TruncMonth('published_at', tzinfo=TASHKENT))
        .values_list('m', flat=True).distinct()
    )
    months = sorted({m.strftime('%Y-%m') for m in months_qs if m}, reverse=True)

    return {
        'items': [post_summary(p, lang) for p in rows[offset:offset + per_page]],
        'total': counts[type_],
        'page': page,
        'perPage': per_page,
        'counts': counts,
        'months': months,
    }


def events_out(lang: str, month: str) -> dict:
    start, end = month_range(month)
    in_month = (
        Post.visible(lang).filter(type='events', starts_at__gte=start, starts_at__lt=end)
        .select_related(*POST_RELATED).order_by('starts_at')[:200]
    )
    return {
        'month': month,
        'items': [event_item(p, lang) for p in in_month],
        'upcoming': [event_item(p, lang) for p in upcoming_events(lang, 3)],
    }


def post_index_out(lang: str) -> list[dict]:
    """Payload bilan mos: /site/index — qidiruv uchun yengil ro'yxat."""
    rows = Post.visible(lang).select_related('category').defer('body').order_by('-published_at')[:1000]
    return [
        {
            'type': p.type, 'slug': p.slug, 'title': tr(p.title, lang), 'text': pick(p.excerpt, lang) or '',
            'category': tr(p.category.name, lang) if p.category else '', 'date': iso(p.published_at),
        }
        for p in rows
    ]


# ─── Rektorat, hujjatlar, videolar ───────────────────────────────────────────

def leader_out(d: Leader, lang: str) -> dict:
    return {
        'staffId': d.staff_id or None,
        'name': d.name,
        'role': tr(d.role, lang),
        'photo': img(d.photo, 'thumb'),
        'hours': tr(d.hours, lang) or None,
        'phone': d.phone or None,
        'ext': d.ext or None,
        'email': d.email or None,
    }


def leadership_out(lang: str) -> dict:
    docs = list(Leader.objects.select_related('photo'))
    rector = next((d for d in docs if d.kind == 'rector'), None)
    press = next((d for d in docs if d.kind == 'press'), None)
    return {
        'rector': leader_out(rector, lang) if rector else None,
        'prorectors': [leader_out(d, lang) for d in docs if d.kind == 'prorector'],
        'press': leader_out(press, lang) if press else None,
        'recipients': [{'id': f'leader-{d.pk}', 'title': tr(d.role, lang)} for d in docs if d.reception],
    }


def document_item(d: Document, lang: str) -> dict | None:
    file = d.file_for(lang)
    is_file = bool(file)
    url = f'{settings.PUBLIC_SERVER_URL}/api/documents/{d.pk}/file?lang={lang}' if is_file else d.url
    if not url:
        return None
    file_meta = ' · '.join(x for x in ('PDF', size_label(file.filesize) if file else None) if x) if is_file else None
    return {
        'id': str(d.pk),
        'category': str(d.category_id),
        'title': tr(d.title, lang),
        'url': url,
        'kind': 'pdf' if is_file else 'link',
        'meta': ' · '.join(x for x in (d.number, file_meta) if x) or None,
        'display': d.display if is_file else None,
        'height': d.height if is_file and d.display == 'embed' else None,
    }


def documents_out(lang: str, page: str | None = None) -> dict:
    docs = Document.objects.select_related('file_uz', 'file_ru', 'file_en', 'file_zh')
    items = [d for d in docs if not page or page in d.page_list]
    return {
        'categories': [{'id': str(c.pk), 'title': tr(c.title, lang)} for c in DocCategory.objects.all()],
        'items': [x for x in (document_item(d, lang) for d in items) if x],
    }


def videos_out(lang: str) -> dict:
    page = VideoPage.load()
    channel = page.channel_url or 'https://www.youtube.com'
    categories = list(VideoCategory.objects.all())
    return {
        'live': {
            'isLive': page.live,
            'url': page.live_url or f"{channel.rstrip('/')}/live",
            'next': {'title': tr(page.next_title, lang), 'startsAt': iso(page.next_at)} if page.next_at and page.next_at > timezone.now() else None,
        },
        'channelUrl': channel,
        'categories': [{'id': c.key, 'title': tr(c.title, lang), 'greeting': c.greeting, 'lang': c.key} for c in categories],
        'items': [
            {
                'id': str(v.pk), 'category': v.category.key, 'title': tr(v.title, lang), 'teacher': v.teacher or None,
                'duration': v.duration or None, 'url': v.url, 'thumbnail': v.thumbnail or None,
            }
            for v in Video.objects.select_related('category')
        ],
    }


# ─── Ta'lim: yo'nalishlar, fakultetlar, qabul ────────────────────────────────

def form_label(form: str, lang: str) -> str:
    return tr(FORM_LABELS.get(form, {}), lang)


def programs_out(lang: str, level: str) -> dict:
    return {
        'level': level,
        'groups': [{'id': g.key, 'title': tr(g.title, lang)} for g in ProgramGroup.objects.filter(level=level)],
        'items': [
            {
                'id': str(p.pk),
                'code': p.code,
                'title': tr(p.title, lang),
                'language': {'code': p.language.code, 'native': p.language.native} if p.language else None,
                'group': p.group.key if p.group else '',
                'form': form_label(p.form, lang),
                'years': p.years,
            }
            for p in Program.objects.filter(level=level).select_related('group', 'language')
        ],
    }


def faculties_out(lang: str) -> dict:
    client = get_client()
    items = []
    for f in Faculty.objects.select_related('logo').annotate(program_count=Count('programs')):
        h = client.faculty(f.slug)
        items.append({
            'id': str(f.pk),
            'slug': f.slug,
            'name': tr(f.name, lang),
            'logo': img(f.logo, 'thumb'),
            'departments': h['stats']['departments'] if h else 0,
            'programs': h['stats']['programs'] if h else f.program_count,
        })
    return {'items': items, 'summary': {'faculties': len(items), 'departments': client.summary()['departments']}}


def _by_lang(value, lang: str, default):
    if not isinstance(value, dict):
        return default
    return value.get(lang) or value.get('uz') or default


def faculty_out(f: Faculty, lang: str) -> dict:
    from apps.structure.models import Department

    h = get_client().faculty(f.slug)
    numbered = list(Faculty.objects.values_list('pk', flat=True))
    own = {d.hemis_id: d for d in Department.objects.filter(hemis_id__in=[d['id'] for d in (h or {}).get('departments', [])])}
    contact = _by_lang((h or {}).get('contact'), lang, {})
    programs = _by_lang((h or {}).get('programs'), lang, []) or [
        {'code': p.code, 'title': tr(p.title, lang), 'level': p.level, 'form': form_label(p.form, lang), 'years': p.years}
        for p in f.programs.all()
    ]
    return {
        'id': str(f.pk),
        'slug': f.slug,
        'name': tr(f.name, lang),
        'logo': img(f.logo, 'thumb'),
        'number': numbered.index(f.pk) + 1,
        'about': tr(f.about, lang) or _by_lang((h or {}).get('about'), lang, ''),
        'stats': (h or {}).get('stats') or {'students': 0, 'departments': 0, 'programs': 0, 'teachers': 0},
        'dean': _by_lang((h or {}).get('dean'), lang, {'name': '', 'role': ''}),
        'programs': programs,
        'departments': [
            {'id': d['id'], 'name': tr(own[d['id']].name, lang) if d['id'] in own and own[d['id']].name else _by_lang(d.get('name'), lang, ''), 'head': d.get('head')}
            for d in (h or {}).get('departments', [])
        ],
        'deanery': _by_lang((h or {}).get('deanery'), lang, []),
        'news': [post_summary(p, lang) for p in latest_posts(lang, 'news', 2)],
        'contact': {
            'address': tr(f.address, lang) or contact.get('address', ''),
            'phone': f.phone or contact.get('phone', ''),
            'email': f.email or contact.get('email') or None,
            'mapUrl': f.map_url or contact.get('mapUrl') or None,
        },
    }


def admission_out(lang: str) -> dict:
    a = AdmissionSettings.load()
    return {
        'year': a.year,
        'applyUrl': a.apply_url,
        'dates': [
            {'title': tr(d.title, lang), 'period': tr(d.period, lang), 'current': d.current}
            for d in a.dates.all()
        ],
        'programs': [
            {
                'id': str(p.pk), 'code': p.code, 'title': tr(p.title, lang),
                'faculty': tr(p.faculty.name, lang) if p.faculty else '',
                'level': p.level, 'form': form_label(p.form, lang), 'years': p.years,
                'price': tr(p.price, lang) or None,
            }
            for p in Program.objects.filter(in_admission=True).select_related('faculty')
        ],
        'documents': lines(a.documents, lang),
        'documentsUrl': a.documents_url or None,
        'faq': [{'q': tr(x.question, lang), 'a': tr(x.answer, lang)} for x in a.faq.all()],
        'contact': {'address': tr(a.address, lang), 'hours': tr(a.hours, lang), 'phone': a.phone, 'telegram': a.telegram},
    }


# ─── BRM ─────────────────────────────────────────────────────────────────────

def sdg_summary(g: SdgGoal, lang: str) -> dict:
    return {'n': g.n, 'url': g.url, 'title': tr(g.title, lang), 'rank': g.impact_rank or None, 'score': g.impact_score or None}


def sdg_goals_out(lang: str) -> dict:
    return {'impactYear': SdgPage.load().impact_year, 'goals': [sdg_summary(g, lang) for g in SdgGoal.objects.all()]}


def sdg_overview_out(lang: str) -> dict:
    p = SdgPage.load()
    highlight = tr(p.gm_highlight_text, lang)
    news = Post.visible(lang).filter(type='news', sdg__gt=0).select_related(*POST_RELATED).order_by('-published_at')[:3]
    return {
        'greenmetric': {
            'year': p.gm_year,
            'world': {'rank': p.gm_world_rank, 'change': p.gm_world_change},
            'asia': {'rank': p.gm_asia_rank, 'change': p.gm_asia_change},
            'country': {'rank': p.gm_country_rank, 'change': p.gm_country_change},
            'highlight': {'text': highlight, 'url': p.gm_highlight_url} if highlight else None,
        },
        'categories': [
            {'code': c.code, 'title': tr(c.title, lang), 'subtitle': c.subtitle, 'badge': tr(c.badge, lang) or None, 'url': c.url}
            for c in p.categories.all()
        ],
        'goals': [sdg_summary(g, lang) for g in SdgGoal.objects.all()],
        'impactYear': p.impact_year,
        'reports': attachments_out(p.reports.select_related('file'), lang),
        'education': {
            'title': tr(p.education_title, lang),
            'text': tr(p.education_text, lang),
            'tags': lines(p.education_tags, lang),
            'url': p.education_url,
        },
        'news': [post_summary(x, lang) for x in news],
    }


def sdg_goal_out(g: SdgGoal, lang: str) -> dict:
    value = tr(g.highlight_value, lang)
    return {
        **sdg_summary(g, lang),
        'subtitle': tr(g.subtitle, lang),
        'highlight': {'label': g.highlight_label, 'value': value} if g.highlight_label and value else None,
        'sections': [
            {
                'id': s.key or f's{i}',
                'title': tr(s.title, lang),
                'body': tr(s.body, lang),
                'images': [x for x in (img(m, 'card') for m in s.images.all()) if x],
            }
            for i, s in enumerate(g.sections.prefetch_related('images'), start=1)
        ],
        'documents': attachments_out(g.reports.select_related('file'), lang),
    }


# ─── Aloqa ───────────────────────────────────────────────────────────────────

def contact_out(lang: str) -> dict:
    s = SiteSettings.load()
    leaders = list(Leader.objects.all())
    return {
        'hotline': {'phone': s.phone, 'ext': s.phone_ext or None},
        'emails': [{'title': tr(e.title, lang), 'value': e.value, 'extra': lines(e.extra, lang)} for e in ContactEmail.objects.all()],
        'campuses': [
            {
                'id': c.key, 'name': tr(c.name, lang), 'address': tr(c.address, lang), 'phone': c.phone or s.phone,
                'mapUrl': c.map_url or f"https://www.google.com/maps/search/?api=1&query={quote(tr(c.address, 'uz'))}",
            }
            for c in Campus.objects.all()
        ],
        'leaders': [
            {'name': d.name, 'role': tr(d.role, lang), 'ext': d.ext, 'phone': d.phone}
            for d in leaders if d.kind == 'prorector'
        ],
        'reception': tr(s.reception, lang),
        'recipients': [{'id': f'leader-{d.pk}', 'title': tr(d.role, lang)} for d in leaders if d.reception],
    }


# ─── Qidiruv ─────────────────────────────────────────────────────────────────

def fold(value: str) -> str:
    """Katta-kichik harf va tutuq belgilari farqisiz solishtirish."""
    return re.sub(r"[‘’ʻʼ`´']", "'", (value or '').lower())


def search_out(lang: str, q: str, kind: str | None, page: int, per_page: int) -> dict:
    terms = fold(q).split()

    def match(*texts) -> bool:
        hay = fold(' '.join(t for t in texts if t))
        return bool(terms) and all(t in hay for t in terms)

    candidates = list(Page.objects.filter(published=True, in_menu=True).select_related('file'))
    by_id = {p.pk: p for p in candidates}

    def group_title(p: Page) -> str:
        node, seen = p, set()
        while node.parent_id and node.parent_id in by_id and node.pk not in seen:
            seen.add(node.pk)
            node = by_id[node.parent_id]
        return tr(node.title, lang)

    pages = []
    for p in candidates:
        if p.template not in ('text', 'special'):
            continue
        title = tr(p.title, lang)
        if match(title, text_of(tr(p.lead, lang)) if p.template == 'text' else ''):
            lead = text_of(tr(p.lead, lang)) if p.template == 'text' else ''
            pages.append({'kind': 'pages', 'title': title, 'url': p.site_url, 'excerpt': lead[:240] or None, 'meta': group_title(p), 'date': None})

    news = []
    for p in Post.visible(lang).select_related('category').defer('body').order_by('-published_at')[:2000]:
        title, excerpt = tr(p.title, lang), pick(p.excerpt, lang) or ''
        if match(title, excerpt):
            news.append({
                'kind': 'news', 'title': title, 'url': f'/{p.type}/{p.slug}', 'excerpt': excerpt or None,
                'meta': tr(p.category.name, lang) if p.category else '', 'date': local_date(p.published_at),
            })

    documents = []
    for d in Document.objects.select_related('file_uz', 'file_ru', 'file_en', 'file_zh'):
        item = document_item(d, lang)
        if item and match(item['title']):
            documents.append({'kind': 'documents', 'title': item['title'], 'url': item['url'], 'excerpt': None, 'meta': 'PDF' if item['kind'] == 'pdf' else 'URL', 'date': None})

    everything = {'pages': pages, 'news': news, 'documents': documents}
    chosen = everything[kind] if kind in everything else pages + news + documents
    start = (page - 1) * per_page
    quick = pages[0] if pages else None
    return {
        'q': q,
        'counts': {k: len(v) for k, v in everything.items()},
        'quick': {'title': quick['title'], 'text': quick['meta'], 'url': quick['url']} if quick else None,
        'items': chosen[start:start + per_page],
        'total': len(chosen),
        'page': page,
        'perPage': per_page,
    }
