"""Bino xaritasi: koordinatani matndan yoki Google Maps havolasidan ajratish va xarita manzillarini qurish.

Admin panelda «Xaritadagi joy» maydoniga koordinata (41.286038, 69.194908) ham, Google Maps'dan nusxalangan
havola yoki «Ulashish → Xaritani joylash» kodi ham qo'yilishi mumkin — shu yerda koordinataga aylantiriladi.
"""
import re
from urllib.parse import quote

from django.core.exceptions import ValidationError

NUM = r'(-?\d{1,3}(?:\.\d+)?)'
# (naqsh, birinchi guruh uzunlikmi) — Google havolalarining turli ko'rinishlari
PATTERNS = (
    (re.compile(rf'!3d{NUM}!4d{NUM}'), False),        # joy havolasi: …!3d<kenglik>!4d<uzunlik>
    (re.compile(rf'!2d{NUM}!3d{NUM}'), True),          # embed kodi: …!2d<uzunlik>!3d<kenglik>
    (re.compile(rf'@{NUM},{NUM}'), False),             # …/@41.28,69.19,17z
    (re.compile(rf'[?&](?:q|query|ll|center)={NUM},\s*{NUM}'), False),
    (re.compile(rf'^\s*{NUM}\s*[,;\s]\s*{NUM}\s*$'), False),  # oddiy koordinata
)
HL = {'uz': 'uz', 'ru': 'ru', 'en': 'en', 'zh': 'zh-CN'}


def parse_coords(value) -> str:
    """Bo'sh qiymat — '' (xarita manzil bo'yicha topiladi); aniqlanmasa — ValidationError."""
    raw = str(value or '').strip()
    if not raw:
        return ''
    for pattern, lng_first in PATTERNS:
        match = pattern.search(raw)
        if not match:
            continue
        a, b = float(match.group(1)), float(match.group(2))
        lat, lng = (b, a) if lng_first else (a, b)
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return f'{lat:.6f}, {lng:.6f}'
    raise ValidationError('Xaritadagi joy aniqlanmadi — koordinata (41.286038, 69.194908) yoki Google Maps havolasini kiriting')


def _query(coords: str, address: str) -> str:
    return coords.replace(' ', '') if coords else address


def map_link(coords: str, address: str) -> str:
    """«Xaritada ochish» — Google Maps (telefonda ilovasi ochiladi)."""
    return f'https://www.google.com/maps/search/?api=1&query={quote(_query(coords, address))}'


def map_embed(coords: str, address: str, lang: str) -> str:
    """Saytdagi kichik xarita (iframe, API kalitsiz)."""
    return f'https://maps.google.com/maps?q={quote(_query(coords, address))}&z=16&hl={HL.get(lang, "uz")}&output=embed'
