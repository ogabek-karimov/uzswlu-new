"""Ochiq API uchun umumiy yordamchilar: til, rasm/fayl manzillari, biriktirmalar, token tekshiruvi."""
import hmac
import os
import re

from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from apps.core.fields import LANGS, is_lang, pick, tr
from apps.core.html import restore_timeline, text_of
from apps.core.utils import local_date, size_label

__all__ = ['LANGS', 'pick', 'tr', 'local_date', 'restore_timeline', 'text_of']


class ApiToken(BasePermission):
    """`Authorization: Bearer <API_TOKEN>` (frontend serveri). API_TOKEN bo'sh bo'lsa — tekshirilmaydi."""

    message = 'Invalid or missing API token'

    def has_permission(self, request, view):
        token = settings.API_TOKEN
        if not token:
            return True
        scheme, _, value = request.META.get('HTTP_AUTHORIZATION', '').partition(' ')
        return scheme.lower() == 'bearer' and hmac.compare_digest(value.strip().encode(), token.encode())


class PublicView(APIView):
    authentication_classes: list = []
    permission_classes = [ApiToken]


class OpenView(APIView):
    """Token talab qilmaydigan ochiq endpointlar (Payload bilan mos: /site/*, /hit)."""

    authentication_classes: list = []
    permission_classes: list = []


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
