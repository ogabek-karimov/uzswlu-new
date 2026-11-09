"""Fayl xavfsizligi middleware'lari (faqat Python/Django).

UploadSizeLimitMiddleware — yuklash so'rovi hajmini fayl o'qilishidan OLDIN `Content-Length` bo'yicha cheklaydi
    (gigabaytlik so'rov bilan diskni/xotirani to'ldirishga qarshi). Hajm sarlavhasi yo'q multipart so'rov rad etiladi.
MediaHeadersMiddleware — `/media/` dan beriladigan har bir javobga xavfsiz sarlavhalar: `Content-Type` kengaytma
    bo'yicha QAT'IY (brauzer «taxmin qilmasin»), nosniff, rasm/audioda sandbox CSP, boshqa turlar — yuklab olish
    (`attachment`). Productionda `/media/` ni nginx bersa, README'dagi shu qoidalarni nginx'da takrorlang.
"""
import os

from django.conf import settings
from django.http import JsonResponse
from django.utils.http import content_disposition_header

_BODY_METHODS = {'POST', 'PUT', 'PATCH'}

# Brauzerda ochilishi mumkin bo'lgan turlar (kengaytma → Content-Type); qolganlari yuklab olinadi
INLINE_TYPES = {
    '.webp': 'image/webp', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
    '.mp3': 'audio/mpeg', '.pdf': 'application/pdf',
}
# Rasm/audio ochilganda hech narsa bajarilmasligi uchun
SANDBOX_CSP = "default-src 'none'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'; sandbox"


class UploadSizeLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in _BODY_METHODS and not request.content_type.startswith('multipart/'):
            # JSON/forma tanasi: yo'l bo'yicha kichik chegara (ochiq endpointlarga katta tana yuborib xotirani to'ldirishga qarshi)
            limit = next((lim for prefix, lim in settings.BODY_LIMITS if request.path.startswith(prefix)), None)
            length = request.META.get('CONTENT_LENGTH', '')
            if limit is not None and length.isdigit() and int(length) > limit:
                return self._error(f'So‘rov tanasi {limit // 1024} KB dan katta', 413)
        if request.method in _BODY_METHODS and request.content_type.startswith('multipart/'):
            limit = next((lim for prefix, lim in settings.UPLOAD_LIMITS if request.path.startswith(prefix)), None)
            if limit is not None:
                length = request.META.get('CONTENT_LENGTH', '')
                if not length.isdigit():
                    return self._error('Content-Length kerak', 411)
                if int(length) > limit:
                    return self._error(f'Yuklanadigan so‘rov {limit // 1024 // 1024} MB dan katta', 413)
        return self.get_response(request)

    @staticmethod
    def _error(message: str, status: int):
        return JsonResponse({'errors': [{'message': message}], 'message': message}, status=status)


class ApiHeadersMiddleware:
    """JSON javoblar: hech qachon brauzerda «sahifa» sifatida bajarilmasin (CSP), shaxsiy/admin javoblar oraliq keshda qolmasin.

    `/api/cms/*` (admin panel), `/api/me*` (kabinet) va `/api/auth/*` (kirish) javoblari — `private, no-store`:
    token, profil va tahrirlanayotgan kontent proksi/CDN/brauzer keshiga tushmaydi.
    """
    NO_STORE = ('/api/cms/', '/api/me', '/api/auth/')
    JSON_CSP = "default-src 'none'; frame-ancestors 'none'"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(self.NO_STORE) and 'Cache-Control' not in response:
            response['Cache-Control'] = 'private, no-store'
        if response.get('Content-Type', '').startswith('application/json') and 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.JSON_CSP
        return response


class MediaHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(settings.MEDIA_URL) and response.status_code < 400:
            ext = os.path.splitext(request.path)[1].lower()
            ctype = INLINE_TYPES.get(ext)
            response['X-Content-Type-Options'] = 'nosniff'
            response['Content-Type'] = ctype or 'application/octet-stream'
            if ctype is None:
                response['Content-Disposition'] = content_disposition_header(True, os.path.basename(request.path))
            if ctype and ctype != 'application/pdf':
                response['Content-Security-Policy'] = SANDBOX_CSP
        return response
