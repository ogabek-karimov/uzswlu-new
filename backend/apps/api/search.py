"""Sayt bo'yicha qidiruv (GET /search).

Nima qidiriladi: menyudagi sahifalar (sarlavha, kirish matni va asosiy matn), PDF/havola sahifalari, yangilik/e'lon/tadbirlar
(sarlavha, qisqa matn va to'liq matn), hujjatlar, fakultetlar, kafedralar, ta'lim yo'nalishlari, video darslar,
rahbariyat va xodimlar (HEMIS).

Yozuv farqlari hisobga olinmaydi: katta-kichik harf, tutuq belgilari (o‘/o'/oʻ/o), yangi alifbo (ö ğ ş ç = o‘ g‘ sh ch),
kirill (о‘збекча кирилл ва рус) — so'rov ham, matn ham bir xil lotin shakliga keltiriladi. So'z oxiridagi qo'shimchalar
("kafedralari" → "kafedra", "кафедры" → "кафедр") qisqartirib ham qidiriladi.

Indeks har til uchun xotirada saqlanadi; admin saqlaganda (`content_ver`) yoki bazadagi postlar/sahifalar o'zgarganda qayta quriladi.
"""
import re
import threading
import time

from django.core.cache import cache
from django.db.models import Count, Max

from apps.content.models import Document, Leader, Post, QuickLink, Video
from apps.core.fields import pick, tr
from apps.core.html import text_of
from apps.core.utils import local_date
from apps.hemis import get_client
from apps.hemis.models import HemisSnapshot
from apps.pages.models import Page
from apps.structure.models import Department, Faculty, Program, StaffProfile

KINDS = ('pages', 'news', 'documents', 'people')
INDEX_TTL = 300          # soniya: shundan keyin indeks baribir qayta quriladi (HEMIS yangilanishi va boshqalar uchun)
BODY_LIMIT = 20_000      # bitta matndan indeksga olinadigan belgilar

# Natija turi yonidagi qisqa izoh (meta) — 4 tilda
META = {
    'faculty': {'uz': 'Fakultet', 'ru': 'Факультет', 'en': 'Faculty', 'zh': '学院'},
    'department': {'uz': 'Kafedra', 'ru': 'Кафедра', 'en': 'Department', 'zh': '教研室'},
    'program': {'uz': 'Ta’lim yo‘nalishi', 'ru': 'Направление обучения', 'en': 'Study programme', 'zh': '专业'},
    'video': {'uz': 'Video dars', 'ru': 'Видеоурок', 'en': 'Video lesson', 'zh': '视频课程'},
    'leader': {'uz': 'Rahbariyat', 'ru': 'Руководство', 'en': 'Leadership', 'zh': '校领导'},
    'staff': {'uz': 'Xodim', 'ru': 'Сотрудник', 'en': 'Staff', 'zh': '教职工'},
    'quick': {'uz': 'Tezkor xizmat', 'ru': 'Быстрый сервис', 'en': 'Quick service', 'zh': '快捷服务'},
}
LEVEL_URL = {'bachelor': '/bakalavriat', 'master': '/magistratura'}

# ─── Matnni bir xil shaklga keltirish ────────────────────────────────────────

_CYR = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y',
    'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'ў': 'o', 'қ': 'q', 'ғ': 'g', 'ҳ': 'h',
    # Yangi va eski lotin alifbosi
    'ö': 'o', 'ó': 'o', 'ğ': 'g', 'ǵ': 'g', 'ş': 'sh', 'ç': 'ch', 'ı': 'i',
}
_APOS = re.compile(r"[‘’ʻʼ`´'ʹ′]")
_WORD_START_E = re.compile(r'(^|[^\w])е')     # o'zbek kirillida so'z boshidagi "е" = "ye"
_NON_WORD = re.compile(r'[^\w№]+')
_CJK = re.compile(r'[぀-ヿ㐀-鿿豈-﫿]')


def norm(value: str | None) -> str:
    """Solishtirish shakli: ' sozlar bosh harfsiz va tutuqsiz ' (chetlarida bo'sh joy — so'z boshini topish uchun)."""
    s = _WORD_START_E.sub(r'\1ye', (value or '').lower())
    s = ''.join(_CYR.get(ch, ch) for ch in s)
    s = _APOS.sub('', s)
    s = _NON_WORD.sub(' ', s).strip()
    return f' {s} ' if s else ' '


