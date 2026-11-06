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
    for path in SITE_ALIASES:
        item = copy.deepcopy(contract['paths'][path])
        put('/api/site' + path, _tag(item, 'Sayt (Payload mos)', '/api/site' + path, secure=False))

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


# ─── Avtorizatsiya va ruxsatlar ─────────────────────────────────────────────

AUTH_DESCRIPTION = """
## Avtorizatsiya

| Qayerda | Sxema | Qanday olinadi |
|---|---|---|
| Ochiq sayt API'si (`/api/home`, `/api/posts`, …) | **bearerAuth** — `Authorization: Bearer <API_TOKEN>` | `backend/.env` dagi `API_TOKEN` (bo‘sh bo‘lsa shart emas). `/api/site/*` va `/api/hit` tokensiz ochiq |
| Admin panel API'si (`/api/cms/*`) | **panelJwt** — `Authorization: Bearer <JWT>` | `POST /api/cms/users/login` javobidagi `token`. Muddati `JWT_TTL_SECONDS` (8 soat), `POST /api/cms/users/refresh-token` bilan yangilanadi |
| Admin panel (brauzer) | **panelSession** — sessiya cookie | Vue admin panel login qilganda o‘zi qo‘yadi. Yozish so‘rovlari uchun `Origin` ruxsat etilgan (`TRUSTED_ORIGINS`) bo‘lishi shart |
| Xodim kabineti (`/api/me*`) | **userSession** (cookie) yoki **staffBearer** | HEMIS orqali kirish; sinash uchun `python manage.py issue_staff_session <hemis_id>` |

**Swagger'da sinash:** `/api/cms/users/login` ni "Try it out" bilan bajaring → javobdagi `token` ni yuqoridagi **Authorize** tugmasiga (`panelJwt`) kiriting.

JWT amal qilmaydi: muddati tugagan, hisob yopilgan (`disabled`) yoki parol o‘zgargan bo‘lsa (`401`).
Ruxsat yetmasa `403`, kirmagan bo‘lsa `401`; xato shakli `{"errors":[{"message":"…"}],"message":"…"}`.

## Rollar
`superadmin` — hammasi · `editor` — kontent muharriri · `faculty` — fakultet admini · `pages` — sahifalar muharriri · `sdg` — BRM menejeri.
Har bir kolleksiya uchun ruxsatlar jadvali tegishli amalning tavsifida (o‘qish, yaratish, o‘zgartirish, o‘chirish).
"""

