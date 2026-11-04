"""Payload CMS so'rov formati → Django ORM.

Vue admin panel Payload REST API'si bilan yozilgan: `?where[and][0][title.uz][like]=…&sort=-publishedAt&limit=20&page=2&depth=1`.
Bu modul shu parametrlarni Django `Q` filtri, saralash va sahifalashga aylantiradi, javob esa Payload shaklida
(`docs`, `totalDocs`, `page`, `totalPages` …) qaytadi — admin panel kodi o'zgarmaydi.
"""
import re
from functools import reduce
from operator import and_, or_

from django.core.paginator import Paginator
from django.db.models import Q


def nested_params(params) -> dict:
    """`where[a][0][b][equals]=x` ko'rinishidagi kalitlardan ichma-ich lug'at."""
    out: dict = {}
    for key in params.keys():
        values = params.getlist(key)
        parts = re.findall(r'[^\[\]]+', key)
        if not parts:
            continue
        node = out
        for p in parts[:-1]:
            node = node.setdefault(p, {})
            if not isinstance(node, dict):
                break
        else:
            node[parts[-1]] = values[0] if len(values) == 1 else values
    return out


def as_list(value) -> list:
    """{'0': a, '1': b} yoki [a, b] yoki 'a,b' → ro'yxat."""
    if isinstance(value, dict):
        return [value[k] for k in sorted(value, key=lambda k: int(k) if str(k).isdigit() else 0)]
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [v for v in value.split(',') if v != '']
    return [value]


def camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def default_path(path: str) -> str:
    """`title.uz` → `title__uz`, `publishedAt` → `published_at`."""
    return '__'.join(camel_to_snake(p) for p in path.split('.'))


def coerce(value):
    if isinstance(value, str):
        low = value.lower()
        if low == 'true':
            return True
        if low == 'false':
            return False
        if low in ('null', 'none'):
            return None
    return value


def condition(path, op: str, value) -> Q:
    """Bitta shart. `path` — Django yo'li yoki maxsus funksiya (op, value) → Q."""
    if callable(path):
        return path(op, value)
    value = coerce(value)
    if op == 'equals':
        return Q(**{f'{path}__isnull': True}) if value is None else Q(**{path: value})
    if op == 'not_equals':
        return Q(**{f'{path}__isnull': False}) if value is None else ~Q(**{path: value}) | Q(**{f'{path}__isnull': True})
    if op == 'like':
        words = str(value or '').split()
        return reduce(and_, (Q(**{f'{path}__icontains': w}) for w in words), Q())
    if op == 'contains':
        return Q(**{f'{path}__icontains': value})
    if op == 'in':
        return Q(**{f'{path}__in': as_list(value)})
    if op == 'not_in':
        return ~Q(**{f'{path}__in': as_list(value)})
    if op == 'exists':
        empty = Q(**{f'{path}__isnull': True})
        return ~empty if coerce(value) in (True, 'true', '1', 1) else empty
    lookups = {'greater_than': 'gt', 'greater_than_equal': 'gte', 'less_than': 'lt', 'less_than_equal': 'lte'}
    if op in lookups:
        return Q(**{f'{path}__{lookups[op]}': value})
    raise ValueError(f'Nomaʼlum shart: {op}')


def where_q(where, fields: dict) -> Q:
    """`where` lug'ati → Q. `fields` — Payload yo'li → Django yo'li (yoki funksiya); bo'lmasa avtomatik."""
    if not isinstance(where, dict):
        return Q()
    q = Q()
    for key, cond in where.items():
        if key in ('and', 'or'):
            parts = [where_q(c, fields) for c in as_list(cond) if isinstance(c, dict)]
            if parts:
                q &= reduce(and_ if key == 'and' else or_, parts)
            continue
        if not isinstance(cond, dict):
            continue
        path = fields.get(key, default_path(key))
        if path is None:
            continue
        for op, value in cond.items():
            q &= condition(path, op, value)
    return q


def order_by(sort: str | None, fields: dict, default: list[str]) -> list[str]:
    if not sort:
        return default
    out = []
    for part in sort.split(','):
        part = part.strip()
        if not part:
            continue
        desc = part.startswith('-')
        name = part.lstrip('-')
        path = fields.get(name, default_path(name))
        if not isinstance(path, str):
            continue
        out.append(('-' if desc else '') + path)
    return out or default


def paginate(qs, params, serialize) -> dict:
    """Payload ro'yxat javobi. limit=0 yoki pagination=false — hammasi."""
    try:
        limit = int(params.get('limit', 10))
    except ValueError:
        limit = 10
    if params.get('pagination') == 'false' or limit <= 0:
        items = list(qs)
        total = len(items)
        return {
            'docs': [serialize(o) for o in items], 'totalDocs': total, 'limit': total, 'totalPages': 1, 'page': 1,
            'pagingCounter': 1, 'hasPrevPage': False, 'hasNextPage': False, 'prevPage': None, 'nextPage': None,
        }
    limit = min(limit, 10000)
    paginator = Paginator(qs, limit)
    try:
        page_no = max(1, int(params.get('page', 1)))
    except ValueError:
        page_no = 1
    page_no = min(page_no, max(1, paginator.num_pages))
    page = paginator.page(page_no)
    return {
        'docs': [serialize(o) for o in page.object_list],
        'totalDocs': paginator.count,
        'limit': limit,
        'totalPages': paginator.num_pages,
        'page': page_no,
        'pagingCounter': (page_no - 1) * limit + 1,
        'hasPrevPage': page.has_previous(),
        'hasNextPage': page.has_next(),
        'prevPage': page_no - 1 if page.has_previous() else None,
        'nextPage': page_no + 1 if page.has_next() else None,
    }
