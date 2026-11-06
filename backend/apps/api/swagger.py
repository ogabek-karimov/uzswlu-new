"""Swagger: ochiq sayt API'sining aniq tavsifi `frontend/docs/openapi.yaml` shartnomasidan olinadi.

Ko'rinishlar serializer'siz yozilgan, shuning uchun drf-spectacular o'zi faqat umumiy obyekt ko'rsata oladi.
Shartnoma esa har endpoint uchun parametr, javob shakli va misollarni allaqachon aniq beradi — postprocessing
hook shularni `/api` prefiksi bilan hujjatga qo'shadi, `/api/site/*` (Payload mos) uchun shu shakllarni qayta ishlatadi.
Frontend shartnomani o'zgartirsa Swagger o'zi yangilanadi (Docker'da `frontend/docs` o'qiladigan qilib ulangan).
"""
import copy
import re
from pathlib import Path

import yaml
from django.conf import settings

# /api/site/* da contract bilan bir xil javob beradigan manzillar
SITE_ALIASES = ['/posts', '/posts/{type}/{slug}', '/events', '/leadership', '/documents', '/videos',
                '/pages/{slug}', '/faculties', '/faculties/{slug}', '/sdg/{n}']
LANG_PARAM = {
    'name': 'lang', 'in': 'query', 'required': False,
    'description': 'Til: uz (standart), ru, en, zh. Tarjima bo‘lmasa o‘zbekcha qaytadi.',
    'schema': {'type': 'string', 'enum': ['uz', 'ru', 'en', 'zh'], 'default': 'uz'},
}
POST_EXTRA = {
    'imageWidth': {'type': ['integer', 'null'], 'description': 'Asosiy surat eni (px) — tik yoki yotiqligini bilish uchun'},
    'imageHeight': {'type': ['integer', 'null'], 'description': 'Asosiy surat bo‘yi (px)'},
    'translations': {
        'type': 'array', 'description': 'Post qaysi tillarda bor va har tildagi asosiy surat (Telegram’da 4 tilda ulashish uchun)',
        'items': {'$ref': '#/components/schemas/PostTranslation'},
    },
}
POST_TRANSLATION = {
    'type': 'object', 'required': ['lang'],
    'properties': {'lang': {'type': 'string', 'enum': ['uz', 'ru', 'en', 'zh']}, 'image': {'type': ['string', 'null'], 'format': 'uri'}},
}


def _contract_file() -> Path | None:
    for p in (settings.BASE_DIR.parent / 'frontend' / 'docs' / 'openapi.yaml', Path(__file__).parent / 'contract' / 'openapi.yaml'):
        if p.is_file():
            return p
    return None


def _norm(path: str) -> str:
    return re.sub(r'\{[^}]+\}', '{}', path)


METHODS = ('get', 'put', 'post', 'delete', 'patch')


def _flatten(item: dict) -> dict:
    """drf-spectacular faqat HTTP metodlarini kutadi: yo'l darajasidagi `parameters` har amalga ko'chiriladi."""
    shared = item.get('parameters', [])
    out = {m: item[m] for m in METHODS if isinstance(item.get(m), dict)}
    for op in out.values():
        if shared:
            op['parameters'] = [*shared, *op.get('parameters', [])]
    return out


def _tag(item: dict, tag: str, path: str, secure: bool | None = None) -> dict:
    item = _flatten(item)
    for method, op in item.items():
        if isinstance(op, dict) and 'responses' in op:
            op['tags'] = [tag]
            op['operationId'] = f"{method}_{re.sub(r'[^a-zA-Z0-9]+', '_', path).strip('_')}"
            if secure is False:
                op['security'] = []
    return item


