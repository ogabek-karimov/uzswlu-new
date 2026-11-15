"""Bino xaritasi: koordinatani matndan yoki Yandex/Google Maps havolasidan ajratish va xarita manzillarini qurish.

Admin panelda «Xaritadagi joy» maydoniga koordinata (41.286038, 69.194908) ham, Yandex Xaritalar yoki Google Maps'dan
nusxalangan havola (yoki «Ulashish → Xaritani joylash» kodi) ham qo'yilishi mumkin — shu yerda koordinataga aylantiriladi.
Saytdagi xarita — Yandex (najottalim.uz kabi), API kalitsiz oddiy widget.
"""
import re
from urllib.parse import quote

from django.core.exceptions import ValidationError

NUM = r'(-?\d{1,3}(?:\.\d+)?)'
# (naqsh, birinchi guruh uzunlikmi) — Yandex va Google havolalarining turli ko'rinishlari
PATTERNS = (
    (re.compile(rf'!3d{NUM}!4d{NUM}'), False),        # joy havolasi: …!3d<kenglik>!4d<uzunlik>
    (re.compile(rf'!2d{NUM}!3d{NUM}'), True),          # embed kodi: …!2d<uzunlik>!3d<kenglik>
    (re.compile(rf'@{NUM},{NUM}'), False),             # …/@41.28,69.19,17z
    (re.compile(rf'[?&](?:ll|pt)={NUM}(?:,|%2C){NUM}', re.I), True),   # Yandex: ll=<uzunlik>,<kenglik> / pt=…
    (re.compile(rf'[?&]whatshere(?:\[|%5B)point(?:\]|%5D)={NUM}(?:,|%2C){NUM}', re.I), True),  # Yandex «bu yerda nima bor»
    (re.compile(rf'[?&](?:q|query|center)={NUM},\s*{NUM}'), False),
    (re.compile(rf'^\s*{NUM}\s*[,;\s]\s*{NUM}\s*$'), False),  # oddiy koordinata
)


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
    raise ValidationError('Xaritadagi joy aniqlanmadi — koordinata (41.286038, 69.194908) yoki Yandex Xaritalar / Google Maps havolasini kiriting')


def _query(coords: str, address: str) -> str:
    return coords.replace(' ', '') if coords else address


def _lng_lat(coords: str) -> str:
    """'41.286038, 69.194908' (kenglik, uzunlik) → '69.194908,41.286038' (Yandex tartibi: uzunlik, kenglik)."""
    lat, lng = (part.strip() for part in coords.split(','))
    return f'{lng},{lat}'


def map_link(coords: str, address: str) -> str:
    """«Xaritada ochish» — Yandex Xaritalar (telefonda ilovasi ochiladi)."""
    if coords:
        point = _lng_lat(coords)
        return f'https://yandex.com/maps/?ll={point}&z=17&pt={point},pm2rdl'
    return f'https://yandex.com/maps/?text={quote(address)}'


def map_embed(coords: str, address: str, lang: str) -> str:
    """Saytdagi xarita (iframe, API kalitsiz): koordinata bo'lsa — qizil belgi bilan, bo'lmasa — manzil bo'yicha qidiruv."""
    if coords:
        point = _lng_lat(coords)
        return f'https://yandex.com/map-widget/v1/?ll={point}&z=17&pt={point},pm2rdl'
    return f'https://yandex.com/map-widget/v1/?mode=search&text={quote(address)}&z=16'
