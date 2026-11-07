"""Ikki bosqichli tasdiq (TOTP, RFC 6238): Google/Microsoft Authenticator, 1Password, Authy va h.k.

Kirish: login+parol to'g'ri bo'lsa va 2FA yoqilgan bo'lsa, sessiya/JWT BERILMAYDI — 5 daqiqalik `challenge` qaytadi;
`POST /users/login/2fa` (challenge + 6 xonali kod yoki zaxira kod) kirishni yakunlaydi.
Kod xatolari parol xatolari bilan bir hisobda sanaladi (5 ta — 15 daqiqa blok), bir kod ikki marta ishlamaydi.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import struct
import time
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, check_any_password
from apps.core.activity import log_activity
from apps.core.throttles import ScopedThrottle

from . import jwt
from .auth import LOCK_MINUTES, MAX_ATTEMPTS, PANEL_AUTH, complete_login, error, record

STEP, DIGITS, CHALLENGE_TTL, RECOVERY_COUNT = 30, 6, 300, 8
ISSUER = 'UzSWLU'


# ─── TOTP ───────────────────────────────────────────────────────────────────

def new_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode().rstrip('=')


def _code(secret: str, step: int) -> str:
    key = base64.b32decode(secret + '=' * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack('>Q', step), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = (struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 10 ** DIGITS
    return f'{number:0{DIGITS}d}'


def check_totp(user: User, code: str, *, consume: bool = True) -> bool:
    """Kod ±1 qadam (30 s) oralig'ida to'g'ri va avval ishlatilmagan bo'lsa True."""
    code = ''.join(ch for ch in str(code or '') if ch.isdigit())
    if len(code) != DIGITS or not user.totp_secret:
        return False
    now = int(time.time() // STEP)
    ok_step = None
    for step in (now - 1, now, now + 1):
        if hmac.compare_digest(_code(user.totp_secret, step), code):
            ok_step = step  # ro'yxat bo'ylab to'liq o'tamiz (vaqt farqi bilinmasin)
    if ok_step is None or ok_step <= user.totp_last_step:
        return False
    if consume:
        user.totp_last_step = ok_step
        user.save(update_fields=['totp_last_step'])
    return True


def _hash(code: str) -> str:
    return hashlib.sha256(code.strip().lower().replace(' ', '').encode()).hexdigest()


def new_recovery_codes(user: User) -> list[str]:
    codes = [f'{secrets.token_hex(3)}-{secrets.token_hex(3)}' for _ in range(RECOVERY_COUNT)]
    user.recovery_hashes = [_hash(c) for c in codes]
    return codes


def use_recovery(user: User, code: str) -> bool:
    h = _hash(code)
    if h not in (user.recovery_hashes or []):
        return False
    user.recovery_hashes = [x for x in user.recovery_hashes if x != h]  # bir martalik
    user.save(update_fields=['recovery_hashes'])
    return True


def check_second_factor(user: User, code: str) -> bool:
    code = str(code or '').strip()
    return check_totp(user, code) or use_recovery(user, code)


def otpauth_uri(user: User) -> str:
    return f'otpauth://totp/{ISSUER}:{quote(user.username)}?secret={user.totp_secret}&issuer={ISSUER}&digits={DIGITS}&period={STEP}'


def required_for(user: User) -> bool:
    return user.role in settings.REQUIRE_2FA_ROLES


# ─── Kirishdagi ikkinchi qadam (challenge) ──────────────────────────────────

def issue_challenge(user: User) -> str:
    body = jwt._b64(json.dumps({'sub': user.pk, 'exp': int(time.time()) + CHALLENGE_TTL, 'pv': jwt.password_trace(user), 'p': '2fa'}).encode())
    return f'{body}.{jwt._sign("2fa." + body)}'


def read_challenge(token: str) -> User | None:
    try:
        body, sig = str(token).split('.')
        if not hmac.compare_digest(jwt._sign('2fa.' + body), sig):
            return None
        claims = json.loads(jwt._unb64(body))
        if claims.get('p') != '2fa' or int(claims['exp']) <= time.time():
            return None
        user = User.objects.filter(pk=int(claims['sub'])).first()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
    if not user or user.status == 'disabled' or not user.totp_enabled or not hmac.compare_digest(jwt.password_trace(user), str(claims.get('pv', ''))):
        return None
    return user


class LoginTwoFactorView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'login'
    throttle_by_ip = True

    @extend_schema(tags=['Admin panel: kirish'], summary='Kirishning 2-qadami: tasdiqlash kodi',
                   description='`POST /users/login` `twoFactorRequired: true` va `challenge` qaytarsa, shu yerga `challenge` va authenticator kodini (yoki zaxira kodni) yuboring. Javob — oddiy kirish javobi (`token`, `user`).',
                   request=inline_serializer('TwoFactorLogin', {'challenge': serializers.CharField(), 'code': serializers.CharField()}))
    def post(self, request):
        user = read_challenge(request.data.get('challenge'))
        if not user:
            return error('Vaqt tugadi yoki so‘rov yaroqsiz — qaytadan kiring', status.HTTP_401_UNAUTHORIZED)
        now = timezone.now()
        if user.lock_until and user.lock_until > now:
            record(request, user, user.username, 'locked')
            return error('Hisob vaqtincha bloklangan — 15 daqiqadan keyin urinib ko‘ring', 423)
        if not check_second_factor(user, request.data.get('code')):
            user.login_attempts += 1
            if user.login_attempts >= MAX_ATTEMPTS:
                user.lock_until, user.login_attempts = now + timedelta(minutes=LOCK_MINUTES), 0
            user.save(update_fields=['login_attempts', 'lock_until'])
            record(request, user, user.username, 'bad_password')
            return error('Tasdiqlash kodi noto‘g‘ri', status.HTTP_401_UNAUTHORIZED)
        return complete_login(request, user, user.username)


# ─── Sozlash (kirgan foydalanuvchi o'zi uchun) ──────────────────────────────

def _me(request):
    u = request.user
    return u if u and u.is_authenticated and u.status != 'disabled' else None


def _confirm(user: User, password, code) -> str | None:
    """Sezgir amal uchun parol + kod. Xato bo'lsa — xabar (urinishlar keshda sanaladi), aks holda None."""
    key = f'2fa-confirm:{user.pk}'
    if cache.get(key, 0) >= 5:
        return 'Juda ko‘p noto‘g‘ri urinish — 15 daqiqadan keyin urinib ko‘ring'
    if not check_any_password(user, str(password or '')):
        cache.add(key, 0, 900)
        cache.incr(key)
        return 'Parol noto‘g‘ri'
    if not check_second_factor(user, code):
        cache.add(key, 0, 900)
        cache.incr(key)
        return 'Tasdiqlash kodi noto‘g‘ri'
    cache.delete(key)
    return None


