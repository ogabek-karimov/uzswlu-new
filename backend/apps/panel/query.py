"""Payload CMS so'rov formati → Django ORM.

Vue admin panel Payload REST API'si bilan yozilgan: `?where[and][0][title.uz][like]=…&sort=-publishedAt&limit=20&page=2&depth=1`.
Bu modul shu parametrlarni Django `Q` filtri, saralash va sahifalashga aylantiradi, javob esa Payload shaklida
(`docs`, `totalDocs`, `page`, `totalPages` …) qaytadi — admin panel kodi o'zgarmaydi.
"""
import re
from functools import reduce
from operator import and_, or_

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.db.models import JSONField, Q

# Hech qachon filtr/saralash uchun ochilmaydigan maydonlar: aks holda `where[uploaded_by.password][like]=a$` kabi
# so'rovlar bilan parol xeshini harf-harf topib olish mumkin bo'lardi (ORM orqali "oracle" hujumi).
DENY_FIELDS = frozenset({'password', 'token_hash', 'session_key', 'secret', 'last_login', 'is_superuser', 'is_staff',
                         'groups', 'user_permissions', 'login_attempts', 'lock_until'})
MAX_WHERE_DEPTH, MAX_CONDITIONS, MAX_IN_VALUES, MAX_LIKE_WORDS = 4, 40, 200, 8
KEY_RE = re.compile(r'^[a-z0-9_]{1,24}$')


def safe_path(model, path: str) -> str:
    """Avtomatik hosil bo'lgan Django yo'lini tekshiradi: faqat modelning o'z maydoni, JSON ichidagi kalit (`title__uz`) yoki
    bog'langan yozuvning id/slug'i. Boshqa hamma narsa (aloqalar bo'ylab o'tish, yashirin maydonlar) — rad etiladi."""
    parts = path.split('__')
    if any(p in DENY_FIELDS for p in parts):
        raise ValidationError('Bu maydon bo‘yicha qidirib bo‘lmaydi')
    if model is None:
        return path
    head = parts[0]
    if head in ('pk', 'id') and len(parts) == 1:
        return path
    try:
        field = model._meta.get_field(head)
    except FieldDoesNotExist:
        raise ValidationError(f'Noma’lum maydon: {head}') from None
    rest = parts[1:]
    if not rest:
        return path
    if field.is_relation:
        if len(rest) == 1 and rest[0] in ('id', 'pk', 'slug'):
            return path
    elif isinstance(field, JSONField) and len(rest) <= 2 and all(KEY_RE.match(r) for r in rest):
        return path
    raise ValidationError(f'Bu yo‘l bo‘yicha qidirib bo‘lmaydi: {path.replace("__", ".")}')


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
        words = str(value or '').split()[:MAX_LIKE_WORDS]
        return reduce(and_, (Q(**{f'{path}__icontains': w}) for w in words), Q())
    if op == 'contains':
        return Q(**{f'{path}__icontains': value})
    if op == 'in':
        return Q(**{f'{path}__in': as_list(value)[:MAX_IN_VALUES]})
    if op == 'not_in':
        return ~Q(**{f'{path}__in': as_list(value)[:MAX_IN_VALUES]})
    if op == 'exists':
        empty = Q(**{f'{path}__isnull': True})
        return ~empty if coerce(value) in (True, 'true', '1', 1) else empty
    lookups = {'greater_than': 'gt', 'greater_than_equal': 'gte', 'less_than': 'lt', 'less_than_equal': 'lte'}
    if op in lookups:
        return Q(**{f'{path}__{lookups[op]}': value})
    raise ValidationError(f'Noma’lum shart: {op}')


def where_q(where, fields: dict, model=None, _depth: int = 0, _budget: list | None = None) -> Q:
    """`where` lug'ati → Q. `fields` — Payload yo'li → Django yo'li (yoki funksiya); bo'lmasa avtomatik (`safe_path` bilan tekshiriladi).
    Ichma-ich chuqurlik va shartlar soni cheklangan (og'ir so'rovlar bilan serverni bosishga qarshi)."""
    if not isinstance(where, dict):
        return Q()
    if _depth > MAX_WHERE_DEPTH:
        raise ValidationError('Filtr juda murakkab')
    budget = _budget if _budget is not None else [MAX_CONDITIONS]
    q = Q()
    for key, cond in where.items():
        if key in ('and', 'or'):
            parts = [where_q(c, fields, model, _depth + 1, budget) for c in as_list(cond) if isinstance(c, dict)]
            if parts:
                q &= reduce(and_ if key == 'and' else or_, parts)
            continue
        if not isinstance(cond, dict):
            continue
        path = fields[key] if key in fields else safe_path(model, default_path(key))
        if path is None:
            continue
        for op, value in cond.items():
            budget[0] -= 1
            if budget[0] < 0:
                raise ValidationError('Filtr juda murakkab')
            q &= condition(path, op, value)
    return q


def _stable(order: list[str]) -> list[str]:
    """Saralash qiymatlari bir xil bo'lsa ham tartib barqaror bo'lsin (aks holda PostgreSQL sahifalar orasida
    yozuvni takrorlashi yoki tushirib qoldirishi mumkin): oxiriga pk qo'shiladi."""
    if any(o.lstrip('-') in ('id', 'pk') for o in order):
        return order
    return [*order, '-pk' if order and order[0].startswith('-') else 'pk']


def order_by(sort: str | None, fields: dict, default: list[str], model=None) -> list[str]:
    if not sort:
        return _stable(default)
    out = []
    for part in sort.split(',')[:4]:
        part = part.strip()
        if not part:
            continue
        desc = part.startswith('-')
        name = part.lstrip('-')
        path = fields[name] if name in fields else default_path(name)
        if not isinstance(path, str):
            continue
        if name not in fields:
            try:
                safe_path(model, path)
            except ValidationError:
                continue  # ruxsat etilmagan maydon bo'yicha saralash e'tiborsiz qoldiriladi
        out.append(('-' if desc else '') + path)
    return _stable(out or default)


def paginate(qs, params, serialize) -> dict:
    """Payload ro'yxat javobi. limit=0 yoki pagination=false — hammasi."""
    try:
        limit = int(params.get('limit', 10))
    except ValueError:
        limit = 10
    cap = settings.ADMIN_MAX_LIMIT
    if params.get('pagination') == 'false' or limit <= 0:
        items = list(qs[:cap])
        total = len(items)
        return {
            'docs': [serialize(o) for o in items], 'totalDocs': total, 'limit': total, 'totalPages': 1, 'page': 1,
            'pagingCounter': 1, 'hasPrevPage': False, 'hasNextPage': False, 'prevPage': None, 'nextPage': None,
        }
    limit = min(limit, cap)
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
