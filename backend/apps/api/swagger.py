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