class _Base(APIView):
    authentication_classes = PANEL_AUTH
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'login'
    throttle_by_ip = True


class SetupView(_Base):
    @extend_schema(tags=['Admin panel: kirish'], summary='2FA: yangi kalit yaratish', request=None,
                   description='Authenticator ilovasiga qo‘lda kiritiladigan `secret` va `otpauthUri` qaytaradi. 2FA hali yoqilmaydi — `/users/2fa/enable` bilan kodni tasdiqlang.')
    def post(self, request):
        user = _me(request)
        if not user:
            return error('Kirish kerak', 401)
        if user.totp_enabled:
            return error('2FA allaqachon yoqilgan. Avval o‘chiring.')
        user.totp_secret = new_secret()
        user.save(update_fields=['totp_secret'])
        return Response({'secret': user.totp_secret, 'otpauthUri': otpauth_uri(user), 'issuer': ISSUER, 'account': user.username})


class EnableView(_Base):
    @extend_schema(tags=['Admin panel: kirish'], summary='2FA ni yoqish (kodni tasdiqlash)',
                   description='Javobdagi `recoveryCodes` faqat bir marta ko‘rsatiladi — saqlab qo‘ying (telefon yo‘qolsa kirish uchun).',
                   request=inline_serializer('TwoFactorEnable', {'code': serializers.CharField()}))
    def post(self, request):
        user = _me(request)
        if not user:
            return error('Kirish kerak', 401)
        if user.totp_enabled or not user.totp_secret:
            return error('Avval kalit yarating (/users/2fa/setup)')
        if not check_totp(user, request.data.get('code')):
            return error('Kod noto‘g‘ri — ilovadagi hozirgi kodni kiriting')
        user.totp_enabled = True
        codes = new_recovery_codes(user)
        user.save(update_fields=['totp_enabled', 'recovery_hashes'])
        log_activity(request, action='update', entity='users', entity_id=user.pk, label=f'{user.name} — 2FA yoqildi')
        return Response({'message': '2FA yoqildi', 'recoveryCodes': codes})


