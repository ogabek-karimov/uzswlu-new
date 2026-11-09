"""Ochiq API uchun umumiy yordamchilar: til, rasm/fayl manzillari, biriktirmalar, token tekshiruvi."""
import hmac
import os
import re
from urllib.parse import parse_qsl, urlencode

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttles import ScopedThrottle
from apps.core.fields import LANGS, is_lang, pick, tr
from apps.core.html import restore_timeline, text_of
from apps.core.utils import local_date, sha256, size_label

__all__ = ['LANGS', 'pick', 'tr', 'local_date', 'restore_timeline', 'text_of']


class ApiToken(BasePermission):
    """`Authorization: Bearer <API_TOKEN>` (frontend serveri). API_TOKEN bo'sh bo'lsa — tekshirilmaydi.
    Tokenni to'xtovsiz almashtirish: `API_TOKEN=yangi,eski` → frontendni yangilang → `API_TOKEN=yangi`."""

    message = 'Invalid or missing API token'

    def has_permission(self, request, view):
        tokens = [t.strip() for t in (settings.API_TOKEN or '').split(',') if t.strip()]  # vergul bilan: eski+yangi (almashtirish uchun)
        if not tokens:
            return True
        scheme, _, value = request.META.get('HTTP_AUTHORIZATION', '').partition(' ')
        given = value.strip().encode()
        ok = scheme.lower() == 'bearer' and any([hmac.compare_digest(given, t.encode()) for t in tokens])  # ro'yxat bo'ylab to'liq o'tadi (vaqt bo'yicha farq bilinmasin)
        if ok:
            request._api_token_ok = True  # ishonchli sayt serveri: IP bo'yicha `public` chegarasi qo'llanmaydi
        return ok


# Views o'qiydigan so'rov parametrlari. Kesh kalitiga FAQAT shular kiradi: begona parametr (`?x=tasodifiy`) yangi kesh yozuvi
# yaratib, keshni to'ldirib haqiqiy yozuvlarni siqib chiqarmasin (cache-busting). Yangi parametr qo'shilsa — shu yerga ham
# (tests/security/test_cache_pressure.py kod bo'ylab tekshiradi).
CACHE_PARAMS = frozenset({'lang', 'type', 'q', 'month', 'sdg', 'page', 'perPage', 'level', 'group', 'department'})


def _cache_key(request, lang_scope: str) -> str:
    pairs = sorted((k, v) for k, v in parse_qsl(request.META.get('QUERY_STRING', ''), keep_blank_values=True) if k in CACHE_PARAMS)
    qs = urlencode(pairs)
    key = f"pub:{cache.get('content_ver', 0)}:{lang_scope}:{request.path}?{qs}"
    if len(key) > 200:  # kesish emas, xesh: uzun kalitlar bir-biri bilan to'qnashmasin
        key = f"pub:{cache.get('content_ver', 0)}:{lang_scope}:{request.path}:{sha256(qs)}"
    return key.replace(' ', '%20')


def bump_content_version() -> None:
    """Kontent o'zgarganda ochiq API keshi bir zumda eskiradi (kalit versiyasi oshadi)."""
    try:
        cache.incr('content_ver')
    except ValueError:
        cache.set('content_ver', 1, None)


class CachedGetMixin:
    """Ochiq GET javoblarini qisqa muddat keshlaydi: bir xil sahifani minglab odam ochsa ham baza bir marta so'raladi.
    Autentifikatsiya, ruxsat va so'rov cheklovi keshdan OLDIN tekshiriladi (kesh ularni chetlab o'tmaydi)."""

    cache_ttl: int | None = None   # None — PUBLIC_CACHE_SECONDS; 0 — keshlamaydi

    def dispatch(self, request, *args, **kwargs):
        ttl = settings.PUBLIC_CACHE_SECONDS if self.cache_ttl is None else self.cache_ttl
        if request.method != 'GET' or not ttl or not hasattr(self, 'get'):  # `get` yo'q (faqat POST) — DRF o'zi 405 qaytaradi, 500 emas
            return super().dispatch(request, *args, **kwargs)
        self.args, self.kwargs = args, kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers
        try:
            self.initial(request, *args, **kwargs)
            key = _cache_key(request, 'x')
            data = cache.get(key)
            if data is None:
                response = self.get(request, *args, **kwargs)
                if response.status_code == 200:
                    cache.set(key, response.data, ttl)
            else:
                response = Response(data)
            # Token bilan himoyalangan javob oraliq kesh/CDN'da «public» bo'lib qolmasin (tokensiz mijozga berilib ketishi mumkin)
            gated = bool(settings.API_TOKEN) and ApiToken in getattr(self, 'permission_classes', ())
            response['Cache-Control'] = f"{'private' if gated else 'public'}, max-age={min(ttl, 30)}"
            response['Vary'] = 'Authorization, Accept-Encoding'
        except Exception as exc:  # noqa: BLE001 — DRF'ning o'z xato ishlovchisi
            response = self.handle_exception(exc)
        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response


class PublicView(CachedGetMixin, APIView):
    authentication_classes: list = []
    permission_classes = [ApiToken]
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'public'


class OpenView(APIView):
    """Token talab qilmaydigan ochiq endpointlar (Payload bilan mos: /site/*, /hit)."""

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'open'


def lang_of(request) -> str:
    lang = request.query_params.get('lang')
    return lang if is_lang(lang) else 'uz'


def iso(dt):
    """Toshkent vaqti bilan ISO 8601: 2026-11-07T10:00:00+05:00"""
    return timezone.localtime(dt).isoformat(timespec='seconds') if dt else None


def img(media, size: str = 'card'):
    return media.size_url(size) if media else None


def file_url(media):
    return media.url if media else None


def lines(value, lang: str) -> list[str]:
    """I18n matn → qatorlar ro'yxati (teglar, hujjatlar ro'yxati)."""
    return [ln.strip() for ln in tr(value, lang).splitlines() if ln.strip()]


def attachment_out(a, lang: str):
    """Biriktirma (PDF yoki havola) → API shakli. Fayl ham, havola ham yo'q bo'lsa None."""
    file = a.file if a.file_id else None
    url = file_url(file) or a.url
    if not url:
        return None
    is_pdf = bool(file) or bool(re.search(r'\.pdf($|\?)', url, re.I))
    meta = pick(a.meta, lang) or pick(a.meta, 'uz')
    if not meta and file:
        meta = ' · '.join(x for x in ['PDF', size_label(file.filesize)] if x)
    return {
        'title': tr(a.title, lang) or (os.path.basename(file.file.name) if file else ''),
        'url': url,
        'kind': 'pdf' if is_pdf else 'link',
        'meta': meta or None,
        'display': a.display if file else None,
        'height': a.height if file and a.display == 'embed' else None,
    }


def attachments_out(items, lang: str) -> list[dict]:
    return [x for x in (attachment_out(a, lang) for a in items) if x]
