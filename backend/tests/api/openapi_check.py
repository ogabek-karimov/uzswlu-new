"""Javobni OpenAPI sxemasiga (frontend/docs/openapi.yaml) solishtiruvchi oddiy tekshiruvchi.

Frontend shartnomasi — yagona haqiqat manbai: backend javobi shu sxemaga mos kelmasa, sayt buziladi.
Qo'llab-quvvatlanadi: $ref, allOf, oneOf, type/nullable, enum, required, properties, items, maxItems, format: uri.
"""
import re
from pathlib import Path

from django.conf import settings

SPEC_PATH = Path(settings.BASE_DIR).parent / 'frontend' / 'docs' / 'openapi.yaml'


def load_spec():
    import yaml  # requirements-dev.txt
    return yaml.safe_load(SPEC_PATH.read_text(encoding='utf-8'))


def type_name(v) -> str:
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, int):
        return 'integer'
    if isinstance(v, float):
        return 'number'
    if isinstance(v, str):
        return 'string'
    return 'array' if isinstance(v, list) else 'object'


class Validator:
    def __init__(self, spec: dict):
        self.spec = spec
        self.schemas = spec['components']['schemas']
        self.errors: list[str] = []

    def resolve(self, s):
        while isinstance(s, dict) and '$ref' in s:
            s = self.schemas[s['$ref'].split('/')[-1]]
        return s

    def response_schema(self, openapi_path: str, method: str = 'get'):
        op = self.spec['paths'][openapi_path][method]
        return op['responses']['200']['content']['application/json']['schema']

    def validate(self, value, openapi_path: str, label: str) -> list[str]:
        """Xatolar ro'yxatini qaytaradi (bo'sh — mos)."""
        before = len(self.errors)
        self.check(value, self.response_schema(openapi_path), label)
        return self.errors[before:]

    def check(self, v, s, path):
        errors = self.errors
        s = self.resolve(s)
        if not isinstance(s, dict):
            return
        if 'allOf' in s:
            for part in s['allOf']:
                self.check(v, part, path)
            rest = {k: x for k, x in s.items() if k != 'allOf'}
            if not rest.keys() - {'description'}:
                return
            s = rest
        if 'oneOf' in s:
            results = []
            for opt in s['oneOf']:
                n = len(errors)
                self.check(v, opt, path)
                results.append(len(errors) == n)
                del errors[n:]
            if not any(results):
                errors.append(f'{path}: oneOf mismatch ({v!r:.60})')
            return
        t = s.get('type')
        if s.get('nullable') and v is None:
            return
        if t:
            ts = t if isinstance(t, list) else [t]
            actual = type_name(v)
            if not (actual in ts or (actual == 'integer' and 'number' in ts)):
                errors.append(f'{path}: type {actual}, expected {ts} ({v!r:.50})')
                return
        if 'enum' in s and v not in s['enum']:
            errors.append(f'{path}: {v!r} not in enum {s["enum"]}')
        if isinstance(v, dict):
            for r in s.get('required', []):
                if r not in v:
                    errors.append(f'{path}: missing required "{r}"')
            for k, sub in s.get('properties', {}).items():
                if k in v:
                    self.check(v[k], sub, f'{path}.{k}')
        if isinstance(v, list) and 'items' in s:
            for i, x in enumerate(v):
                self.check(x, s['items'], f'{path}[{i}]')
        if isinstance(v, list) and 'maxItems' in s and len(v) > s['maxItems']:
            errors.append(f'{path}: {len(v)} > maxItems {s["maxItems"]}')
        if isinstance(v, str) and s.get('format') == 'uri' and not re.match(r'^https?://|^/', v):
            errors.append(f'{path}: not a uri: {v!r}')
