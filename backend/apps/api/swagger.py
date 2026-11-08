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

**Swagger'da sinash:** sahifa tepasidagi **«Sinash uchun kirish»** paneliga login/parolni (2FA bo‘lsa kodni ham) kiriting — token `Authorize` → `panelJwt` ga o‘zi qo‘yiladi, rolingizga ruxsat etilmagan amallar xiralashadi («faqat menga ruxsat etilganlar» filtri ham bor). Qo‘lda: `POST /api/cms/users/login` → javobdagi `token` ni **Authorize** ga kiriting.

**Rol bo‘yicha sxema:** `/api/schema/?role=editor` — faqat shu rolga ruxsat etilgan amallar (har amalda `x-roles`, yozuv darajasidagi qoidalar — `Qoida:`).
"""

AUTH_TAG_DESCRIPTION = """
`POST /users/login` sessiya cookie’sini qo‘yadi va javobda `token` (JWT, HS256) qaytaradi. Cookie’siz: `Authorization: Bearer <token>`.
2FA yoqilgan hisobda login `twoFactorRequired` va `challenge` qaytaradi — `POST /users/login/2fa` bilan kodni yuboring. Yangilash — `POST /users/refresh-token`. Muddat — `JWT_TTL_SECONDS` (8 soat). JWT muddati tugasa, chiqilsa (`POST /users/logout`), yangilansa, hisob yopilsa yoki parol o‘zgarsa bekor bo‘ladi (`401`).
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
    ('Admin: Kirish', 'Login, JWT, yangilash, joriy foydalanuvchi, chiqish.', 'Admin panel API'),
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
    ('Eski manzillar (/api/site)', 'Payload CMS bilan mos manzillar (`NUXT_CMS_BASE`). Token talab qilinmaydi.', 'Eski manzillar'),
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


def _ref(name: str) -> dict:
    return {'$ref': f'#/components/schemas/{name}'}


def _json(schema: dict, desc: str) -> dict:
    return {'description': desc, 'content': {'application/json': {'schema': schema}}}


Q = {  # so'rov parametrlari
    'where': lambda required=False: {
        'name': 'where', 'in': 'query', 'required': required, 'style': 'deepObject', 'explode': True,
        'schema': {'type': 'object', 'additionalProperties': True},
        'description': ('**Majburiy** (tasodifan butun jadvalga tegmaslik uchun; ko‘pi bilan 500 yozuv). ' if required else '')
        + 'Payload filtri: `where[id][in]=1,2,3`, `where[title.uz][like]=…`, `where[and][0][status][equals]=published`.',
    },
    'sort': {'name': 'sort', 'in': 'query', 'schema': {'type': 'string'}, 'description': 'Saralash: `-publishedAt`, `order`.'},
    'limit': {'name': 'limit', 'in': 'query', 'schema': {'type': 'integer', 'default': 10, 'maximum': 100}},
    'page': {'name': 'page', 'in': 'query', 'schema': {'type': 'integer', 'default': 1, 'minimum': 1}},
    'depth': {'name': 'depth', 'in': 'query', 'schema': {'type': 'integer', 'minimum': 0, 'maximum': 3, 'default': 2},
              'description': '0 — bog‘liq yozuvlar faqat ID, 1+ — to‘liq obyekt.'},
    'trash': {'name': 'trash', 'in': 'query', 'schema': {'type': 'boolean'},
              'description': '`true` — savatdagi (o‘chirilgan) postlar ham ko‘rinadi / tahrirlanadi.'},
    'id': {'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}},
    'vid': {'name': 'vid', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}, 'description': 'Saqlangan holat (version) ID si.'},
}


def _p(*names, where_required=False) -> list:
    out = []
    for n in names:
        p = Q[n](where_required) if n == 'where' else Q[n]
        out.append(copy.deepcopy(p))
    return out