def merge_contract(result, generator, request, public):
    f = _contract_file()
    if not f:
        return result
    contract = yaml.safe_load(f.read_text(encoding='utf-8'))
    paths = result.setdefault('paths', {})
    by_norm = {_norm(p): p for p in paths}

    def put(path: str, item: dict):
        old = by_norm.get(_norm(path))
        if old:
            del paths[old]
        paths[path] = item
        by_norm[_norm(path)] = path

    for path, item in contract['paths'].items():
        item = copy.deepcopy(item)
        put('/api' + path, _tag(item, 'Xodim kabineti' if path.startswith('/me') else 'Sayt API', '/api' + path))
    for path in SITE_ALIASES:  # Payload mos nusxa alohida ko'rsatilmaydi — asl amalning tavsifiga yozib qo'yiladi
        for op in paths['/api' + path].values():
            if isinstance(op, dict) and 'responses' in op:
                op['description'] = ((op.get('description') or '').rstrip() + f'\n\n_Payload mos nusxa: `/api/site{path}` — xuddi shu javob, token talab qilmaydi._').strip()

    # Shartnomada yo'q, lekin shu manzildagi qolgan /api/site/* ko'rinishlariga `lang` parametri
    for path, item in paths.items():
        if path.startswith('/api/site/') and not path.startswith('/api/site/hit'):
            for op in item.values():
                if isinstance(op, dict) and 'responses' in op and not any(p.get('name') == 'lang' for p in op.get('parameters', [])):
                    op.setdefault('parameters', []).append(LANG_PARAM)

    comps = result.setdefault('components', {})
    schemas = comps.setdefault('schemas', {})
    schemas.update(copy.deepcopy(contract['components'].get('schemas', {})))
    comps.setdefault('securitySchemes', {}).update(contract['components'].get('securitySchemes', {}))
    comps.setdefault('parameters', {}).update(contract['components'].get('parameters', {}))
    comps.setdefault('responses', {}).update(contract['components'].get('responses', {}))
    # Yangi frontend kutadigan maydonlar (shartnoma faylida hali yo'q bo'lishi mumkin)
    if 'Post' in schemas:
        schemas['Post'].setdefault('properties', {}).update({k: v for k, v in POST_EXTRA.items() if k not in schemas['Post']['properties']})
    schemas.setdefault('PostTranslation', POST_TRANSLATION)

    result['servers'] = [{'url': settings.PUBLIC_SERVER_URL, 'description': 'Shu backend'}]
    result['security'] = contract.get('security', [])
    return result


# ─── Tuzilma, avtorizatsiya, ruxsatlar ──────────────────────────────────────

INFO_DESCRIPTION = """
Sayt (Nuxt), Vue admin panel va xodim kabineti uchun yagona API. Matnlar `?lang=uz|ru|en|zh` bo‘yicha qaytadi (tarjima bo‘lmasa o‘zbekcha).

| Qayerda | Qanday kiriladi |
|---|---|
| Ochiq sayt API'si | `Authorization: Bearer <API_TOKEN>` (`bearerAuth`; `API_TOKEN` bo‘sh bo‘lsa shart emas) |
| Admin panel (`/api/cms/*`) | JWT (`panelJwt`) yoki sessiya cookie (`panelSession`) |
| Xodim kabineti (`/api/me*`) | HEMIS sessiyasi (`userSession`) yoki token (`staffBearer`) |

**Swagger'da sinash:** «Admin: Kirish» bo‘limidagi `POST /api/cms/users/login` ni bajaring, javobdagi `token` ni yuqoridagi **Authorize** → `panelJwt` ga kiriting.
"""

AUTH_TAG_DESCRIPTION = """
`POST /users/login` sessiya cookie’sini qo‘yadi va javobda `token` (JWT, HS256) qaytaradi. Cookie’siz: `Authorization: Bearer <token>`.
Yangilash — `POST /users/refresh-token`. Muddat — `JWT_TTL_SECONDS` (8 soat). JWT muddati tugasa, hisob yopilsa yoki parol o‘zgarsa bekor bo‘ladi (`401`).
5 marta noto‘g‘ri parol — hisob 15 daqiqaga bloklanadi (`423`). Yozish so‘rovlarida `Origin` ruxsat etilgan bo‘lishi shart (`TRUSTED_ORIGINS`).

**Rollar:** `superadmin` — hammasi · `editor` — kontent muharriri · `faculty` — fakultet admini · `pages` — sahifalar muharriri · `sdg` — BRM menejeri.
Har bir amalning tavsifida unga ruxsat etilgan rollar yozilgan. Xato shakli: `{"errors":[{"message":"…"}],"message":"…"}`.
"""

