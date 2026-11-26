"""Ochiq sayt API'si javoblarini yig'ish (frontend/docs/openapi.yaml shartnomasi)."""
import re
from collections import defaultdict
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.api.builders_staff import department_staff_out, units_out
from apps.content.models import (
    Document, DocCategory, HomeBanner, HomeVideoTour, Leader, Partner, UnitHead, QuickLink, Post, Slide, StateSymbol, TaughtLanguage, Video, VideoCategory, VideoPage,
)
from apps.content.video_tour import parse_video
from apps.core.fields import pick, tr
from apps.core.html import restore_timeline, text_of
from apps.core.models import SiteSettings
from apps.core.utils import local_date, size_label
from apps.hemis import get_client
from apps.pages.models import Page, SdgGoal, SdgPage
from apps.structure.maps import map_embed, map_link
from apps.structure.models import (
    FORM_LABELS, AdmissionYear, Campus, ContactEmail, Faculty, PhoneEntry, Program, ProgramGroup, RudeWord,
)

from .builders import (
    POST_RELATED, announcement_item, event_item, latest_posts, news_item, post_summary, upcoming_events,
)
from .common import attachment_out, attachments_out, img, iso, lines

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
        'banner': banner_out(lang),
        'videoTour': video_tour_out(lang),
        'quickLinks': quick_links_out(lang),
        'updatedAt': iso(synced or timezone.now()),
    }


def banner_out(lang: str) -> dict | None:
    """Bayram banneri: yashirilgan yoki rasmi yo'q bo'lsa — null (blok chiqmaydi)."""
    b = HomeBanner.load()
    if not b.visible or not b.image_id:
        return None
    # width/height — brauzer rasm yuklanguncha joyini oldindan ajratadi (sahifa sakramaydi)
    return {'image': img(b.image, 'hero'), 'width': b.image.width or None, 'height': b.image.height or None,
            'alt': tr(b.alt, lang), 'link': b.link or None}


def quick_links_out(lang: str) -> list[dict]:
    """«Tezkor xizmatlar»: faqat ko'rinadigan kartalar, tartib bo'yicha. Sarlavhasi tanlangan tilda bo'sh bo'lsa — o'zbekcha."""
    out = []
    for q in QuickLink.objects.filter(visible=True):
        title = tr(q.title, lang) or q.title.get('uz') or ''
        if not title:
            continue
        out.append({'id': str(q.pk), 'icon': q.icon, 'url': q.url, 'external': q.url.startswith('http'),
                    'title': title, 'text': tr(q.text, lang) or None})
    return out


