"""Xodimlar: ommaviy ro'yxat/profil (HEMIS + saytdagi qo'shimcha ma'lumot) va xodim kabineti."""
import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db.models import Count
from rest_framework.exceptions import APIException, NotFound

from apps.core.fields import LANGS, pick, tr
from apps.core.models import Media
from apps.core.uploads import clean_upload, square_avatar
from apps.core.utils import abs_url
from apps.hemis import get_client
from apps.structure.models import StaffDocument, StaffProfile

from .cabinet_roles import cabinet_role
from .common import img, iso

GROUPS = ('lead', 'faculty', 'chair', 'unit')
CONTACT_TYPES = ('email', 'telegram', 'whatsapp', 'mobile', 'phone', 'office')
SOCIAL_NETWORKS = ('instagram', 'threads', 'facebook', 'linkedin', 'x', 'youtube')
SCIENCE_NETWORKS = ('orcid', 'scholar', 'scopus', 'researchgate')
PUBLIC_SECTIONS = ('cv', 'books', 'articles')
SECTIONS = ('cv', 'books', 'presentations', 'articles', 'videos')

# Oldingi saytdagi qoidalar: bo'limga qarab ruxsat etilgan fayl turlari
DOC_RULES = {
    'cv': {'.pdf', '.doc', '.docx'},
    'books': {'.pdf', '.doc', '.docx'},
    'articles': {'.pdf', '.doc', '.docx'},
    'presentations': {'.ppt', '.pptx', '.pdf'},
    'videos': set(),
}
DOC_MAX_BYTES = 20 * 1024 * 1024
# Bitta xodim uchun kabinetdagi fayllar chegarasi (disk to'ldirib yuborilmasligi uchun)
DOC_QUOTA_COUNT = 100
DOC_QUOTA_BYTES = 300 * 1024 * 1024
ABOUT_MAX = 2000
VALUE_MAX = 300


class Unprocessable(APIException):
    status_code = 422
    default_detail = 'Invalid value'
    default_code = 'invalid'


def fold(value: str) -> str:
    """Qidiruvda tutuq belgilari, katta-kichik harf va alifbo farqi hisobga olinmaydi:
    "yo'ldoshev" = "Yo‘ldoshev" = "Yöldoşev" (HEMIS eski alifboda, sayt matnlari yangi alifboda)."""
    value = re.sub(r"[‘’ʻʼ`']", '', (value or '').lower())
    return value.translate(_FOLD_ABC)


_FOLD_ABC = str.maketrans({'ö': 'o', 'ğ': 'g', 'ş': 'sh', 'ç': 'ch'})


# ─── Ommaviy ro'yxat va profil ───────────────────────────────────────────────

def _profiles() -> dict[str, StaffProfile]:
    return {p.hemis_id: p for p in StaffProfile.objects.select_related('own_photo')}


def _photos(person: dict, profile: StaffProfile | None) -> tuple[str | None, str | None]:
    own = img(profile.own_photo, 'card') if profile and profile.own_photo_id else None
    hemis = person.get('photo')
    return (own or hemis), (hemis if own else None)


def staff_summary(person: dict, profile: StaffProfile | None) -> dict:
    photo, fallback = _photos(person, profile)
    return {
        'id': str(person['id']),
        'name': person['name'],
        'patronymic': person.get('patronymic'),
        'photo': photo,
        'photoFallback': fallback,
        'employments': person['employments'],
        'group': person['group'],
    }


