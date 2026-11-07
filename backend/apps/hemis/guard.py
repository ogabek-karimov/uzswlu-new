"""HEMIS serveriga bosim tushmasligi uchun himoya ("circuit breaker").

HEMIS javob bermay qolsa, har bir foydalanuvchi so'rovi 8–20 soniya kutib, gunicorn jarayonlarini band qilib qo'ymasligi kerak.
Ketma-ket {MAX_FAILURES} marta xato bo'lsa, {COOLDOWN} soniya HEMIS'ga umuman so'rov yuborilmaydi (tez xato qaytadi),
so'ng bitta sinov so'rovi o'tadi.
"""
from django.core.cache import cache

MAX_FAILURES = 5
WINDOW = 60
COOLDOWN = 30
KEY_FAILS, KEY_OPEN = 'hemis:fails', 'hemis:open'


class HemisUnavailable(RuntimeError):
    pass


def call(fn, *args, **kwargs):
    if cache.get(KEY_OPEN):
        raise HemisUnavailable('HEMIS vaqtincha javob bermayapti — birozdan keyin urinib ko‘ring')
    try:
        result = fn(*args, **kwargs)
    except Exception:
        try:
            cache.add(KEY_FAILS, 0, WINDOW)
            if cache.incr(KEY_FAILS) >= MAX_FAILURES:
                cache.set(KEY_OPEN, 1, COOLDOWN)
                cache.delete(KEY_FAILS)
        except Exception:  # noqa: BLE001 — kesh ishlamasa ham asl xato qaytsin
            pass
        raise
    cache.delete(KEY_FAILS)
    return result
