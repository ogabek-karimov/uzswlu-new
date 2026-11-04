"""Vue admin panel kirishi: Django sessiyasi + Payload'dagi kabi Origin tekshiruvi, bloklash va kirish tarixi."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, check_any_password
from apps.core.activity import log_activity

from .models import LoginEvent
from .request import request_info

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15
SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


def allowed_origins() -> set[str]:
    return set(settings.TRUSTED_ORIGINS) | {settings.PUBLIC_SERVER_URL}


class PanelSessionAuth(SessionAuthentication):
    """CSRF himoyasi token o'rniga Origin bo'yicha (admin panel boshqa manzilda, Payload ham shunday qilardi)."""

    def enforce_csrf(self, request):
        if request.method in SAFE_METHODS:
            return
        origin = request.META.get('HTTP_ORIGIN') or ''
        if not origin:
            referer = request.META.get('HTTP_REFERER') or ''
            origin = '/'.join(referer.split('/')[:3]) if referer.startswith('http') else ''
        if origin.rstrip('/') not in allowed_origins():
            raise PermissionDenied('So‘rov ruxsat etilmagan manzildan keldi')


def error(message: str, code: int = 400) -> Response:
    """Payload xato shakli: { errors: [{ message }] } — admin panel shu ko'rinishni o'qiydi."""
    return Response({'errors': [{'message': message}], 'message': message}, status=code)


def record(request, user, username: str, result: str, method: str = 'password'):
    info = request_info(request)
    LoginEvent.objects.create(user=user, username=username[:100], method=method, result=result, **info)


Credentials = inline_serializer('Credentials', {'username': serializers.CharField(), 'password': serializers.CharField()})


class LoginView(APIView):
    authentication_classes = [PanelSessionAuth]
    permission_classes: list = []

    @extend_schema(tags=['Admin panel: kirish'], request=Credentials, summary='Admin panelga kirish (login va parol)',
                   examples=[OpenApiExample('Kirish', value={'username': 'superadmin', 'password': '••••••••••'})])
    def post(self, request):
        username = str(request.data.get('username') or request.data.get('email') or '').strip()
        password = str(request.data.get('password') or '')
        if not username or not password:
            return error('Login va parolni kiriting', status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(username__iexact=username).first() or User.objects.filter(email__iexact=username).first()
        now = timezone.now()
        if user and user.lock_until and user.lock_until > now:
            record(request, user, username, 'locked')
            return error('Hisob vaqtincha bloklangan — 15 daqiqadan keyin urinib ko‘ring', 423)
        if not user or not check_any_password(user, password):
            if user:
                user.login_attempts += 1
                if user.login_attempts >= MAX_ATTEMPTS:
                    user.lock_until, user.login_attempts = now + timedelta(minutes=LOCK_MINUTES), 0
                user.save(update_fields=['login_attempts', 'lock_until'])
            record(request, user, username, 'bad_password')
            return error('Login yoki parol noto‘g‘ri', status.HTTP_401_UNAUTHORIZED)
        if user.status == 'disabled':
            record(request, user, username, 'denied')
            return error('Hisob yopilgan — superadmin bilan bog‘laning', status.HTTP_403_FORBIDDEN)
        user.login_attempts, user.lock_until = 0, None
        user.last_login = now
        user.save(update_fields=['login_attempts', 'lock_until', 'last_login'])
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        record(request, user, username, 'success')
        from .collections import REGISTRY
        return Response({
            'message': 'Kirish muvaffaqiyatli',
            'user': REGISTRY['users'].out(user, 1),
            'exp': int((now + timedelta(seconds=settings.SESSION_COOKIE_AGE)).timestamp()),
        })


class LogoutView(APIView):
    authentication_classes = [PanelSessionAuth]
    permission_classes: list = []

    @extend_schema(tags=['Admin panel: kirish'], request=None, summary='Chiqish')
    def post(self, request):
        logout(request)
        return Response({'message': 'Chiqildi'})


class MeView(APIView):
    authentication_classes = [PanelSessionAuth]
    permission_classes: list = []

    @extend_schema(tags=['Admin panel: kirish'], summary='Kirgan foydalanuvchi (kirmagan bo‘lsa user: null)')
    def get(self, request):
        from .collections import REGISTRY
        user = request.user if request.user and request.user.is_authenticated and request.user.status != 'disabled' else None
        return Response({'user': REGISTRY['users'].out(user, 1) if user else None, 'collection': 'users'})


class UnlockView(APIView):
    authentication_classes = [PanelSessionAuth]
    permission_classes: list = []

    @extend_schema(tags=['Admin panel: kirish'], request=inline_serializer('Unlock', {'username': serializers.CharField()}),
                   summary='Bloklangan hisobni ochish (superadmin)')
    def post(self, request):
        if not (request.user and request.user.is_authenticated and request.user.role == 'superadmin'):
            return error('Ruxsat yo‘q', status.HTTP_403_FORBIDDEN)
        user = User.objects.filter(username=str(request.data.get('username') or '')).first()
        if not user:
            return error('Foydalanuvchi topilmadi', status.HTTP_404_NOT_FOUND)
        user.login_attempts, user.lock_until = 0, None
        user.save(update_fields=['login_attempts', 'lock_until'])
        log_activity(request, action='role', entity='users', entity_id=user.pk, label=f'{user.name} — blok ochildi')
        return Response({'message': 'Hisob ochildi'})