def _op(*, tag, summary, op_id, action, roles, ok, ok_desc, ok_schema, params=(), body=None, note='', rules='',
        extra=None, codes=('401', '403', '429')):
    """Bitta admin amali: ruxsat etilgan rollar (`x-roles`), aniq javob kodlari va sxemalar."""
    desc = '\n\n'.join(x for x in (note, _roles_line(roles, action), f'**Qoida:** {rules}' if rules else '') if x)
    op = {'tags': [tag], 'summary': summary, 'operationId': op_id, 'description': desc, 'security': copy.deepcopy(PANEL_SECURITY),
          'x-roles': sorted(roles), 'responses': {ok: _json(ok_schema, ok_desc)}}
    if params:
        op['parameters'] = list(params)
    if body:
        op['requestBody'] = body
    op['responses'].update(extra or {})
    msgs = {'401': 'Kirilmagan yoki JWT yaroqsiz / muddati tugagan', '403': 'Roling bu amalga ruxsat bermaydi, yozuv doirangdan tashqarida yoki Origin ruxsat etilmagan',
            '429': 'So‘rovlar juda ko‘p (throttle)'}
    for c in codes:
        op['responses'][c] = _err(msgs[c])
    return op


def _probe(coll, action: str) -> set:
    """Ommaviy amal yozuvsiz (`obj=None`) tekshiriladi — haqiqiy `can()` har rol uchun chaqiriladi (qo'lda ro'yxat emas)."""
    from apps.accounts.models import User
    return {r for r in ALL_ROLES if coll.can(User(username=f'probe_{r}', role=r, status='active'), action)}


def _body(schema_name: str) -> dict:
    return {'required': True, 'content': {'application/json': {'schema': _ref(schema_name)}}}


MEDIA_BODY = {'required': True, 'content': {'multipart/form-data': {'schema': {
    'type': 'object', 'required': ['file'],
    'properties': {
        'file': {'type': 'string', 'format': 'binary', 'description': 'Rasm (jpg/png/gif/webp → WebP), PDF yoki audio. Hajm va tur serverda tekshiriladi (`413`/`400`).'},
        '_payload': {'type': 'string', 'description': 'JSON satr: `{"alt":{"uz":"…","ru":"…"},"folder":"posts"}`'},
    }}}}}
DOC_ID = {'type': 'object', 'properties': {'doc': {'type': 'object', 'properties': {'id': {'type': 'integer'}}}, 'message': {'type': 'string'}}}
BULK = {'type': 'object', 'properties': {
    'docs': {'type': 'array', 'items': {}},
    'errors': {'type': 'array', 'description': 'Ruxsati yo‘q yoki xato bergan yozuvlar; qolganlari saqlangan.',
               'items': {'type': 'object', 'properties': {'id': {'type': 'integer'}, 'message': {'type': 'string'}}}}}}