# O'zbekcha so'z o'zgartiruvchi qo'shimchalar (lotin, tutuqsiz) — uzunidan qisqasiga
_UZ_SUFFIXES = sorted({
    'larimizning', 'laringizning', 'larining', 'larimiz', 'laringiz', 'laridan', 'larida', 'lariga', 'larini',
    'lardan', 'larda', 'larga', 'larni', 'larning', 'lari', 'lar',
    'imizning', 'ingizning', 'ining', 'imiz', 'ingiz', 'ning', 'idagi', 'dagi', 'idan', 'ida', 'iga', 'ini',
    'dan', 'da', 'ga', 'ka', 'qa', 'ni', 'si', 'i',
}, key=len, reverse=True)


def variants(term: str) -> list[str]:
    """So'rovdagi so'z va uning qisqartirilgan shakllari (qo'shimchasiz, oxirgi 1–2 harfsiz)."""
    out = [term]
    if len(term) >= 5 and not term.isdigit():
        stem = term
        for _ in range(3):
            cut = next((s for s in _UZ_SUFFIXES if stem.endswith(s) and len(stem) - len(s) >= 4), None)
            if not cut:
                break
            stem = stem[:-len(cut)]
            out.append(stem)
        if len(term) >= 6:
            out.append(term[:-1])
        if len(term) >= 7:
            out.append(term[:-2])
    return list(dict.fromkeys(out))


def _has(hay: str, word: str) -> bool:
    """So'z boshidan mos keladimi (xitoycha — istalgan joyidan)."""
    return f' {word}' in hay or (bool(_CJK.search(word)) and word in hay)


# ─── Indeks ──────────────────────────────────────────────────────────────────

def _entry(kind, title, url, *, meta='', excerpt='', body='', date=None, order=0):
    title = title or ''
    excerpt = (excerpt or '').strip()
    return {
        'kind': kind, 'title': title, 'url': url, 'meta': meta or '', 'excerpt': excerpt[:240] or None, 'date': date,
        'order': order, 'plain': (body or '')[:BODY_LIMIT], 't': norm(title), 'b': norm(f'{excerpt} {body[:BODY_LIMIT] if body else ""}'),
    }


def _is_pdf(page: Page) -> bool:
    return bool(page.file_id) or bool(re.search(r'\.pdf($|\?)', page.url or '', re.I))


def _by_lang(value, lang: str) -> str:
    """HEMIS matni: satr yoki {uz, ru, ...}."""
    if isinstance(value, str):
        return value
    return tr(value, lang) if isinstance(value, dict) else ''


def _person(name: str) -> str:
    """HEMIS'dagi "TUXTASINOV ILXOMJON" → "Tuxtasinov Ilxomjon" (tutuqdan keyingi harf kichik qoladi)."""
    if not name.isupper():
        return name
    return ' '.join(w[:1] + w[1:].lower() for w in name.split())


def _pages(lang: str) -> list[dict]:
    rows = list(Page.objects.filter(published=True, in_menu=True).select_related('file').order_by('order', 'id'))
    by_id = {p.pk: p for p in rows}

    def section(p: Page) -> str:
        node, seen = p, set()
        while node.parent_id and node.parent_id in by_id and node.pk not in seen:
            seen.add(node.pk)
            node = by_id[node.parent_id]
        return tr(node.title, lang) if node is not p else ''

    out = []
    for i, p in enumerate(rows):
        title = tr(p.title, lang)
        if p.template == 'group':
            url = p.overview or p.url
            if url:
                out.append(_entry('pages', title, url, meta=title, excerpt=tr(p.description, lang), order=i))
        elif p.template == 'link':
            kind = 'documents' if _is_pdf(p) else 'pages'
            out.append(_entry(kind, title, p.site_url, meta='PDF' if kind == 'documents' else section(p), order=i))
        else:
            lead = text_of(tr(p.lead, lang)) if p.template == 'text' else ''
            body = text_of(tr(p.body, lang)) if p.template == 'text' else ''
            out.append(_entry('pages', title, p.site_url, meta=section(p), excerpt=lead, body=body, order=i))
    return out


def _posts(lang: str) -> list[dict]:
    out = []
    for p in Post.visible(lang).select_related('category').order_by('-published_at')[:3000]:
        out.append(_entry(
            'news', tr(p.title, lang), f'/{p.type}/{p.slug}',
            meta=tr(p.category.name, lang) if p.category else '', excerpt=pick(p.excerpt, lang) or '',
            body=text_of(tr(p.body, lang)), date=local_date(p.published_at),
        ))
    return out


