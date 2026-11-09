"""Sayt statistikasi — cookie'siz va shaxsiy ma'lumotsiz (Umami usulida).

IP manzil saqlanmaydi: tashrifchi kodi = hash(kunlik tuz + IP + brauzer). Tuz har kuni almashadi, shuning uchun
bir kishini kunlar bo'yicha kuzatib bo'lmaydi va cookie banner kerak emas.
"""
import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.core.fields import is_lang
from apps.core.models import Hit
from apps.core.utils import client_ip, sha256

BOTS = re.compile(r'bot|crawl|spider|slurp|preview|headless|lighthouse|monitor|curl|wget|python|axios|node-fetch', re.I)
TABLET = re.compile(r'ipad|tablet', re.I)
MOBILE = re.compile(r'mobi|android|iphone', re.I)
KINDS = ('pageview', 'event', 'search')


def visitor_code(ip: str, ua: str) -> str:
    day = timezone.localtime().date().isoformat()
    salt = sha256(f'{settings.SECRET_KEY}:{day}')
    return sha256(f'{salt}:{ip}:{ua}')[:24]


def device_of(ua: str) -> str:
    return 'tablet' if TABLET.search(ua) else 'mobile' if MOBILE.search(ua) else 'desktop'


def _clip(value, limit: int) -> str:
    return value.strip()[:limit] if isinstance(value, str) else ''


def record_hit(request, data: dict) -> None:
    """Bitta yozuv. Botlar va noto'g'ri yozuvlar e'tiborsiz qoldiriladi; xato hech qachon tashqariga chiqmaydi."""
    ua = request.META.get('HTTP_USER_AGENT', '')
    kind = data.get('kind')
    if not ua or BOTS.search(ua) or kind not in KINDS:
        return
    referrer = ''
    try:
        raw = _clip(data.get('referrer'), 500)
        if raw:
            referrer = (urlparse(raw).hostname or '').removeprefix('www.')[:200]
    except ValueError:
        pass
    path = _clip(data.get('path'), 300)
    country = _clip(request.META.get('HTTP_CF_IPCOUNTRY') or request.META.get('HTTP_X_COUNTRY_CODE'), 2).upper()
    lang = data.get('lang')
    visitor = visitor_code(client_ip(request), ua)
    # Bir xil yozuvni (bir tashrifchi, bir sahifa/hodisa) qisqa vaqtda takrorlash bazani to'ldirmasin
    fingerprint = ':'.join((visitor, kind, path, _clip(data.get('name'), 200), _clip(data.get('value'), 300)))
    if not cache.add(f'hit:{sha256(fingerprint)[:24]}', 1, 10):
        return
    Hit.objects.create(
        visitor=visitor,
        kind=kind,
        path=path if path.startswith('/') else '',
        lang=lang if is_lang(lang) else '',
        referrer=referrer,
        device=device_of(ua),
        country=country,
        name=_clip(data.get('name'), 200),
        value=_clip(data.get('value'), 300),
    )
