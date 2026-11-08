"""Admin panel (`/api/cms/*`) sxemalari: kolleksiya kodidan avtomatik olinadi — qo'lda yozilgan ro'yxat yo'q.

- **Javob maydonlari** — kolleksiyaning `out()` funksiyasi (AST) tahlil qilinadi: `return {...}` kalitlari va qiymat
  turlari (`i18n_out` → PanelI18n, `media_out` → PanelMedia, `dt` → date-time, model maydonlari → ularning turi).
- **So'rov maydonlari** — `write()`/`after()` dagi `put(obj, data, {...})` jadvali, `'x' in data`, `data.get('x')`.

Shu tufayli kolleksiyaga maydon qo'shilsa, Swagger o'zi yangilanadi; `tests/api/test_swagger.py` haqiqiy javoblar
sxemaga mosligini tekshiradi (hujjat va kod ajralib ketmasin).
"""
import ast
import inspect
import textwrap

from django.core.exceptions import FieldDoesNotExist
from django.db import models as dm

from apps.core.fields import I18nField

I18N = {'$ref': '#/components/schemas/PanelI18n'}
MEDIA = {'$ref': '#/components/schemas/PanelMedia'}
READ_ONLY = {'id', 'createdAt', 'updatedAt', 'collection', 'label'}
WRITE_ONLY = {'password', 'currentPassword'}

# put() jadvalidagi aylantirgichlar → JSON tur
CONVERTERS = {
    'text': {'type': 'string'},
    'i18n_in': I18N,
    'num': {'type': 'integer'},
    'flag': {'type': 'boolean'},
    'parse_dt': {'type': ['string', 'null'], 'format': 'date-time'},
    'ref_id': {'type': ['integer', 'null']},
    'lines_to_lists': {'type': 'object', 'additionalProperties': {'type': 'array', 'items': {'type': 'string'}}},
}


def nullable(schema: dict) -> dict:
    if '$ref' in schema:
        return {'oneOf': [schema, {'type': 'null'}]}
    if 'oneOf' in schema:
        return schema if {'type': 'null'} in schema['oneOf'] else {**schema, 'oneOf': [*schema['oneOf'], {'type': 'null'}]}
    t = schema.get('type')
    if t is None:
        return schema
    return {**schema, 'type': t if isinstance(t, list) and 'null' in t else [*(t if isinstance(t, list) else [t]), 'null']}


def field_schema(f) -> dict:
    """Django model maydoni → JSON sxema."""
    if isinstance(f, I18nField):
        return I18N
    if isinstance(f, (dm.ForeignKey, dm.OneToOneField)):
        s = {'type': 'integer'}
    elif isinstance(f, dm.BooleanField):
        s = {'type': 'boolean'}
    elif isinstance(f, dm.DateTimeField):
        s = {'type': 'string', 'format': 'date-time'}
    elif isinstance(f, dm.DateField):
        s = {'type': 'string', 'format': 'date'}
    elif isinstance(f, (dm.IntegerField, dm.AutoField, dm.BigAutoField)):
        s = {'type': 'integer'}
    elif isinstance(f, dm.FloatField):
        s = {'type': 'number'}
    elif isinstance(f, (dm.CharField, dm.TextField, dm.FileField)):
        s = {'type': 'string'}
    else:
        return {}
    return nullable(s) if f.null or f.blank and isinstance(f, (dm.ForeignKey,)) else s


def _tree(fn):
    try:
        return ast.parse(textwrap.dedent(inspect.getsource(fn)))
    except (OSError, TypeError, SyntaxError):  # pragma: no cover
        return None


_CONST = {str: 'string', bool: 'boolean', int: 'integer', float: 'number', type(None): 'null'}