def _documents(lang: str) -> list[dict]:
    from .builders_site import document_item

    out = []
    for d in Document.objects.select_related('category', 'file_uz', 'file_ru', 'file_en', 'file_zh'):
        item = document_item(d, lang)
        if item:
            category = tr(d.category.title, lang) if d.category_id else ''
            out.append(_entry('documents', item['title'], item['url'], meta='PDF' if item['kind'] == 'pdf' else 'URL',
                              body=f'{category} {d.number or ""}'))
    return out


def _structure(lang: str) -> list[dict]:
    client = get_client()
    out = []
    own = {d.hemis_id: d for d in Department.objects.all()}
    for i, f in enumerate(Faculty.objects.all()):
        name = tr(f.name, lang)
        h = client.faculty(f.slug) or {}
        about = text_of(tr(f.about, lang) or _by_lang(h.get('about'), lang))
        out.append(_entry('pages', name, f'/faculty/{f.slug}', meta=META['faculty'][lang], excerpt=about, order=i))
        for d in h.get('departments') or []:
            mine = own.get(d.get('id'))
            dname = (tr(mine.name, lang) if mine and mine.name else None) or _by_lang(d.get('name'), lang)
            head = d.get('head') or {}
            head_name = head.get('name', '') if isinstance(head, dict) else str(head)
            if dname:
                out.append(_entry('pages', dname, f"/faculty/{f.slug}#dept-{d.get('id')}", meta=f"{META['department'][lang]} · {name}",
                                  body=head_name, order=100 + i))
    for i, ql in enumerate(QuickLink.objects.filter(visible=True)):
        out.append(_entry('pages', tr(ql.title, lang), ql.url, meta=META['quick'][lang], excerpt=tr(ql.text, lang), order=50 + i))
    for p in Program.objects.select_related('faculty'):
        title = f'{p.code} — {tr(p.title, lang)}'
        out.append(_entry('pages', title, f"{LEVEL_URL.get(p.level, '/bakalavriat')}#{p.code}", meta=META['program'][lang],
                          body=tr(p.faculty.name, lang) if p.faculty_id else '', order=200))
    for v in Video.objects.select_related('category'):
        out.append(_entry('pages', tr(v.title, lang), f'/video-darsliklar#video-{v.pk}', meta=META['video'][lang],
                          body=f"{v.teacher} {tr(v.category.title, lang) if v.category_id else ''}", order=300))
    return out


def _people(lang: str) -> list[dict]:
    out = []
    for i, ld in enumerate(Leader.objects.all()):
        role = text_of(tr(ld.role, lang))
        url = f'/teacher/{ld.staff_id}' if ld.staff_id else f'/rektorat#leader-{ld.pk}'
        out.append(_entry('people', ld.name, url, meta=META['leader'][lang], excerpt=role, order=i))
    hidden = set(StaffProfile.objects.filter(hidden=True).values_list('hemis_id', flat=True))
    for p in get_client().staff(lang):
        if str(p['id']) in hidden:
            continue
        jobs = [e for e in p.get('employments') or [] if str((e.get('status') or {}).get('code')) != '14']
        base, patronymic = p.get('name') or '', p.get('patronymic') or ''
        name = f'{base} {patronymic}' if patronymic and patronymic not in base else base
        first = jobs[0] if jobs else None
        meta = ' · '.join(x for x in ((first['position'] or {}).get('name') if first else '', first['department']['name'] if first else '') if x)
        extra = ' '.join(f"{(e.get('position') or {}).get('name', '')} {e['department']['name']}" for e in jobs)
        out.append(_entry('people', _person(name), f"/teacher/{p['id']}",
                          meta=meta or META['staff'][lang], body=extra, order=1000))
    return out


def _fingerprint():
    posts = Post.objects.aggregate(n=Count('id'), u=Max('updated_at'))
    pages = Page.objects.aggregate(n=Count('id'), u=Max('updated_at'))
    hemis = HemisSnapshot.objects.aggregate(u=Max('synced_at'))
    return (
        cache.get('content_ver', 0), posts['n'], posts['u'], pages['n'], pages['u'], hemis['u'],
        Document.objects.count(), Faculty.objects.count(), Department.objects.count(), Program.objects.count(),
        Video.objects.count(), Leader.objects.count(), QuickLink.objects.filter(visible=True).count(), StaffProfile.objects.filter(hidden=True).count(),
    )


_INDEX: dict[str, tuple] = {}
_LOCK = threading.Lock()


def build_index(lang: str) -> list[dict]:
    seen, out = set(), []
    for e in _pages(lang) + _posts(lang) + _documents(lang) + _structure(lang) + _people(lang):
        key = (e['kind'], e['title'], e['url'])
        if e['title'] and key not in seen:
            seen.add(key)
            out.append(e)
    return out