ALL_ROLES = {'superadmin', 'editor', 'faculty', 'pages', 'sdg'}
LABELS = {
    'users': 'Foydalanuvchilar', 'media': 'Media fayllar', 'categories': 'Kategoriyalar', 'posts': 'Postlar',
    'slides': 'Bosh sahifa slaydlari', 'leaders': 'Rahbariyat', 'doc-categories': 'Hujjat toifalari', 'documents': 'Hujjatlar',
    'video-categories': 'Video toifalari', 'videos': 'Videolar', 'faculties': 'Fakultetlar', 'departments': 'Kafedralar',
    'staff-profiles': 'Xodim profillari', 'sdg-goals': 'BRM maqsadlari', 'pages': 'Sahifalar',
    'login-events': 'Kirish tarixi', 'activity': 'Faollik jurnali',
    'settings': 'Sayt sozlamalari', 'symbols': 'Davlat ramzlari', 'video-page': 'Video sahifasi', 'sdg-page': 'BRM bosh sahifasi',
}
ADMIN_TAG = {
    'posts': 'Admin: Postlar', 'categories': 'Admin: Postlar',
    'media': 'Admin: Media',
    'pages': 'Admin: Sahifalar va hujjatlar', 'documents': 'Admin: Sahifalar va hujjatlar', 'doc-categories': 'Admin: Sahifalar va hujjatlar',
    'videos': 'Admin: Sahifalar va hujjatlar', 'video-categories': 'Admin: Sahifalar va hujjatlar', 'video-page': 'Admin: Sozlamalar',
    'slides': 'Admin: Tuzilma va bosh sahifa', 'leaders': 'Admin: Tuzilma va bosh sahifa', 'faculties': 'Admin: Tuzilma va bosh sahifa',
    'departments': 'Admin: Tuzilma va bosh sahifa', 'staff-profiles': 'Admin: Tuzilma va bosh sahifa',
    'sdg-goals': 'Admin: BRM', 'sdg-page': 'Admin: BRM',
    'users': 'Admin: Foydalanuvchilar va jurnal', 'login-events': 'Admin: Foydalanuvchilar va jurnal', 'activity': 'Admin: Foydalanuvchilar va jurnal',
    'settings': 'Admin: Sozlamalar', 'symbols': 'Admin: Sozlamalar',
}
PUBLIC_TAG = {
    '/home': 'Sayt: Umumiy', '/site': 'Sayt: Umumiy', '/search': 'Sayt: Umumiy', '/contact': 'Sayt: Umumiy', '/appeals': 'Sayt: Umumiy',
    '/posts': 'Sayt: Postlar', '/posts/{type}/{slug}': 'Sayt: Postlar', '/events': 'Sayt: Postlar',
    '/pages/{slug}': 'Sayt: Tuzilma', '/faculties': 'Sayt: Tuzilma', '/faculties/{slug}': 'Sayt: Tuzilma', '/programs': 'Sayt: Tuzilma',
    '/admission': 'Sayt: Tuzilma', '/leadership': 'Sayt: Tuzilma', '/staff': 'Sayt: Xodimlar', '/staff/{id}': 'Sayt: Xodimlar',
    '/documents': 'Sayt: Hujjat va video', '/documents/{id}/file': 'Sayt: Hujjat va video', '/videos': 'Sayt: Hujjat va video',
    '/sdg': 'Sayt: BRM', '/sdg/{n}': 'Sayt: BRM', '/hit': 'Sayt: Statistika',
}
EXTRA_SUMMARY = {
    '/documents/{id}/file': 'Hujjat faylini yuklab olish (PDF manziliga yo‘naltiradi, yuklab olishlar sonini oshiradi)',
    '/hit': 'Statistika yozuvi (sendBeacon; hech qachon xato qaytarmaydi, doim 204)',
}
COMPAT_SUMMARY = {
    '/api/site/latest': 'Oxirgi yangilik, e’lon va tadbirlar', '/api/site/index': 'Postlar indeksi (oylar va sanoqlar)',
    '/api/site/menu': 'Sayt menyusi', '/api/site/settings': 'Sayt sozlamalari', '/api/site/slides': 'Bosh sahifa slaydlari',
    '/api/site/symbols': 'Davlat ramzlari', '/api/site/sdg-goals': 'BRM 17 maqsadi', '/api/site/staff-hidden': 'Saytda yashirilgan xodimlar',
    '/api/site/staff/{id}': 'Xodimning qo‘shimcha profili', '/api/site/hit': 'Statistika yozuvi',
    '/api/site/documents/{id}/file': 'Hujjat faylini yuklab olish',
}
TAGS = [  # (nom, tavsif, guruh)
    ('Sayt: Umumiy', 'Bosh sahifa, umumiy ma’lumot, qidiruv, aloqa va virtual qabulxona.', 'Ochiq sayt API'),
    ('Sayt: Postlar', 'Yangiliklar, e’lonlar va tadbirlar.', 'Ochiq sayt API'),
    ('Sayt: Tuzilma', 'Sahifalar, fakultetlar, ta’lim yo‘nalishlari, qabul, rektorat.', 'Ochiq sayt API'),
    ('Sayt: Xodimlar', 'Xodimlar ro‘yxati va profili.', 'Ochiq sayt API'),
    ('Sayt: Hujjat va video', 'Me’yoriy hujjatlar va video darsliklar.', 'Ochiq sayt API'),
    ('Sayt: BRM', 'Barqaror rivojlanish maqsadlari.', 'Ochiq sayt API'),
    ('Sayt: Statistika', 'Sayt statistikasi yozuvi.', 'Ochiq sayt API'),
    ('Admin: Kirish', AUTH_TAG_DESCRIPTION, 'Admin panel API'),
    ('Admin: Postlar', 'Yangilik, e’lon, tadbir va kategoriyalar.', 'Admin panel API'),
    ('Admin: Media', 'Rasm, PDF va audio fayllar (yuklanganda WebP ga o‘tkaziladi).', 'Admin panel API'),
    ('Admin: Sahifalar va hujjatlar', 'Sahifalar, hujjatlar, videolar va ularning toifalari.', 'Admin panel API'),
    ('Admin: Tuzilma va bosh sahifa', 'Slaydlar, rahbariyat, fakultetlar, kafedralar, xodim profillari.', 'Admin panel API'),
    ('Admin: BRM', 'BRM maqsadlari va bosh sahifasi.', 'Admin panel API'),
    ('Admin: Sozlamalar', 'Sayt sozlamalari, davlat ramzlari, video sahifasi (+ sozlamalar tarixi).', 'Admin panel API'),
    ('Admin: Foydalanuvchilar va jurnal', 'Foydalanuvchilar, kirish tarixi, faollik jurnali.', 'Admin panel API'),
    ('Admin: Statistika va yordamchi', 'Boshqaruv paneli raqamlari, statistika, media foydalanilishi, YouTube, HEMIS.', 'Admin panel API'),
    ('Xodim kabineti', 'HEMIS orqali kirgan xodim: profil, rasm, hujjatlar.', 'Xodim kabineti va HEMIS'),
    ('HEMIS', 'HEMIS bilan ulanish: OAuth2 kirish va holat.', 'Xodim kabineti va HEMIS'),
    ('Eski manzillar (/api/site)', 'Payload CMS bilan mos manzillar (`NUXT_CMS_BASE=<backend>/api/site`). Token talab qilinmaydi. '
     'Postlar, tadbirlar, rahbariyat, hujjatlar, videolar, sahifalar, fakultetlar va BRM manzillari ham `/api/site/...` bilan ishlaydi — ular yuqoridagi ochiq API bilan bir xil.', 'Eski manzillar'),
]
PANEL_SECURITY = [{'panelJwt': []}, {'panelSession': []}]
ERROR_SCHEMA = {
    'type': 'object',
    'properties': {
        'errors': {'type': 'array', 'items': {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        'message': {'type': 'string'},
    },
}
ACTION_LABEL = {'read': 'o‘qish', 'create': 'yaratish', 'update': 'o‘zgartirish', 'delete': 'o‘chirish'}


def _roles_line(roles, action: str) -> str:
    if not roles:
        return ''
    r = set(roles)
    who = 'barcha rollar' if r >= ALL_ROLES else ', '.join(f'`{x}`' for x in sorted(r))
    return f'**Ruxsat ({ACTION_LABEL[action]}):** {who}'


def _err(desc: str) -> dict:
    return {'description': desc, 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ApiError'}}}}


def _clone(op: dict, *, path: str, tag: str, summary: str, op_id: str, roles_line: str = '', drop_params=('slug',), note: str = '') -> dict:
    op = copy.deepcopy(op)
    op['tags'], op['summary'], op['operationId'] = [tag], summary, op_id
    op['parameters'] = [p for p in op.get('parameters', []) if p.get('name') not in drop_params]
    if not op['parameters']:
        op.pop('parameters')
    op['description'] = '\n\n'.join(x for x in (note, roles_line) if x)
    op['security'] = copy.deepcopy(PANEL_SECURITY)
    op['responses'].setdefault('401', _err('Kirilmagan yoki JWT yaroqsiz / muddati tugagan'))
    op['responses'].setdefault('403', _err('Rolingizga bu amal ruxsat etilmagan yoki Origin ruxsat etilmagan'))
    return op


def _expand_admin(paths: dict) -> None:
    """Umumiy `/api/cms/{slug}` o'rniga har bir kolleksiya uchun alohida, o'z ruxsatlari bilan amallar."""
    from apps.panel.collections import REGISTRY
    from apps.panel.globals_ import GLOBALS

    g_list, g_doc, g_count = paths.pop('/api/cms/{slug}', {}), paths.pop('/api/cms/{slug}/{id}', {}), paths.pop('/api/cms/{slug}/count', {})
    g_vlist, g_vdoc = paths.pop('/api/cms/{slug}/versions', {}), paths.pop('/api/cms/{slug}/versions/{vid}', {})
    gg, gg_vlist, gg_vdoc = (paths.pop('/api/cms/globals/{slug}', {}), paths.pop('/api/cms/globals/{slug}/versions', {}),
                             paths.pop('/api/cms/globals/{slug}/versions/{vid}', {}))

    for slug, coll in REGISTRY.items():
        label, tag, acc = LABELS[slug], ADMIN_TAG[slug], coll.access
        base = f'/api/cms/{slug}'
        lst, doc = {}, {}
        if 'read' in acc:
            lst['get'] = _clone(g_list['get'], path=base, tag=tag, summary=f'{label}: ro‘yxat', op_id=f'cms_{slug}_list', roles_line=_roles_line(acc['read'], 'read'))
            doc['get'] = _clone(g_doc['get'], path=base, tag=tag, summary=f'{label}: bitta yozuv', op_id=f'cms_{slug}_get', roles_line=_roles_line(acc['read'], 'read'))
            paths[f'{base}/count'] = {'get': _clone(g_count['get'], path=base, tag=tag, summary=f'{label}: soni', op_id=f'cms_{slug}_count', roles_line=_roles_line(acc['read'], 'read'))}
        if 'create' in acc:
            note = 'Fayl `multipart/form-data` bilan yuboriladi: `file` + `_payload` (JSON).' if slug == 'media' else ''
            lst['post'] = _clone(g_list['post'], path=base, tag=tag, summary=f'{label}: yaratish', op_id=f'cms_{slug}_create', roles_line=_roles_line(acc['create'], 'create'), note=note)
        if 'update' in acc:
            doc['patch'] = _clone(g_doc['patch'], path=base, tag=tag, summary=f'{label}: o‘zgartirish', op_id=f'cms_{slug}_update', roles_line=_roles_line(acc['update'], 'update'))
        if 'delete' in acc:
            note = 'Post savatga tushadi; savatdagisi butunlay o‘chiriladi.' if slug == 'posts' else ''
            doc['delete'] = _clone(g_doc['delete'], path=base, tag=tag, summary=f'{label}: o‘chirish', op_id=f'cms_{slug}_delete', roles_line=_roles_line(acc['delete'], 'delete'), note=note)
        if slug == 'posts':  # ommaviy amallar faqat postlarda ishlatiladi
            lst['patch'] = _clone(g_list['patch'], path=base, tag=tag, summary='Postlar: ommaviy o‘zgartirish (`where` bo‘yicha)', op_id='cms_posts_bulk_update', roles_line=_roles_line(acc['update'], 'update'))
            lst['delete'] = _clone(g_list['delete'], path=base, tag=tag, summary='Postlar: ommaviy o‘chirish (`where` bo‘yicha)', op_id='cms_posts_bulk_delete', roles_line=_roles_line(acc['delete'], 'delete'))
        if coll.versions:
            paths[f'{base}/versions'] = {'get': _clone(g_vlist['get'], path=base, tag=tag, summary=f'{label}: saqlangan holatlar', op_id=f'cms_{slug}_versions', roles_line=_roles_line(acc.get('update'), 'update'))}
            paths[f'{base}/versions/{{vid}}'] = {'post': _clone(g_vdoc['post'], path=base, tag=tag, summary=f'{label}: shu holatga qaytarish', op_id=f'cms_{slug}_restore', roles_line=_roles_line(acc.get('update'), 'update'))}
        if lst:
            paths[base] = lst
        if doc:
            paths[f'{base}/{{id}}'] = doc

    for slug, g in GLOBALS.items():
        label, tag, acc = LABELS[slug], ADMIN_TAG[slug], g.access
        base = f'/api/cms/globals/{slug}'
        item = {}
        if acc.get('read') is not None or 'read' in acc:
            item['get'] = _clone(gg['get'], path=base, tag=tag, summary=f'{label}: o‘qish', op_id=f'cms_global_{slug}_get', roles_line=_roles_line(acc.get('read'), 'read') or 'Ochiq: kirgan har qanday xodim')
        item['post'] = _clone(gg['post'], path=base, tag=tag, summary=f'{label}: saqlash', op_id=f'cms_global_{slug}_save', roles_line=_roles_line(acc.get('update'), 'update'))
        paths[base] = item
        if g.versions:
            paths[f'{base}/versions'] = {'get': _clone(gg_vlist['get'], path=base, tag=tag, summary=f'{label}: o‘zgarishlar tarixi', op_id=f'cms_global_{slug}_versions', roles_line=_roles_line(acc.get('update'), 'update'))}
            paths[f'{base}/versions/{{vid}}'] = {'post': _clone(gg_vdoc['post'], path=base, tag=tag, summary=f'{label}: shu holatga qaytarish', op_id=f'cms_global_{slug}_restore', roles_line=_roles_line(acc.get('update'), 'update'))}


def finalize(result, generator, request, public):
    """Swagger'ni tartibga solish: tuzilma, teglar, avtorizatsiya sxemalari, ruxsatlar."""
    result['info']['description'] = INFO_DESCRIPTION.strip()
    comps = result.setdefault('components', {})
    comps.setdefault('schemas', {})['ApiError'] = ERROR_SCHEMA
    schemes = comps.setdefault('securitySchemes', {})
    schemes['bearerAuth'] = {'type': 'http', 'scheme': 'bearer', 'description': 'Ochiq sayt API’si: `API_TOKEN` (backend/.env). Bo‘sh bo‘lsa tekshirilmaydi.'}
    schemes['panelJwt'] = {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT', 'description': 'Admin panel JWT (HS256): `POST /api/cms/users/login` javobidagi `token`.'}
    schemes['panelSession'] = {'type': 'apiKey', 'in': 'cookie', 'name': settings.SESSION_COOKIE_NAME,
                               'description': 'Admin panel sessiya cookie’si (login qilganda qo‘yiladi). Yozish uchun Origin ruxsat etilgan bo‘lishi kerak.'}
    schemes['staffBearer'] = {'type': 'http', 'scheme': 'bearer', 'description': 'Xodim kabineti tokeni (`issue_staff_session` yoki HEMIS kirishi natijasi).'}

    paths = result['paths']
    _expand_admin(paths)

    for path, item in paths.items():
        for method, op in item.items():
            if not isinstance(op, dict) or 'responses' not in op:
                continue
            if path.startswith('/api/cms/users/') or path in ('/api/cms/users/login',):
                tail = path.removeprefix('/api/cms/')
                op['tags'] = ['Admin: Kirish']
                open_ = tail == 'users/login'
                op['security'] = [] if open_ else (copy.deepcopy(PANEL_SECURITY) + [{}] if tail == 'users/me' else copy.deepcopy(PANEL_SECURITY))
                if open_:
                    op['responses'].setdefault('401', _err('Login yoki parol noto‘g‘ri'))
                    op['responses'].setdefault('423', _err('5 marta xato — hisob 15 daqiqaga bloklangan'))
                else:
                    op['responses'].setdefault('401', _err('Kirilmagan yoki JWT yaroqsiz / muddati tugagan'))
                if tail == 'users/unlock':
                    op['description'] = (op.get('description') or '') + '\n\nRuxsat: faqat `superadmin`.'
            elif path.startswith('/api/cms/panel/'):
                op['tags'] = ['Admin: Statistika va yordamchi']
                op['security'] = copy.deepcopy(PANEL_SECURITY)
                op['responses'].setdefault('401', _err('Kirilmagan yoki JWT yaroqsiz / muddati tugagan'))
                op['responses'].setdefault('403', _err('Rolingizga bu amal ruxsat etilmagan'))
            elif path.startswith('/api/me'):
                op['tags'] = ['Xodim kabineti']
                op['security'] = [{'userSession': []}, {'staffBearer': []}]
                op['responses'].setdefault('401', _err('Xodim kirmagan'))
            elif path.startswith('/api/auth/hemis'):
                op['tags'] = ['HEMIS']
            elif path.startswith('/api/site/'):
                op['tags'] = ['Eski manzillar (/api/site)']
                op['security'] = []
                op.setdefault('summary', COMPAT_SUMMARY.get(path, op.get('summary') or path))
            elif path.startswith('/api/') and not path.startswith('/api/cms'):
                key = path.removeprefix('/api')
                if key in PUBLIC_TAG:
                    op['tags'] = [PUBLIC_TAG[key]]
                if key in EXTRA_SUMMARY and not op.get('summary'):
                    op['summary'] = EXTRA_SUMMARY[key]
                if key in ('/hit', '/appeals'):
                    op['security'] = [] if key == '/hit' else op.get('security', [])

    used = {t for item in paths.values() for op in item.values() if isinstance(op, dict) for t in op.get('tags', [])}
    result['tags'] = [{'name': n, 'description': d.strip()} for n, d, _ in TAGS if n in used]
    groups: dict[str, list[str]] = {}
    for n, _, g in TAGS:
        if n in used:
            groups.setdefault(g, []).append(n)
    result['x-tagGroups'] = [{'name': g, 'tags': t} for g, t in groups.items()]  # Redoc
    return result