def infer(n, model) -> dict:
    """`out()` ichidagi ifoda → JSON sxema (aniqlab bo'lmasa — `{}`, ya'ni ixtiyoriy tur)."""
    if isinstance(n, ast.Constant):
        return {'type': _CONST.get(type(n.value), 'string')}
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        name = n.func.id
        if name == 'i18n_out':
            return I18N
        if name == 'media_out':
            return {'oneOf': [MEDIA, {'type': 'integer'}, {'type': 'null'}]}
        if name == 'dt':
            return {'type': ['string', 'null'], 'format': 'date-time'}
        if name == 'lines_to_lists':
            return CONVERTERS['lines_to_lists']
        if name in ('str', 'int', 'bool'):
            return {'type': {'str': 'string', 'int': 'integer', 'bool': 'boolean'}[name]}
        return {}
    if isinstance(n, ast.ListComp):
        item = infer(n.elt, model)
        return {'type': 'array', 'items': item} if item else {'type': 'array'}
    if isinstance(n, ast.Dict):
        props = {k.value: infer(v, model) for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant)}
        return {'type': 'object', 'properties': props}
    if isinstance(n, ast.IfExp):
        a, b = infer(n.body, model), infer(n.orelse, model)
        if b == {'type': 'null'}:
            return nullable(a) if a else {}
        if a == {'type': 'null'}:
            return nullable(b) if b else {}
        if a == b:
            return a
        return {'oneOf': [x for x in (a, b) if x]} if a and b else {}
    if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
        first = infer(n.values[0], model)
        return nullable(first) if first and isinstance(n.values[-1], ast.Constant) and n.values[-1].value is None else first
    if isinstance(n, ast.Attribute):
        if n.attr == 'pk' or n.attr.endswith('_id'):
            return {'type': 'integer'}
        if model is not None:
            try:
                return field_schema(model._meta.get_field(n.attr))
            except FieldDoesNotExist:
                return {}
    return {}


def _returned_dicts(fn, ns: dict, seen=()):
    """`return {...}` lug'atlari; `return helper(...)` bo'lsa — helper (masalan `media_out`) ichiga kiriladi."""
    tree = _tree(fn)
    if tree is None:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            v = node.value
            if isinstance(v, ast.Dict):
                out.append(v)
            elif isinstance(v, ast.Name):  # doc = {...}; ...; return doc
                for a in ast.walk(tree):
                    if isinstance(a, ast.Assign) and isinstance(a.value, ast.Dict) and any(isinstance(t, ast.Name) and t.id == v.id for t in a.targets):
                        out.append(a.value)
            elif isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id in ns and v.func.id not in seen:
                helper = ns[v.func.id]
                if callable(helper):
                    out += _returned_dicts(helper, ns, (*seen, v.func.id))
    return out


def loop_keys(fn, ns: dict) -> set:
    """`for net, (...) in SCIENCE.items(): ... doc[net] = ... / if net in data` — modul lug'ati kalitlari maydon bo'ladi."""
    tree = _tree(fn)
    found: set = set()
    if tree is None:
        return found
    for node in ast.walk(tree):
        if not (isinstance(node, ast.For) and isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Attribute)
                and node.iter.func.attr == 'items' and isinstance(node.iter.func.value, ast.Name)):
            continue
        table = ns.get(node.iter.func.value.id)
        first = node.target.elts[0] if isinstance(node.target, ast.Tuple) else node.target
        if not isinstance(table, dict) or not isinstance(first, ast.Name):
            continue
        used = any((isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Name) and n.slice.id == first.id)
                   or (isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == first.id)
                   for n in ast.walk(node))
        if used:
            found |= {k for k in table if isinstance(k, str)}
    return found


def response_schema(coll) -> dict:
    """Kolleksiya javobidagi bitta yozuv (`out()`) sxemasi."""
    import apps.panel.collections as mod
    ns = vars(mod)
    props: dict = {}
    for d in _returned_dicts(type(coll).out, ns):
        for k, v in zip(d.keys, d.values):
            if isinstance(k, ast.Constant) and k.value not in props:
                props[k.value] = infer(v, coll.model)
    for k in sorted(loop_keys(type(coll).out, ns)):
        props.setdefault(k, {'type': ['string', 'null']})
    return {'type': 'object', 'properties': props}