class DisableView(_Base):
    @extend_schema(tags=['Admin panel: kirish'], summary='2FA ni o‘chirish (parol + kod)',
                   request=inline_serializer('TwoFactorDisable', {'password': serializers.CharField(), 'code': serializers.CharField()}))
    def post(self, request):
        user = _me(request)
        if not user:
            return error('Kirish kerak', 401)
        if not user.totp_enabled:
            return error('2FA yoqilmagan')
        if required_for(user):
            return error('Sizning rolingiz uchun 2FA majburiy — o‘chirib bo‘lmaydi', 403)
        if (msg := _confirm(user, request.data.get('password'), request.data.get('code'))):
            return error(msg)
        user.totp_enabled, user.totp_secret, user.recovery_hashes, user.totp_last_step = False, '', [], 0
        user.save(update_fields=['totp_enabled', 'totp_secret', 'recovery_hashes', 'totp_last_step'])
        log_activity(request, action='update', entity='users', entity_id=user.pk, label=f'{user.name} — 2FA o‘chirildi')
        return Response({'message': '2FA o‘chirildi'})


class RecoveryView(_Base):
    @extend_schema(tags=['Admin panel: kirish'], summary='Yangi zaxira kodlar (eskilari bekor bo‘ladi)',
                   request=inline_serializer('TwoFactorRecovery', {'password': serializers.CharField(), 'code': serializers.CharField()}))
    def post(self, request):
        user = _me(request)
        if not user or not user.totp_enabled:
            return error('2FA yoqilmagan')
        if (msg := _confirm(user, request.data.get('password'), request.data.get('code'))):
            return error(msg)
        codes = new_recovery_codes(user)
        user.save(update_fields=['recovery_hashes'])
        return Response({'recoveryCodes': codes})


class ResetView(_Base):
    @extend_schema(tags=['Admin panel: kirish'], summary='Boshqa foydalanuvchining 2FA sini bekor qilish (superadmin)',
                   description='Foydalanuvchi telefonini yo‘qotib, zaxira kodlari ham bo‘lmasa. Keyingi kirishida 2FA ni qaytadan sozlaydi.',
                   request=inline_serializer('TwoFactorReset', {'username': serializers.CharField()}))
    def post(self, request):
        me = _me(request)
        if not me or me.role != 'superadmin':
            return error('Ruxsat yo‘q', 403)
        target = User.objects.filter(username=str(request.data.get('username') or '')).first()
        if not target:
            return error('Foydalanuvchi topilmadi', 404)
        target.totp_enabled, target.totp_secret, target.recovery_hashes, target.totp_last_step = False, '', [], 0
        target.save(update_fields=['totp_enabled', 'totp_secret', 'recovery_hashes', 'totp_last_step'])
        log_activity(request, action='role', entity='users', entity_id=target.pk, label=f'{target.name} — 2FA superadmin tomonidan bekor qilindi')
        return Response({'message': '2FA bekor qilindi'})