def _expand_admin(paths: dict, schemas: dict) -> None:
    """Umumiy `/api/cms/{slug}` o'rniga har bir kolleksiya uchun alohida, o'z ruxsatlari va sxemalari bilan amallar."""
    from apps.panel.collections import REGISTRY
    from apps.panel.globals_ import GLOBALS
    from . import swagger_fields as sf

    for k in ('/api/cms/{slug}', '/api/cms/{slug}/{id}', '/api/cms/{slug}/count', '/api/cms/{slug}/versions',
              '/api/cms/{slug}/versions/{vid}', '/api/cms/globals/{slug}', '/api/cms/globals/{slug}/versions',
              '/api/cms/globals/{slug}/versions/{vid}'):
        paths.pop(k, None)

    schemas['PanelI18n'] = {'type': 'object', 'description': 'To‘rt tilli matn.', 'properties': {l: {'type': 'string'} for l in ('uz', 'ru', 'en', 'zh')}}
    schemas['PanelMedia'] = sf.media_schema()
    schemas['PanelPage'] = sf.PAGED

    for slug, coll in REGISTRY.items():
        label, tag, acc, rules = LABELS[slug], ADMIN_TAG[slug], coll.access, getattr(coll, 'rules', {}) or {}
        name = sf.pascal(slug)
        resp = sf.response_schema(coll)
        schemas[name] = resp
        schemas[f'{name}Input'] = sf.input_schema(coll, resp)
        schemas[f'{name}List'] = {'allOf': [_ref('PanelPage'), {'type': 'object', 'properties': {'docs': {'type': 'array', 'items': _ref(name)}}}]}
        base = f'/api/cms/{slug}'
        trash = slug == 'posts'
        lst, doc = {}, {}
        R = lambda a: acc.get(a, ())
        if 'read' in acc:
            r = rules.get('read', '')
            lst['get'] = _op(tag=tag, summary=f'{label}: ro‘yxat', op_id=f'cms_{slug}_list', action='read', roles=R('read'), rules=r,
                             ok='200', ok_desc='Sahifalangan ro‘yxat', ok_schema=_ref(f'{name}List'),
                             params=_p('where', 'sort', 'limit', 'page', 'depth', *(['trash'] if trash else [])))
            doc['get'] = _op(tag=tag, summary=f'{label}: bitta yozuv', op_id=f'cms_{slug}_get', action='read', roles=R('read'), rules=r,
                             ok='200', ok_desc='Yozuv', ok_schema=_ref(name), params=_p('id', 'depth', *(['trash'] if trash else [])),
                             extra={'404': _err('Yozuv topilmadi yoki doirangizdan tashqarida')})
            paths[f'{base}/count'] = {'get': _op(tag=tag, summary=f'{label}: soni', op_id=f'cms_{slug}_count', action='read', roles=R('read'),
                                                 ok='200', ok_desc='Soni', ok_schema={'type': 'object', 'properties': {'totalDocs': {'type': 'integer'}}},
                                                 params=_p('where'))}
        if 'create' in acc:
            lst['post'] = _op(tag=tag, summary=f'{label}: yaratish', op_id=f'cms_{slug}_create', action='create', roles=R('create'), rules=rules.get('create', ''),
                              ok='201', ok_desc='Yaratildi', ok_schema={'type': 'object', 'properties': {'doc': _ref(name), 'message': {'type': 'string'}}},
                              body=MEDIA_BODY if slug == 'media' else _body(f'{name}Input'),
                              note='Fayl `multipart/form-data` bilan yuboriladi: `file` + `_payload` (JSON).' if slug == 'media' else '',
                              extra={'400': _err('Tekshiruvdan o‘tmadi (maydon xatolari `errors` da)'), '409': _err('Takroriy qiymat (slug, username …)')})
        if 'update' in acc:
            r = rules.get('update', '')
            note = ('Savatdan tiklash: `PATCH /api/cms/posts/{id}?trash=true` tanasi `{"deletedAt": null}`.' if trash else '')
            doc['patch'] = _op(tag=tag, summary=f'{label}: o‘zgartirish', op_id=f'cms_{slug}_update', action='update', roles=R('update'), rules=r,
                               ok='200', ok_desc='Saqlandi', ok_schema={'type': 'object', 'properties': {'doc': _ref(name), 'message': {'type': 'string'}}},
                               params=_p('id', 'depth', *(['trash'] if trash else [])), body=_body(f'{name}Input'), note=note,
                               extra={'400': _err('Tekshiruvdan o‘tmadi'), '404': _err('Yozuv topilmadi yoki doirangizdan tashqarida'),
                                      '409': _err('Takroriy qiymat yoki boshqa foydalanuvchi o‘zgartirib bo‘lgan')})
            lst['patch'] = _op(tag=tag, summary=f'{label}: ommaviy o‘zgartirish', op_id=f'cms_{slug}_bulk_update', action='update', roles=_probe(coll, 'update'), rules=r,
                               ok='200', ok_desc='Natija (qisman muvaffaqiyat mumkin)', ok_schema=BULK,
                               params=_p('where', 'sort', 'depth', where_required=True), body=_body(f'{name}Input'),
                               note='Bir xil o‘zgarish `where` ga mos hamma yozuvga (ko‘pi bilan 500). Har yozuv uchun ruxsat alohida tekshiriladi — ruxsatsizlari `errors` da qoladi.',
                               extra={'400': _err('`where` yo‘q yoki noto‘g‘ri')})
        if 'delete' in acc:
            r = rules.get('delete', '')
            note = 'Post savatga tushadi; savatdagisi (`?trash=true`) butunlay o‘chiriladi.' if trash else ''
            doc['delete'] = _op(tag=tag, summary=f'{label}: o‘chirish', op_id=f'cms_{slug}_delete', action='delete', roles=R('delete'), rules=r,
                                ok='200', ok_desc='O‘chirildi (204 emas — javob tanasi bor)', ok_schema=DOC_ID,
                                params=_p('id', *(['trash'] if trash else [])), note=note,
                                extra={'404': _err('Yozuv topilmadi yoki doirangizdan tashqarida'), '409': _err('Boshqa yozuvlar unga bog‘langan')})
            lst['delete'] = _op(tag=tag, summary=f'{label}: ommaviy o‘chirish', op_id=f'cms_{slug}_bulk_delete', action='delete', roles=_probe(coll, 'delete'), rules=r,
                                ok='200', ok_desc='Natija (qisman muvaffaqiyat mumkin)', ok_schema=BULK,
                                params=_p('where', *(['trash'] if trash else []), where_required=True),
                                note=('Postlar savatga tushadi. ' if trash else '') + 'Har yozuv uchun ruxsat alohida tekshiriladi.',
                                extra={'400': _err('`where` yo‘q yoki noto‘g‘ri')})
        if coll.versions:
            paths[f'{base}/versions'] = {'get': _op(tag=tag, summary=f'{label}: saqlangan holatlar', op_id=f'cms_{slug}_versions', action='read', roles=R('read'),
                                                    ok='200', ok_desc='Holatlar ro‘yxati', ok_schema=_ref('PanelPage'), params=_p('where', 'sort', 'limit', 'page'))}
            paths[f'{base}/versions/{{vid}}'] = {'post': _op(tag=tag, summary=f'{label}: shu holatga qaytarish', op_id=f'cms_{slug}_restore', action='update', roles=R('update'),
                                                             ok='200', ok_desc='Qaytarildi', ok_schema={'type': 'object', 'properties': {'doc': _ref(name), 'message': {'type': 'string'}}},
                                                             params=_p('vid'), rules=rules.get('update', ''), extra={'404': _err('Holat yoki yozuv topilmadi')})}
        if lst:
            paths[base] = lst
        if doc:
            paths[f'{base}/{{id}}'] = doc

    for slug, g in GLOBALS.items():
        label, tag, acc = LABELS[slug], ADMIN_TAG[slug], g.access
        base = f'/api/cms/globals/{slug}'
        read_roles = acc.get('read') or ALL_ROLES
        item = {'get': _op(tag=tag, summary=f'{label}: o‘qish', op_id=f'cms_global_{slug}_get', action='read', roles=read_roles,
                           ok='200', ok_desc='Joriy qiymat', ok_schema={'type': 'object'}, params=_p('depth'),
                           note='' if acc.get('read') else '**Ochiq:** token shart emas (ommaviy sayt ma’lumoti; admin paneldagi «Texnik yordam» tugmasi uchun).'),
                'post': _op(tag=tag, summary=f'{label}: saqlash', op_id=f'cms_global_{slug}_save', action='update', roles=acc.get('update', ()),
                            ok='200', ok_desc='Saqlandi', ok_schema={'type': 'object', 'properties': {'result': {'type': 'object'}, 'message': {'type': 'string'}}},
                            body={'required': True, 'content': {'application/json': {'schema': {'type': 'object'}}}},
                            extra={'400': _err('Tekshiruvdan o‘tmadi')})}
        if not acc.get('read'):
            item['get']['security'] = [{}, *copy.deepcopy(PANEL_SECURITY)]  # tokensiz ham mumkin
            item['get']['x-roles'] = sorted(ALL_ROLES)
            item['get']['x-anonymous'] = True
        paths[base] = item
        if g.versions:
            paths[f'{base}/versions'] = {'get': _op(tag=tag, summary=f'{label}: o‘zgarishlar tarixi', op_id=f'cms_global_{slug}_versions', action='read', roles=read_roles,
                                                    ok='200', ok_desc='Holatlar', ok_schema=_ref('PanelPage'), params=_p('limit', 'page'))}
            paths[f'{base}/versions/{{vid}}'] = {'post': _op(tag=tag, summary=f'{label}: shu holatga qaytarish', op_id=f'cms_global_{slug}_restore', action='update', roles=acc.get('update', ()),
                                                             ok='200', ok_desc='Qaytarildi', ok_schema={'type': 'object'}, params=_p('vid'),
                                                             extra={'404': _err('Holat topilmadi')})}