def media_schema() -> dict:
    import apps.panel.collections as mod
    ns = vars(mod)
    props: dict = {}
    for d in _returned_dicts(mod.media_out, ns):
        for k, v in zip(d.keys, d.values):
            if isinstance(k, ast.Constant) and k.value not in props:
                props[k.value] = infer(v, None)
    return {'type': 'object', 'description': 'Media yozuvi (`depth ≥ 1` bo‘lganda; aks holda faqat `id`).', 'properties': props}


def input_schema(coll, response: dict) -> dict:
    """So'rov tanasi: `write()`/`after()` qabul qiladigan maydonlar (hammasi ixtiyoriy — PATCH qisman o'zgartiradi)."""
    keys: dict[str, dict | None] = {}
    for fn in (type(coll).write, type(coll).after):
        tree = _tree(fn)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'put' and len(node.args) >= 3 \
                    and isinstance(node.args[2], ast.Dict):
                for k, v in zip(node.args[2].keys, node.args[2].values):
                    if not (isinstance(k, ast.Constant) and isinstance(v, ast.Tuple) and len(v.elts) == 2):
                        continue
                    conv = v.elts[1].id if isinstance(v.elts[1], ast.Name) else None
                    field = v.elts[0].value if isinstance(v.elts[0], ast.Constant) else None
                    if conv in CONVERTERS:
                        keys[k.value] = CONVERTERS[conv]
                    elif field and coll.model is not None:
                        try:
                            keys[k.value] = field_schema(coll.model._meta.get_field(field))
                        except FieldDoesNotExist:
                            keys.setdefault(k.value, None)
                    else:
                        keys.setdefault(k.value, None)
            elif isinstance(node, ast.Compare) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) \
                    and isinstance(node.ops[0], ast.In) and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == 'data':
                keys.setdefault(node.left.value, None)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get' \
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'data' and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                keys.setdefault(node.args[0].value, None)
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == 'data' \
                    and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                keys.setdefault(node.slice.value, None)

    import apps.panel.collections as mod
    for fn in (type(coll).write, type(coll).after):
        for k in loop_keys(fn, vars(mod)):
            keys.setdefault(k, {'type': 'string'})
    resp = response.get('properties', {})
    props = {}
    for k, s in keys.items():
        if k in READ_ONLY:
            continue
        if not s:
            r = resp.get(k, {})
            if r == {'oneOf': [MEDIA, {'type': 'integer'}, {'type': 'null'}]}:
                s = {'type': ['integer', 'null'], 'description': 'Media ID (`POST /api/cms/media` javobidan)'}
            else:
                s = {kk: vv for kk, vv in r.items() if kk != 'properties'} if r else {}
                if r.get('type') == 'object' and r.get('properties'):
                    s = {'type': 'object'}
        props[k] = dict(s)
        if k in WRITE_ONLY:
            props[k] = {'type': 'string', 'writeOnly': True}
    return {'type': 'object', 'properties': dict(sorted(props.items()))}


PAGED = {
    'type': 'object',
    'properties': {
        'docs': {'type': 'array', 'items': {}},
        'totalDocs': {'type': 'integer'}, 'limit': {'type': 'integer'}, 'page': {'type': 'integer'}, 'totalPages': {'type': 'integer'},
        'pagingCounter': {'type': 'integer'}, 'hasPrevPage': {'type': 'boolean'}, 'hasNextPage': {'type': 'boolean'},
        'prevPage': {'type': ['integer', 'null']}, 'nextPage': {'type': ['integer', 'null']},
    },
}


def pascal(slug: str) -> str:
    return 'Panel' + ''.join(w.title() for w in slug.split('-'))