def video_tour_out(lang: str) -> dict | None:
    """«Universitet haqida» blokidagi video tur: havola yo'q/noto'g'ri yoki yashirilgan bo'lsa — null (eski karta qoladi)."""
    v = HomeVideoTour.load()
    parsed = parse_video(v.url) if v.visible else None
    if not parsed:
        return None
    kind, embed = parsed
    return {'kind': kind, 'url': embed, 'poster': img(v.poster, 'hero') if v.poster_id else None,
            'title': tr(v.title, lang) or None, 'text': tr(v.text, lang) or None}


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

    # Qabul sahifasi bandi nomidagi yil (masalan «Qabul – 2026/2027») — doim faol qabul yili (admin → Qabul yillari)
    adm_year = AdmissionYear.active().year

    menu = []
    for g in children.get(None, []):
        if g.template != 'group':
            continue
        links = []
        for p in flatten(g.pk):
            if p.template == 'group':
                continue
            url = p.site_url
            title = tr(p.title, lang)
            if url == '/qabul':
                title = re.sub(r'\d{4}\s*/\s*\d{4}', adm_year, title)
            links.append({
                'title': title,
                'url': url,
                'file': 'pdf' if p.template == 'link' and (p.file_id or re.search(r'\.pdf($|\?)', url, re.I)) else None,
                'highlight': p.highlight,
                'sdg': p.sdg or None,
                'icon': p.icon or None,
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
        # mapUrl — «Xaritada ochish» (Aloqa sahifasidagi bilan bir xil); footerdagi QR kod bosh binoning shu havolasini kodlaydi
        'campuses': [
            {'id': c.key, 'name': tr(c.name, lang), 'address': tr(c.address, lang),
             'mapUrl': c.map_url if c.map_url and 'google.' not in c.map_url else map_link(c.coords, tr(c.address, 'uz'))}
            for c in Campus.objects.all()
        ],
        'socials': socials,
        'showBuildings': s.show_buildings_link,
        # Faol qabul yili (admin → Qabul yillari): header tugmasi, menyu, sahifa sarlavhalari shundan
        'admissionYear': AdmissionYear.active().year,
        'symbols': symbols_out(lang) or None,
        'symbolsBackground': s.symbols_background,
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

def _trail(p: Page, lang: str) -> list[dict]:
    out = []
    while p and p.template != 'group':
        out.insert(0, {'title': tr(p.title, lang), 'url': p.site_url})
        if p.in_menu:
            break
        p = p.parent
    return out


# Onlayn kameralar (Online translatsiya): matndagi «Nomi | https://rtsp.ru/embed/…» qatorlari — 2 ustunli kamera setkasi.
# Admin matnda faqat şu qatorlarni qöşadi/öçiradi; boşiga «-» qöyilsa kamera vaqtinça yaşiriladi; iframe saqlanmaydi, faqat ruxsat etilgan xostdan quriladi.
_CAMERA = re.compile(r'<p>(?:<[^>]+>|\s)*([^<|]{1,60}?)\s*\|\s*(?:<a[^>]*>)?\s*(https://rtsp\.ru/embed/[\w-]+/?)\s*(?:</a>)?(?:</[^>]+>|\s)*</p>')
_CAMERA_RUN = re.compile(r'(?:\s*' + _CAMERA.pattern + r')+')


def cameras_html(body: str) -> str:
    def grid(run):
        items = ''.join(
            f'<figure class="camera"><figcaption>{escape(name.strip())}</figcaption><div class="camera-frame">'
            f'<iframe src="{escape(url)}" title="{escape(name.strip())}" allow="fullscreen; autoplay" allowfullscreen loading="lazy"></iframe></div></figure>'
            for name, url in _CAMERA.findall(run.group(0)) if not name.strip().startswith(('-', '#')))
        return f'<div class="camera-grid">{items}</div>' if items else ''
    return _CAMERA_RUN.sub(grid, body) if 'rtsp.ru/embed/' in body else body


def page_out(p: Page, lang: str) -> dict:
    return {
        'slug': p.slug,
        'title': tr(p.title, lang),
        'lead': tr(p.lead, lang) or None,
        # Menyuda yöq ichki sahifa (masalan, Magistrlik dasturlari → Qabul kvotasi): bölim va yon menyu ota sahifa orqali topiladi
        # cards — ota sahifadagi boşqa havolali kartalar (sahifa ostida «tez ötiş» uçun)
        'parent': {'title': tr(p.parent.title, lang), 'url': p.parent.site_url,
                   'cards': [c for b in showcase_out(p.parent.showcase, lang) for c in b['cards'] if c['url'] != p.site_url],
                   # Çuqur ichki sahifa (3-4 daraja): menyudagi ajdodgaça zanjir — breadcrumb va yon menyu uçun
                   'trail': _trail(p.parent, lang)}
        if not p.in_menu and p.parent_id and p.parent.template != 'group' else None,
        'facts': [{'value': f.value, 'label': tr(f.label, lang)} for f in p.facts.all()],
        'body': cameras_html(restore_timeline(tr(p.body, lang))),
        'timeline': [{'label': tr(t.label, lang), 'text': tr(t.text, lang), 'highlight': t.highlight} for t in p.timeline.all()],
        'attachments': attachments_out(p.attachments.select_related('file'), lang),
        # Matndan keyin rektor kartasi (admin → Rahbariyat; rektor almashsa sahifa o'zi yangilanadi)
        'rector': rector_card(lang) if p.show_rector else None,
        # Hujjat uslubi: Times New Roman, sarlavhalar markazda
        'docStyle': p.doc_style,
        # Bo'limlar kartalari: HEMIS'dan avtomatik (rahbar, surat, xodimlar soni) + admin → «Bo'limlar» qo'shimchalari
        'units': units_out(lang) if p.show_units else [],
        # Bo'lim xodimlari (HEMIS'dan avtomatik; admin → Sahifalar'da bo'lim tanlanadi)
        # Matndan keyin chaqiruv bloki (masalan, uzlib.uz) — havola va tugma yozuvi bo'lsa
        'cta': ({'title': tr(p.cta_title, lang) or None, 'text': tr(p.cta_text, lang) or None, 'label': tr(p.cta_label, lang), 'url': p.cta_url}
                if p.cta_url and tr(p.cta_label, lang) else None),
        # Ichki sahifalar kartalari (masalan, Yoshlar ittifoqi → Zakovat, Futbol…): belgi, nom, hujjatlar
        'children': [
            {'slug': c.slug, 'title': tr(c.title, lang), 'icon': c.icon or None, 'url': f'/{c.slug}',
             'attachments': attachments_out(c.attachments.select_related('file'), lang)}
            for c in p.children.filter(published=True, template='text').exclude(slug=None).prefetch_related('attachments__file').order_by('order', 'id')
        ] if p.show_children else [],
        # Kartali bloklar (matndagi [[kartalar-N]] joyida): raqamlar, ustunlar (klublar / loyihalar…), xulosa
        'showcase': showcase_out(p.showcase, lang),
        'staff': department_staff_out(p.staff_department, lang, p.staff_extra, p.staff_contacts, tr(p.staff_hours, lang)),
        'updatedAt': iso(p.updated_at),
    }


def _lines(value, lang: str) -> list[str]:
    return [x.strip() for x in (tr(value, lang) or '').splitlines() if x.strip()]


def showcase_out(data, lang: str) -> list[dict]:
    """Kartali bloklar (matndagi [[kartalar-N]] joyida). Blok: suratlar, kirish gapi, raqamlar («7 | nomi»), ustunlar
    (bandlar har qatorda; «Nom — izoh»; uslub: numbers — raqamli, checks — belgili), xulosa gapi.
    Eski shakl ({intro, columns}) — bitta blok sifatida."""
    if not isinstance(data, dict):
        return []
    blocks = data.get('blocks') if 'blocks' in data else ([data] if data.get('columns') else [])
    # Bloklardagi suratlar (media ID) — bitta so'rov bilan
    from apps.core.models import Media
    ids = {int(x) for b in blocks or [] if isinstance(b, dict) for x in (b.get('photos') or []) if str(x).isdigit()}
    ids |= {int(c['photo']) for b in blocks or [] if isinstance(b, dict) for c in (b.get('cards') or []) if isinstance(c, dict) and str(c.get('photo') or '').isdigit()}
    media = {m.pk: m for m in Media.objects.filter(pk__in=ids, kind='image')} if ids else {}
    out = []
    for n, block in enumerate(blocks or [], start=1):
        if not isinstance(block, dict):
            continue
        stats = []
        for line in _lines(block.get('stats'), lang):
            value, _, label = line.partition('|')
            if value.strip() and label.strip():
                stats.append({'value': value.strip(), 'label': label.strip()})
        columns = []
        for col in block.get('columns') or []:
            items = []
            for line in _lines(col.get('items'), lang):
                name, _, note = line.partition(' — ')
                items.append({'name': name.strip(), 'note': note.strip() or None})
            if items:
                columns.append({'title': tr(col.get('title'), lang) or '', 'icon': col.get('icon') or None,
                                'style': 'checks' if col.get('style') == 'checks' else 'numbers', 'items': items})
        # Kirish/xulosa gapi — oddiy matn: unga HTML tushib qolsa (eski saytdan nusxa) teglar ko'rinmasin
        intro, outro = ((text_of(v) if '<' in v else v) or None for v in (tr(block.get(k), lang) or '' for k in ('intro', 'outro')))
        photos = [{'url': m.size_url('hero') or m.url, 'thumb': m.size_url('card') or m.url, 'alt': tr(m.alt, lang) or '',
                   'width': m.width, 'height': m.height}
                  for m in (media.get(int(x)) for x in (block.get('photos') or []) if str(x).isdigit()) if m]
        # Havolali kartalar: rasm + nom, bosilsa sahifaga (masalan, Xalqaro talabalar → Doktorantura, Viza …)
        cards = []
        for c in block.get('cards') or []:
            if not isinstance(c, dict) or not c.get('url'):
                continue
            m = media.get(int(c['photo'])) if str(c.get('photo') or '').isdigit() else None
            cards.append({'title': tr(c.get('title'), lang) or '', 'url': c['url'], 'photo': (m.size_url('card') or m.url) if m else None})
        if stats or columns or intro or photos or cards:
            # slider — suratlar slayderda (buklet sahifalari: bittadan, ← 1 2 3 → bilan)
            out.append({'n': n, 'intro': intro, 'stats': stats, 'columns': columns, 'outro': outro, 'photos': photos, 'cards': cards,
                        'slider': bool(block.get('slider'))})
    return out


def rector_card(lang: str) -> dict | None:
    """Rektor (admin → Rahbariyat) — surat bo'lmasa ham; saytda rasm o'rnida belgi. Rektor kiritilmagan bo'lsa — karta yo'q."""
    r = Leader.objects.filter(kind='rector').select_related('photo').first()
    return {**leader_out(r, lang), 'photo': img(r.photo, 'card') if r.photo_id else None} if r else None


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
        Post.visible(lang, scheduled=True).filter(type='events', starts_at__gte=start, starts_at__lt=end)
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
                'formId': p.form,  # day | evening | distance — saytdagi «Kunduzgi / Kechki / Sirtqi» filtri uchun
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
    campus = (Campus.objects.filter(faculty=f).exclude(coords='').first()
              or Campus.objects.filter(faculty__isnull=True).exclude(coords='').first())
    map_addr = (tr(campus.address, 'uz') if campus else '') or tr(f.address, 'uz') or contact.get('address', '')
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
            # Google havolasi (eski ma'lumot) o'rniga Yandex; qo'lda kiritilgan boshqa havola saqlanadi
            # Xarita — fakultet joylashgan bino (admin → Binolar, «Fakultet»), bo'lmasa bosh bino koordinatasi; manzil matni
            # odatda xona («Bosh bino, 2-qavat, 214-xona») — Yandex qidiruvi uni topa olmaydi
            'mapUrl': (f.map_url if f.map_url and 'google.' not in f.map_url else map_link(campus.coords if campus else '', map_addr))
            if (f.map_url or campus or map_addr) else None,
            'mapEmbed': map_embed(campus.coords if campus else '', map_addr, lang) if (campus or map_addr) else None,
        },
    }