def staff_list_out(lang: str, *, q: str, department: str, group: str, page: int, per_page: int) -> dict:
    client = get_client()
    profiles = _profiles()
    visible = [p for p in client.staff(lang) if not (profiles.get(str(p['id'])) and profiles[str(p['id'])].hidden)]
    words = fold(q).split()
    base = [
        p for p in visible
        if (not department or any(e['department']['id'] == department for e in p['employments']))
        and all(w in fold(p['name']) for w in words)
    ]
    groups = {'all': len(base), **{g: sum(1 for p in base if p['group'] == g) for g in GROUPS}}
    filtered = base if group not in GROUPS else [p for p in base if p['group'] == group]
    total_pages = max(1, -(-len(filtered) // per_page))
    page = min(max(1, page), total_pages)
    departments = sorted(client.staff_departments(lang), key=lambda d: d['name'].casefold())
    return {
        'items': [staff_summary(p, profiles.get(str(p['id']))) for p in filtered[(page - 1) * per_page:page * per_page]],
        'total': len(filtered),
        'page': page,
        'perPage': per_page,
        'groups': groups,
        'departments': departments,
        'summary': {'staff': len(visible), 'departments': len(departments)},
    }


def _doc_title(title: dict, lang: str) -> str:
    """Nom: so'ralgan tilda; xitoychasi bo'lmasa inglizcha, u ham bo'lmasa o'zbekcha."""
    return pick(title, lang) or (pick(title, 'en') if lang == 'zh' else None) or pick(title, 'uz') or ''


def _public_documents(hemis_id: str, profile: StaffProfile | None, lang: str) -> list[dict]:
    shown = {s for s in PUBLIC_SECTIONS if getattr(profile, f'show_{s}', True)}
    if not shown:
        return []
    docs = StaffDocument.objects.filter(hemis_id=hemis_id, section__in=shown)
    by_section: dict[str, list[dict]] = {}
    for d in docs:
        url = abs_url(d.file.url) if d.file else d.url
        if url:
            by_section.setdefault(d.section, []).append({'title': _doc_title(d.title, lang), 'url': url})
    return [{'section': s, 'items': by_section[s]} for s in PUBLIC_SECTIONS if by_section.get(s)]


def staff_profile_out(person: dict, profile: StaffProfile | None, lang: str) -> dict:
    return {
        **staff_summary(person, profile),
        'about': (tr(profile.about, lang) or None) if profile else None,
        'contacts': [c for c in (profile.contacts if profile else []) if c.get('value')],
        'socials': [s for s in (profile.socials if profile else []) if s.get('url')],
        'science': [s for s in (profile.science if profile else []) if s.get('url')],
        'documents': _public_documents(str(person['id']), profile, lang),
        'cardImage': None,
    }


def find_person(hemis_id: str, lang: str) -> dict | None:
    return next((p for p in get_client().staff(lang) if str(p['id']) == str(hemis_id)), None)


def staff_public_out(hemis_id: str, lang: str) -> dict:
    person = find_person(hemis_id, lang)
    profile = StaffProfile.objects.select_related('own_photo').filter(hemis_id=hemis_id).first()
    if not person or (profile and profile.hidden):
        raise NotFound('Staff member not found')
    return staff_profile_out(person, profile, lang)


def staff_overlay_out(hemis_id: str, lang: str) -> dict:
    """Payload bilan mos: /site/staff/:id — faqat saytda to'ldirilgan qism."""
    p = StaffProfile.objects.filter(hemis_id=hemis_id).first()
    if not p:
        return {'hidden': False, 'about': None, 'science': []}
    return {'hidden': p.hidden, 'about': tr(p.about, lang) or None, 'science': [s for s in p.science if s.get('url')]}


# ─── Kabinet ─────────────────────────────────────────────────────────────────

def _localized(value) -> dict:
    value = value if isinstance(value, dict) else {}
    return {lang: str(value.get(lang) or '') for lang in LANGS}


def cabinet_doc_out(d: StaffDocument) -> dict:
    return {
        'id': str(d.pk),
        'title': _localized(d.title),
        'url': (abs_url(d.file.url) if d.file else d.url) or '',
        'createdAt': iso(d.created_at),
    }


def cabinet_out(hemis_id: str, lang: str) -> dict:
    person = find_person(hemis_id, lang)
    if not person:
        raise NotFound('Staff member not found')
    profile = StaffProfile.objects.select_related('own_photo').filter(hemis_id=hemis_id).first()
    counts = dict(StaffDocument.objects.filter(hemis_id=hemis_id).values_list('section').annotate(n=Count('id')))
    hemis = get_client().person(hemis_id) or {}
    return {
        **cabinet_role(person, lang),
        'profile': staff_profile_out(person, profile, lang),
        'hemis': {
            'firstName': hemis.get('firstName', ''),
            'lastName': hemis.get('lastName', ''),
            'patronymic': hemis.get('patronymic'),
            'birthDate': hemis.get('birthDate'),
            'phone': hemis.get('phone'),
            'email': hemis.get('email'),
        },
        'about': _localized(profile.about if profile else {}),
        'hasOwnPhoto': bool(profile and profile.own_photo_id),
        'documents': {
            s: {
                'count': counts.get(s, 0),
                # Taqdimotlar va videolar Staff sahifasida chiqmaydi
                'visible': bool(getattr(profile, f'show_{s}', True)) if s in PUBLIC_SECTIONS else False,
            }
            for s in SECTIONS
        },
    }


def _profile_for(hemis_id: str) -> StaffProfile:
    profile, _ = StaffProfile.objects.get_or_create(hemis_id=hemis_id)
    if not profile.name:
        person = find_person(hemis_id, 'uz')
        if person:
            profile.name = person['name']
            profile.save(update_fields=['name'])
    return profile


def _https_url(value, field: str) -> str:
    value = str(value or '').strip()
    u = urlparse(value)
    if len(value) > VALUE_MAX or u.scheme != 'https' or not u.netloc:
        raise Unprocessable(f'{field}: faqat https havola (≤ {VALUE_MAX} belgi)')
    return value


def _clean_list(items, kinds: tuple, key: str, field: str) -> list[dict]:
    """key='value' — aloqa (type + value); key='url' — ijtimoiy/ilmiy profil (network + url)."""
    if not isinstance(items, list):
        raise Unprocessable(f'{field}: ro‘yxat kerak')
    kind_key = 'type' if key == 'value' else 'network'
    out = []
    for item in items:
        if not isinstance(item, dict) or item.get(kind_key) not in kinds:
            raise Unprocessable(f'{field}: noto‘g‘ri tur')
        raw = str(item.get(key) or '').strip()
        if not raw:
            continue  # bo'sh qiymat — maydon o'chiriladi
        if key == 'url':
            raw = _https_url(raw, field)
        else:
            if len(raw) > VALUE_MAX:
                raise Unprocessable(f'{field}: qiymat {VALUE_MAX} belgidan oshmasin')
            if item[kind_key] == 'email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', raw):
                raise Unprocessable(f'{field}: e-pochta noto‘g‘ri')
        out.append({kind_key: item[kind_key], key: raw})
    return out


def patch_cabinet(hemis_id: str, patch: dict) -> None:
    """Faqat yuborilgan qismlar o'zgaradi; hammasi tekshiriladi, keyin birdaniga saqlanadi."""
    if not isinstance(patch, dict):
        raise Unprocessable('JSON obyekt kerak')
    changes: dict = {}
    if 'about' in patch:
        about = patch['about']
        if not isinstance(about, dict):
            raise Unprocessable('about: {uz, ru, en, zh} kerak')
        cleaned = {}
        for lang in LANGS:
            text = re.sub(r'<[^>]*>', '', str(about.get(lang) or '')).strip()
            if len(text) > ABOUT_MAX:
                raise Unprocessable(f'about: {ABOUT_MAX} belgidan oshmasin')
            if text:
                cleaned[lang] = text
        changes['about'] = cleaned
    if 'contacts' in patch:
        changes['contacts'] = _clean_list(patch['contacts'], CONTACT_TYPES, 'value', 'contacts')
    if 'socials' in patch:
        changes['socials'] = _clean_list(patch['socials'], SOCIAL_NETWORKS, 'url', 'socials')
    if 'science' in patch:
        changes['science'] = _clean_list(patch['science'], SCIENCE_NETWORKS, 'url', 'science')
    if 'visibility' in patch:
        vis = patch['visibility']
        if not isinstance(vis, dict):
            raise Unprocessable('visibility: obyekt kerak')
        for s in PUBLIC_SECTIONS:
            if s in vis:
                if not isinstance(vis[s], bool):
                    raise Unprocessable(f'visibility.{s}: true/false kerak')
                changes[f'show_{s}'] = vis[s]
    profile = _profile_for(hemis_id)
    for name, value in changes.items():
        setattr(profile, name, value)
    profile.save()


def set_avatar(hemis_id: str, file) -> None:
    try:
        content = square_avatar(file)
    except ValidationError as exc:
        raise Unprocessable(exc.messages[0]) from exc
    profile = _profile_for(hemis_id)
    old = profile.own_photo
    media = Media(folder='staff', file=content)  # Media.save() o'zi WebP va kichik o'lchamlarni tayyorlaydi
    media.save()
    profile.own_photo = media
    profile.save(update_fields=['own_photo', 'updated_at'])
    if old:
        old.delete()


def remove_avatar(hemis_id: str) -> None:
    profile = StaffProfile.objects.filter(hemis_id=hemis_id).select_related('own_photo').first()
    if profile and profile.own_photo_id:
        old = profile.own_photo
        profile.own_photo = None
        profile.save(update_fields=['own_photo', 'updated_at'])
        old.delete()


def docs_list_out(hemis_id: str, section: str) -> list[dict]:
    return [cabinet_doc_out(d) for d in StaffDocument.objects.filter(hemis_id=hemis_id, section=section)]


def _check_quota(hemis_id: str) -> None:
    docs = list(StaffDocument.objects.filter(hemis_id=hemis_id).exclude(file='').only('file'))
    used = 0
    for d in docs:
        try:
            used += d.file.size
        except (OSError, ValueError):
            pass
    if len(docs) >= DOC_QUOTA_COUNT or used >= DOC_QUOTA_BYTES:
        raise Unprocessable('Fayllar chegarasi to‘ldi — eskilarini o‘chiring')


def add_document(hemis_id: str, section: str, data, files) -> dict:
    titles = {lang: str(data.get(f'title_{lang}') or '').strip() for lang in LANGS}
    if not titles['uz'] or any(len(t) > 255 for t in titles.values()):
        raise Unprocessable('title_uz majburiy, nomlar ≤ 255 belgi')
    title = {lang: t for lang, t in titles.items() if t}
    if section == 'videos':
        url = _https_url(data.get('url'), 'url')
        doc = StaffDocument.objects.create(hemis_id=hemis_id, section=section, title=title, url=url)
        return cabinet_doc_out(doc)
    file = files.get('file')
    if not file:
        raise Unprocessable('Fayl kerak')
    _check_quota(hemis_id)
    try:
        clean, _ = clean_upload(file, DOC_RULES[section], DOC_MAX_BYTES)  # tozalangan nusxa, tasodifiy nom
    except ValidationError as exc:
        raise Unprocessable(exc.messages[0]) from exc
    doc = StaffDocument(hemis_id=hemis_id, section=section, title=title)
    doc.file = clean
    doc.save()
    return cabinet_doc_out(doc)


def delete_document(hemis_id: str, section: str, pk: str) -> None:
    doc = StaffDocument.objects.filter(hemis_id=hemis_id, section=section, pk=pk if str(pk).isdigit() else -1).first()
    if not doc:
        raise NotFound('Document not found')
    if doc.file:
        doc.file.delete(save=False)
    doc.delete()


# ─── Bo'limlar sahifasi (/bolimlar) ──────────────────────────────────────────
# Kartalar HEMIS'dan avtomatik (Staff kabi): har bir bo'lim/markaz (group=unit) — rahbari (lavozimi boshlig'i/direktori/mudiri/raisi…),
# surati, xodimlar soni; bosilsa Staff'da shu bo'lim xodimlari. Admin → «Bo'limlar» (UnitHead) HEMIS'da yo'q narsani to'ldiradi:
# telefon, ichki raqam, bo'lim sahifasi havolasi, yashirish (rahbar F.I.Sh. bo'yicha moslanadi); HEMIS'da yo'q bo'lim — alohida karta.
HEAD_RE = re.compile(r"boshli|direktor|mudir|rais|rahbar|начальник|директор|заведующ|председател|руковод|head|director|chair", re.I)


def _same_person(hemis_name: str, admin_name: str) -> bool:
    """F.I.Sh. so'zlar tartibidan qat'i nazar: HEMIS'dagi ism va familiya admin yozuvidagi so'zlar ichida bo'lsa."""
    h, a = set(fold(hemis_name).split()), set(fold(admin_name).split())
    return len(h) >= 2 and len(h & a) >= 2


def units_out(lang: str) -> list[dict]:
    from apps.api.common import img
    from apps.content.models import UnitHead
    client = get_client()
    profiles = _profiles()
    manual = list(UnitHead.objects.select_related('photo'))
    used: set[int] = set()
    out = []
    staff = [p for p in client.staff(lang) if not (profiles.get(str(p['id'])) and profiles[str(p['id'])].hidden)]
    for d in client.staff_departments(lang):
        if d.get('group') != 'unit':
            continue
        members = [(p, e) for p in staff for e in p['employments'] if e['department']['id'] == d['id']]
        head = next(((p, e) for p, e in members if HEAD_RE.search(e['position']['name'] or '')), None)
        # 1) shu odam (F.I.Sh.) — surat ham; 2) bo'lim nomi admin lavozim matnida — faqat telefon/havola/yashirish
        extra = next((u for u in manual if u.pk not in used and head and _same_person(head[0]['name'], u.name)), None)
        same_person = extra is not None
        if not extra:
            extra = next((u for u in manual if u.pk not in used and fold(d['name']) in fold(pick(u.position, 'uz'))), None)
        if extra:
            used.add(extra.pk)
            if not extra.visible:
                continue
        photo = None
        if head:
            photo, fallback = _photos(head[0], profiles.get(str(head[0]['id'])))
            photo = photo or fallback
        if extra and same_person and extra.photo_id:
            photo = img(extra.photo, 'card')
        out.append({
            'unit': d['name'], 'count': d.get('count') or len(members),
            'name': head[0]['name'] if head else None,
            'position': head[1]['position']['name'] if head else None,
            'photo': photo,
            'phone': (extra.phone if extra else '') or None, 'ext': (extra.ext if extra else '') or None,
            'email': (extra.email if extra else '') or None,
            'url': (extra.url if extra and extra.url else f"/staff?department={d['id']}"),
            'source': 'hemis',
        })
    # Admin qo'shgan, HEMIS'da topilmagan bo'limlar
    for u in manual:
        if u.pk in used or not u.visible:
            continue
        out.append({
            'unit': None, 'count': None, 'name': u.name, 'position': pick(u.position, lang) or None,
            'photo': img(u.photo, 'card') if u.photo_id else None,
            'phone': u.phone or None, 'ext': u.ext or None, 'email': u.email or None, 'url': u.url or None, 'source': 'admin',
        })
    return out


# ─── Sahifadagi bo'lim xodimlari (masalan, /axborot-resurs-markazi) ─────────────
# Admin → Sahifalar → «Bo'lim xodimlari» da HEMIS bo'limi tanlanadi; xodimlar HEMIS'dan avtomatik (Staff kabi, yashirilganlar chiqmaydi).
# Tartib: rahbar (direktor, boshliq) → o'rinbosar → bo'lim mudirlari → qolganlar (alifbo bo'yicha).
DEPUTY_RE = re.compile(r"o.?rinbosar|заместител|deputy|vice", re.I)
SUBHEAD_RE = re.compile(r"mudir|заведующ|head of|rais|председател", re.I)
CHIEF_RE = re.compile(r"direktor|boshli|rahbar|директор|начальник|руковод|director|chief", re.I)


def _rank(position: str) -> int:
    if DEPUTY_RE.search(position):
        return 1
    if CHIEF_RE.search(position):
        return 0
    return 2 if SUBHEAD_RE.search(position) else 3


def _resolve_department(client, department: str) -> str | None:
    """ID yoki o'zbekcha nom («Axborot-resurs markazi») — nom bo'lsa HEMIS ID'siga aylantiriladi (alifbodan mustaqil)."""
    if not department:
        return None
    deps = client.staff_departments('uz')
    if str(department) in {str(d['id']) for d in deps}:
        return str(department)
    key = fold(department)
    return next((str(d['id']) for d in deps if fold(d['name']) == key), None)


def department_staff_out(department: str, lang: str, extra: list | None = None, contacts: dict | None = None, hours: str = '') -> list[dict]:
    """Bo'lim xodimlari (HEMIS, avtomatik; rahbar birinchi) + admin qo'shgan HEMIS xodimlari (zaxira, tanlangan tartibda).
    Takrorlanmaydi; yashirilgan xodimlar chiqmaydi. Karta (eski saytdagidek): surat, F.I.Sh., lavozim, telefon, qabul kunlari,
    e-pochta — telefon/e-pochta: admin shu sahifada kiritgani, bo'lmasa xodim o'z kabinetida kiritgani."""
    extra_ids = [str(x) for x in (extra or []) if x]
    client = get_client()
    dep = _resolve_department(client, department)
    if not dep and not extra_ids:
        return []
    profiles = _profiles()
    rows, by_id = [], {}
    for person in client.staff(lang):
        profile = profiles.get(str(person['id']))
        if profile and profile.hidden:
            continue
        by_id[str(person['id'])] = (person, profile)
        jobs = [e for e in person['employments'] if dep and str(e['department']['id']) == dep]
        if jobs:
            job = min(jobs, key=lambda e: _rank(e['position']['name'] or ''))
            rows.append((_rank(job['position']['name'] or ''), fold(person['name']), _page_card(person, profile, job, contacts, hours)))
    out = [r[2] for r in sorted(rows, key=lambda r: (r[0], r[1]))]
    seen = {p['id'] for p in out}
    for hid in extra_ids:
        if hid in by_id and hid not in seen:
            seen.add(hid)
            person, profile = by_id[hid]
            out.append(_page_card(person, profile, (person['employments'] or [None])[0], contacts, hours))
    return out


def _page_card(person: dict, profile, job: dict | None, contacts: dict | None, hours: str) -> dict:
    own = (contacts or {}).get(str(person['id'])) or {}
    mine = {c.get('type'): c.get('value') for c in (profile.contacts if profile else []) if c.get('value')}
    return {
        **staff_summary(person, profile),
        'position': (job or {}).get('position', {}).get('name') or None,
        # Faqat universitetdagi ichki (ish) telefoni: admin kiritgani yoki xodim kabinetidagi «Ichki telefon» (phone).
        # Shaxsiy «Mobil telefon» (mobile) kartada HECH QACHON ko'rinmaydi.
        'phone': (own.get('phone') or '').strip() or mine.get('phone') or None,
        'email': (own.get('email') or '').strip() or mine.get('email') or None,
        'hours': hours or None,
    }
