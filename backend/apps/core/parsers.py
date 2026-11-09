"""So'rov tanasi parserlari: hamma endpoint (panel, kabinet, murojaat, kirish) shu orqali o'tadi.

- JSON faqat OBYEKT bo'la oladi (massiv/null/son — 400; avval 500 berardi) va juda chuqur ichma-ich emas.
- Matnlardagi NUL bayt (`\\x00`) olib tashlanadi: PostgreSQL uni rad etib 500 qaytarardi (SQLite'da sezilmaydi) —
  ochiq murojaat formasi orqali ham kelishi mumkin edi.
"""
from django.http import QueryDict
from rest_framework.exceptions import ParseError
from rest_framework.parsers import DataAndFiles, FormParser, JSONParser, MultiPartParser

MAX_DEPTH = 24


def clean(value, depth: int = 0):
    if depth > MAX_DEPTH:
        raise ParseError('JSON juda chuqur ichma-ich')
    if isinstance(value, str):
        return value.replace('\x00', '')
    if isinstance(value, dict):
        return {(k.replace('\x00', '') if isinstance(k, str) else k): clean(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v, depth + 1) for v in value]
    return value


def clean_querydict(qd: QueryDict) -> QueryDict:
    out = QueryDict(mutable=True)
    for key in qd.keys():
        out.setlist(key.replace('\x00', ''), [v.replace('\x00', '') if isinstance(v, str) else v for v in qd.getlist(key)])
    out._mutable = False
    return out


class SafeJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            data = super().parse(stream, media_type, parser_context)
        except RecursionError:
            raise ParseError('JSON juda chuqur ichma-ich') from None
        if not isinstance(data, dict):
            raise ParseError('JSON obyekt bo‘lishi kerak')
        return clean(data)


class SafeFormParser(FormParser):
    def parse(self, stream, media_type=None, parser_context=None):
        return clean_querydict(super().parse(stream, media_type, parser_context))


class SafeMultiPartParser(MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(stream, media_type, parser_context)
        return DataAndFiles(clean_querydict(result.data), result.files)