def _panel_roles() -> dict:
    """Kolleksiyaga tegishli bo'lmagan panel amallari: (method, yo'l) → rollar. `tests/security/test_role_matrix.py` haqiqatga tekshiradi."""
    from apps.panel import collections as c
    media, every, sup = c.MEDIA_ROLES, c.ALL, c.SUPER
    return {
        '/api/cms/panel/overview': every, '/api/cms/panel/hemis': every, '/api/cms/panel/sdg-counts': every,
        '/api/cms/panel/media-stats': media, '/api/cms/panel/media-used': media, '/api/cms/panel/youtube': media,
        '/api/cms/panel/media-usage/{id}': media, '/api/cms/panel/stats': sup,
        '/api/cms/users/unlock': sup, '/api/cms/users/2fa/reset': sup, '/api/cms/private/{name}': sup,
    }


def _tag_roles(paths: dict) -> None:
    """Kolleksiyaga tegishli bo'lmagan `/api/cms/*` amallariga ham `x-roles` (yoki ochiq bo'lsa `x-public`)."""
    special = {_norm(k): v for k, v in _panel_roles().items()}
    for path, item in paths.items():
        if not path.startswith('/api/cms/'):
            continue
        for op in item.values():
            if not isinstance(op, dict) or 'responses' not in op or 'x-roles' in op:
                continue
            if path in ('/api/cms/users/login', '/api/cms/users/login/2fa'):
                op['x-public'] = True
                continue
            roles = special.get(_norm(path), ALL_ROLES)
            op['x-roles'] = sorted(roles)
            line = '**Ruxsat:** ' + ('kirgan har qanday xodim' if set(roles) >= ALL_ROLES else ', '.join(f'`{x}`' for x in sorted(roles)))
            op['description'] = ((op.get('description') or '').rstrip() + '\n\n' + line).strip()