PANEL_SECURITY = [{'panelJwt': []}, {'panelSession': []}]
ACTION_BY_OP = {  # (yo'l turi, metod) -> amal
    ('list', 'get'): 'read', ('list', 'post'): 'create', ('list', 'patch'): 'update', ('list', 'delete'): 'delete',
    ('doc', 'get'): 'read', ('doc', 'patch'): 'update', ('doc', 'delete'): 'delete', ('count', 'get'): 'read',
}
ACTION_LABEL = {'read': 'o‘qish', 'create': 'yaratish', 'update': 'o‘zgartirish', 'delete': 'o‘chirish'}
ERROR_SCHEMA = {
    'type': 'object',
    'properties': {
        'errors': {'type': 'array', 'items': {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        'message': {'type': 'string'},
    },
}


def _role_cell(roles) -> str:
    if roles is None:
        return 'ochiq'
    names = sorted(roles)
    return ', '.join(f'`{r}`' for r in names) if names else '—'


def _matrix(action: str, with_globals: bool = False) -> str:
    from apps.panel.collections import REGISTRY
    from apps.panel.globals_ import GLOBALS
    rows = [(slug, c.access.get(action, frozenset())) for slug, c in REGISTRY.items() if action in c.access]
    if with_globals:
        rows = [(slug, g.access.get(action, frozenset())) for slug, g in GLOBALS.items() if action in g.access]
    lines = [f'**Ruxsat — {ACTION_LABEL[action]}** (rol bo‘yicha):', '', '| Kolleksiya | Ruxsat etilgan rollar |', '|---|---|']
    lines += [f'| `{slug}` | {_role_cell(roles)} |' for slug, roles in rows]
    return '\n'.join(lines)


def _kind(path: str) -> str | None:
    tail = path.removeprefix('/api/cms/')
    if tail.startswith(('users/', 'panel/', 'globals/')) or '/versions' in tail:
        return None
    if tail.endswith('/count'):
        return 'count'
    return 'doc' if tail.endswith('/{id}') else 'list'


def document_auth(result, generator, request, public):
    from apps.panel.collections import REGISTRY
    from apps.panel.globals_ import GLOBALS
    import copy as _copy

    result['info']['description'] = (result['info'].get('description') or '') + '\n' + AUTH_DESCRIPTION
    schemes = result.setdefault('components', {}).setdefault('securitySchemes', {})
    schemes['bearerAuth'] = {
        'type': 'http', 'scheme': 'bearer',
        'description': 'Ochiq sayt API’si: `API_TOKEN` (backend/.env). Bo‘sh bo‘lsa tekshirilmaydi.',
    }
    schemes['panelJwt'] = {
        'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT',
        'description': 'Admin panel JWT (HS256): `POST /api/cms/users/login` javobidagi `token`.',
    }
    schemes['panelSession'] = {
        'type': 'apiKey', 'in': 'cookie', 'name': settings.SESSION_COOKIE_NAME,
        'description': 'Admin panel sessiya cookie’si (login qilganda qo‘yiladi). Yozish uchun Origin ruxsat etilgan bo‘lishi kerak.',
    }
    schemes['staffBearer'] = {
        'type': 'http', 'scheme': 'bearer',
        'description': 'Xodim kabineti tokeni (`issue_staff_session` yoki HEMIS kirishi natijasi).',
    }
    result.setdefault('components', {}).setdefault('schemas', {})['ApiError'] = ERROR_SCHEMA
    err = lambda desc: {'description': desc, 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ApiError'}}}}

    for path, item in result['paths'].items():
        for method, op in item.items():
            if not isinstance(op, dict) or 'responses' not in op:
                continue
            if path.startswith('/api/cms/'):
                tail = path.removeprefix('/api/cms/')
                open_ = tail in ('users/login',)
                op['security'] = [] if open_ else (PANEL_SECURITY + [{}] if tail == 'users/me' else _copy.deepcopy(PANEL_SECURITY))
                if not open_:
                    op['responses'].setdefault('401', err('Kirilmagan yoki JWT yaroqsiz / muddati tugagan'))
                    op['responses'].setdefault('403', err('Rolingizga bu amal ruxsat etilmagan yoki Origin ruxsat etilmagan'))
                else:
                    op['responses'].setdefault('401', err('Login yoki parol noto‘g‘ri'))
                    op['responses'].setdefault('423', err('5 marta xato — hisob 15 daqiqaga bloklangan'))
                kind = _kind(path)
                action = ACTION_BY_OP.get((kind, method)) if kind else None
                if action:
                    op['description'] = (op.get('description') or '') + '\n\n' + _matrix(action)
                    for prm in op.get('parameters', []):
                        if prm.get('name') == 'slug':
                            prm['schema'] = {'type': 'string', 'enum': list(REGISTRY)}
                elif tail.startswith('globals/') and tail.count('/') == 1:
                    action = 'read' if method == 'get' else 'update'
                    op['description'] = (op.get('description') or '') + '\n\n' + _matrix(action, with_globals=True)
                    for prm in op.get('parameters', []):
                        if prm.get('name') == 'slug':
                            prm['schema'] = {'type': 'string', 'enum': list(GLOBALS)}
                elif tail == 'users/unlock':
                    op['description'] = (op.get('description') or '') + '\n\nRuxsat: faqat `superadmin`.'
            elif path.startswith('/api/me'):
                op['security'] = [{'userSession': []}, {'staffBearer': []}]
                op['responses'].setdefault('401', err('Xodim kirmagan'))
    return result
