import hashlib
import re
from datetime import datetime

from django.conf import settings
from django.utils import timezone


def abs_url(path: str | None) -> str | None:
    """Nisbiy manzilni to'liq URL'ga aylantiradi (frontend boshqa domenda)."""
    if not path:
        return None
    if re.match(r'^https?://', path):
        return path
    return f"{settings.PUBLIC_SERVER_URL}{path if path.startswith('/') else '/' + path}"


def client_ip(request) -> str:
    """Haqiqiy IP. `X-Forwarded-For` faqat ishonchli proksilar soni (NUM_PROXIES) hisobga olinib o'qiladi:
    mijoz bu sarlavhani o'zi yozib, IP'sini yashira olmaydi (so'rov cheklovlarini chetlab o'tolmaydi)."""
    from django.conf import settings
    proxies = int(getattr(settings, 'REST_FRAMEWORK', {}).get('NUM_PROXIES') or 0)
    fwd = [x.strip() for x in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if x.strip()]
    if proxies and fwd:
        return fwd[-min(proxies, len(fwd))][:45]
    return (request.META.get('REMOTE_ADDR') or '')[:45]


def size_label(num_bytes: int | None) -> str | None:
    """PDF hajmi: kichik fayllar KB'da ("0,0 MB" chiqmasin)."""
    if not num_bytes:
        return None
    if num_bytes < 1024 * 1024:
        return f'{max(1, round(num_bytes / 1024))} KB'
    return f'{num_bytes / 1024 / 1024:.1f}'.replace('.', ',') + ' MB'


def local_date(value: datetime | None) -> str | None:
    """Toshkent vaqti bo'yicha YYYY-MM-DD."""
    if not value:
        return None
    return timezone.localtime(value).date().isoformat()


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