def admission_programs_snapshot() -> list:
    """Qabuldagi yo'nalishlar va narxlar (4 tilda) — yil arxivga o'tganda saqlanadi."""
    return [
        {'id': str(p.pk), 'code': p.code, 'title': p.title, 'faculty': p.faculty.name if p.faculty else {},
         'level': p.level, 'form': p.form, 'years': p.years, 'price': p.price}
        for p in Program.objects.filter(in_admission=True).select_related('faculty')
    ]


def admission_out(lang: str, year: str | None = None) -> dict | None:
    """Qabul sahifasi: year berilmasa — faol yil (jonli yo'nalishlar); berilsa (masalan 2025-2026) — saytda ko'rinadigan arxiv yili (saqlangan nusxa)."""
    if year:
        a = AdmissionYear.objects.filter(year=year.replace('-', '/'), status='archive', public=True).first()
        if not a:
            return None
        programs = [
            {'id': x.get('id') or x.get('code'), 'code': x.get('code', ''), 'title': tr(x.get('title') or {}, lang),
             'faculty': tr(x.get('faculty') or {}, lang), 'level': x.get('level', ''), 'form': form_label(x.get('form', ''), lang),
             'years': x.get('years'), 'price': tr(x.get('price') or {}, lang) or None}
            for x in (a.programs_snapshot or [])
        ]
    else:
        a = AdmissionYear.active()
        programs = [
            {
                'id': str(p.pk), 'code': p.code, 'title': tr(p.title, lang),
                'faculty': tr(p.faculty.name, lang) if p.faculty else '',
                'level': p.level, 'form': form_label(p.form, lang), 'years': p.years,
                'price': tr(p.price, lang) or None,
            }
            for p in Program.objects.filter(in_admission=True).select_related('faculty')
        ]
    return {
        'year': a.year,
        'archived': a.status == 'archive',
        # Saytda ko'rinadigan arxiv yillari (yangidan eskiga) — sahifa pastida «Oldingi yillar»
        'archive': [{'year': x.year, 'slug': x.slug} for x in AdmissionYear.objects.filter(status='archive', public=True)],
        'applyUrl': a.apply_url,
        'dates': [
            {'title': tr(d.title, lang), 'period': tr(d.period, lang), 'current': d.current and a.status == 'active'}
            for d in a.dates.all()
        ],
        'programs': programs,
        'documents': lines(a.documents, lang),
        'documentsUrl': a.documents_url or None,
        'faq': [{'q': tr(x.question, lang), 'a': tr(x.answer, lang)} for x in a.faq.all()],
        'contact': {'address': tr(a.address, lang), 'hours': tr(a.hours, lang), 'phone': a.phone, 'telegram': a.telegram},
        # «Qabul bo'yicha ma'lumotlar» ichki sahifalari (Qabul fanlari, kvota, ijodiy imtihonlar…) — admin → Sahifalar
        'guides': admission_guides(lang),
    }