def get_index(lang: str) -> list[dict]:
    fp = _fingerprint()
    hit = _INDEX.get(lang)
    if hit and hit[0] == fp and time.monotonic() - hit[1] < INDEX_TTL:
        return hit[2]
    with _LOCK:
        hit = _INDEX.get(lang)
        if hit and hit[0] == fp and time.monotonic() - hit[1] < INDEX_TTL:
            return hit[2]
        entries = build_index(lang)
        _INDEX[lang] = (fp, time.monotonic(), entries)
        return entries


# ─── Qidiruv ─────────────────────────────────────────────────────────────────

def _score(entry: dict, terms: list[list[str]]) -> float:
    """Har bir so'z topilishi shart. Sarlavhada — ko'proq ball, aniq so'z — qisqartirilganidan ko'proq."""
    total = 0.0
    for forms in terms:
        best = 0.0
        for rank, word in enumerate(forms):
            exact = rank == 0
            if _has(entry['t'], word):
                best = max(best, 6 if exact and f' {word} ' in entry['t'] else 4 if exact else 3)
            elif _has(entry['b'], word):
                best = max(best, 1.5 if exact else 1)
            if best >= 6:
                break
        if not best:
            return 0
        total += best
    return total


def _snippet(entry: dict, raw_terms: list[str]) -> str | None:
    """Matn ichidan topilgan joy atrofidagi parcha (kirish matni bo'lmasa yoki so'z unda bo'lmasa)."""
    text = entry['plain']
    if not text:
        return entry['excerpt']
    low = _APOS.sub("'", text.lower())
    for term in raw_terms:
        for form in variants(_APOS.sub("'", term.lower())):
            i = low.find(form)
            if i >= 0:
                if entry['excerpt'] and form in _APOS.sub("'", entry['excerpt'].lower()):
                    return entry['excerpt']
                start = max(0, text.rfind(' ', 0, max(0, i - 90)) + 1)
                end = text.find(' ', min(len(text), i + 150))
                end = len(text) if end < 0 else end
                return ('… ' if start else '') + text[start:end].strip() + (' …' if end < len(text) else '')
    return entry['excerpt'] or text[:200]


def search_out(lang: str, q: str, kind: str | None, page: int, per_page: int) -> dict:
    words = norm(q).split()
    words = [w for w in words if len(w) > 1 or w.isdigit()] or words   # bitta harf hamma narsaga mos keladi
    raw_terms = [w for w in re.split(r'\s+', q.strip()) if w]
    terms = [variants(w) for w in words]
    found = {k: [] for k in KINDS}
    if terms:
        for entry in get_index(lang):
            score = _score(entry, terms)
            if score:
                found[entry['kind']].append((score, entry))
    # Eng mosi tepada; bir manzil bir marta (masalan bo'lim va uning umumiy sahifasi bitta manzilda)
    ranked_all, urls = [], set()
    for score, entry in sorted((se for k in KINDS for se in found[k]),
                               key=lambda se: (-se[0], -int((se[1]['date'] or '0').replace('-', '') or 0), se[1]['order'])):
        if entry['url'] not in urls:
            urls.add(entry['url'])
            ranked_all.append(entry)

    def out(entry: dict) -> dict:
        excerpt = _snippet(entry, raw_terms) if entry['kind'] in ('pages', 'news') else entry['excerpt']
        return {'kind': entry['kind'], 'title': entry['title'], 'url': entry['url'], 'excerpt': excerpt, 'meta': entry['meta'], 'date': entry['date']}

    ranked = {k: [e for e in ranked_all if e['kind'] == k] for k in KINDS}
    chosen = ranked[kind] if kind in ranked else ranked_all   # "Hammasi" — turidan qat'i nazar, mosligi bo'yicha
    start = (page - 1) * per_page
    best = {id(e): sc for sc, e in found['pages']}
    top = ranked['pages'][0] if ranked['pages'] else None
    quick = top if top and best[id(top)] >= 4 * len(terms) else None   # tezkor javob — sarlavhasi so'rovga to'liq mos sahifa
    return {
        'q': q,
        'counts': {k: len(v) for k, v in ranked.items()},
        'quick': {'title': quick['title'], 'text': quick['meta'], 'url': quick['url']} if quick else None,
        'items': [out(e) for e in chosen[start:start + per_page]],
        'total': len(chosen),
        'page': page,
        'perPage': per_page,
    }
