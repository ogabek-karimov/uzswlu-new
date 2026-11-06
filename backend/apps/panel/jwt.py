"""JWT (HS256) — admin panel API'sini Swagger, Postman va boshqa dasturlardan cookie'siz chaqirish uchun.

Tashqi kutubxonasiz: imzo `SECRET_KEY` dan olingan alohida kalit bilan. Token amal qilmaydi, agar:
muddati tugagan, imzo noto'g'ri, foydalanuvchi o'chirilgan/yopilgan yoki parol o'zgargan (`pv` — parol izi).
"""
import base64
import hashlib
import hmac
import json
import time

from django.conf import settings

ISSUER = 'uzswlu'
HEADER = {'alg': 'HS256', 'typ': 'JWT'}


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def _key() -> bytes:
    return hashlib.sha256(f'uzswlu-panel-jwt|{settings.SECRET_KEY}'.encode()).digest()


def _sign(signing_input: str) -> str:
    return _b64(hmac.new(_key(), signing_input.encode(), hashlib.sha256).digest())


def password_trace(user) -> str:
    return hashlib.sha256((user.password or '').encode()).hexdigest()[:16]


def issue(user, ttl: int | None = None) -> tuple[str, int]:
    """(token, tugash vaqti — unix sekund)"""
    now = int(time.time())
    exp = now + int(ttl or settings.JWT_TTL_SECONDS)
    claims = {'iss': ISSUER, 'sub': str(user.pk), 'role': user.role, 'iat': now, 'exp': exp, 'pv': password_trace(user)}
    signing_input = f"{_b64(json.dumps(HEADER, separators=(',', ':')).encode())}.{_b64(json.dumps(claims, separators=(',', ':')).encode())}"
    return f'{signing_input}.{_sign(signing_input)}', exp


def verify(token: str):
    """Token yaroqli bo'lsa foydalanuvchi, aks holda None."""
    from apps.accounts.models import User
    try:
        head_b64, body_b64, sig = token.split('.')
        if not hmac.compare_digest(_sign(f'{head_b64}.{body_b64}'), sig):
            return None
        header, claims = json.loads(_unb64(head_b64)), json.loads(_unb64(body_b64))
        if header.get('alg') != 'HS256' or claims.get('iss') != ISSUER or int(claims['exp']) <= time.time():
            return None
        user = User.objects.filter(pk=int(claims['sub'])).first()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
    if not user or user.status == 'disabled' or not hmac.compare_digest(password_trace(user), str(claims.get('pv', ''))):
        return None
    return user
