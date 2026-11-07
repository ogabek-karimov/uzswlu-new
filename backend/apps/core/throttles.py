"""So'rov cheklovlari (rate limit) — tizimga yuklama tushmasligi va parol terib ko'rishdan himoya.

Hisob: kirgan foydalanuvchi bo'lsa — uning id'si, bo'lmasa — haqiqiy IP (NUM_PROXIES hisobga olinadi,
shuning uchun `X-Forwarded-For` ni soxtalashtirib chetlab o'tib bo'lmaydi).
Hisoblagich keshda (CACHES) saqlanadi: bir nechta gunicorn jarayoni orasida umumiy.
"""
from rest_framework.throttling import ScopedRateThrottle


# Ishlab chiqish (DEBUG) rejimida umumiy chegaralar o'chadi (bitta kompyuterdan ko'p so'rov normal); kirish va murojaat cheklovlari qoladi
DEV_EXEMPT = frozenset({'public', 'open', 'search', 'panel-read', 'panel-write', 'cabinet', 'docs'})


class ScopedThrottle(ScopedRateThrottle):
    """`view.throttle_scope` (yoki `view.get_throttle_scope(request)`) bo'yicha cheklaydi.

    Sayt serveri (Nuxt) to'g'ri `API_TOKEN` bilan murojaat qilsa — u ishonchli, tashrifchilarning
    hammasi bitta IP'dan ko'rinadi, shuning uchun `public` chegarasi unga qo'llanmaydi.
    """

    def allow_request(self, request, view):
        scope = view.get_throttle_scope(request) if hasattr(view, 'get_throttle_scope') else getattr(view, 'throttle_scope', None)
        if not scope:
            return True
        if scope == 'public' and getattr(request, '_api_token_ok', False):
            return True
        from django.conf import settings
        if settings.DEBUG and scope in DEV_EXEMPT:
            return True
        self.scope = scope
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super(ScopedRateThrottle, self).allow_request(request, view)

    def get_rate(self):
        from django.conf import settings
        return settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].get(self.scope)

    def get_cache_key(self, request, view):
        if getattr(view, 'throttle_by_ip', False):
            return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
        return super().get_cache_key(request, view)