def filter_by_role(schema: dict, role: str) -> dict:
    """`?role=editor` — shu rolga ruxsat etilmagan admin amallari olib tashlanadi (ochiq sayt API'si o'zgarmaydi)."""
    schema = copy.deepcopy(schema)
    for path in list(schema.get('paths', {})):
        item = schema['paths'][path]
        for m in list(item):
            op = item[m]
            if isinstance(op, dict) and 'x-roles' in op and role not in op['x-roles']:
                del item[m]
        if not any(isinstance(v, dict) and 'responses' in v for v in item.values()):
            del schema['paths'][path]
    used = {t for i in schema['paths'].values() for o in i.values() if isinstance(o, dict) for t in o.get('tags', [])}
    schema['tags'] = [t for t in schema.get('tags', []) if t['name'] in used]
    for g in schema.get('x-tagGroups', []):
        g['tags'] = [t for t in g['tags'] if t in used]
    schema['x-tagGroups'] = [g for g in schema.get('x-tagGroups', []) if g['tags']]
    schema['info']['title'] = f"{schema['info'].get('title', 'API')} — rol: {role}"
    return schema


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
    _expand_admin(paths, comps['schemas'])

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
                    op['description'] = ((op.get('description') or '').rstrip() + '\n\n' + AUTH_TAG_DESCRIPTION.strip()).strip()
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

    _tag_roles(paths)

    used = {t for item in paths.values() for op in item.values() if isinstance(op, dict) for t in op.get('tags', [])}
    result['tags'] = [{'name': n, 'description': d.strip()} for n, d, _ in TAGS if n in used]
    groups: dict[str, list[str]] = {}
    for n, _, g in TAGS:
        if n in used:
            groups.setdefault(g, []).append(n)
    result['x-tagGroups'] = [{'name': g, 'tags': t} for g, t in groups.items()]  # Redoc
    return result