def admission_guides(lang: str) -> list[dict]:
    g = Page.objects.filter(slug='qabul-hujjatlari', published=True).first()
    if not g:
        return []
    return [
        {'title': tr(c.title, lang), 'url': f'/{c.slug}', 'icon': c.icon or None, 'docs': c.attachments.count()}
        for c in g.children.filter(published=True, template='text').exclude(slug=None).order_by('order', 'id')
    ]


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
        'documents': [
            {**x, 'section': r.section or None}
            for r in g.reports.select_related('file') for x in [attachment_out(r, lang)] if x
        ],
    }


# ─── Aloqa ───────────────────────────────────────────────────────────────────

def contact_out(lang: str) -> dict:
    s = SiteSettings.load()
    leaders = list(Leader.objects.all())
    return {
        'hotline': {'phone': s.phone, 'ext': s.phone_ext or None},
        'emails': [{'title': tr(e.title, lang), 'value': e.value, 'extra': lines(e.extra, lang)} for e in ContactEmail.objects.all()],
        # Binolar (bosh sahifadagi «Biz bilan bog'lanish» kartalari ham shundan): xarita koordinata bo'yicha, bo'lmasa manzil bo'yicha
        'campuses': [
            {
                'id': c.key, 'name': tr(c.name, lang), 'address': tr(c.address, lang), 'phone': c.phone or s.phone,
                'email': c.email or s.email or None,
                # Admin qo'lda boshqa (Google emas) havola kiritgan bo'lsa — o'sha; aks holda Yandex (xarita bilan bir xil xizmat)
                'mapUrl': c.map_url if c.map_url and 'google.' not in c.map_url else map_link(c.coords, tr(c.address, 'uz')),
                'mapEmbed': map_embed(c.coords, tr(c.address, 'uz'), lang),
                'logo': img(c.faculty.logo, 'thumb') if c.faculty_id else None,
            }
            for c in Campus.objects.select_related('faculty__logo')
        ],
        'leaders': [
            {'name': d.name, 'role': tr(d.role, lang), 'ext': d.ext, 'phone': d.phone}
            for d in leaders if d.kind == 'prorector'
        ],
        # Telefonlar ma'lumotnomasi (admin → Telefonlar): bo'lim sarlavhalari va xodim qatorlari, faqat ko'rinadiganlari
        'phones': [
            {'section': e.is_section, 'name': e.name or None, 'position': tr(e.position, lang), 'ext': e.ext or None, 'phone': e.phone or None}
            for e in PhoneEntry.objects.filter(visible=True)
        ],
        # Murojaat shaklida taqiqlangan so'zlar (admin → Haqoratli so'zlar); backend ham shu ro'yxat bilan tekshiradi
        'rudeWords': list(RudeWord.objects.filter(active=True).values_list('word', flat=True)),
        'reception': tr(s.reception, lang),
        'recipients': [{'id': f'leader-{d.pk}', 'title': tr(d.role, lang)} for d in leaders if d.reception],
    }


# ─── Qidiruv ─────────────────────────────────────────────────────────────────
