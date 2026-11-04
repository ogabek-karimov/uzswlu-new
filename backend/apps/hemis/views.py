"""HEMIS orqali kirish (OAuth2): xodim universitet login-paroli bilan kiradi.

  /api/auth/hemis/status                  — HEMIS ulanganmi (API va OAuth)
  /api/auth/hemis/login?next=admin        — admin panelga (faqat superadmin tayinlagan xodim)
  /api/auth/hemis/login?next=cabinet      — saytdagi xodim kabinetiga
  /api/auth/hemis/callback                — HEMIS qaytaradigan manzil (OAuth client'da shu yoziladi)

.env: HEMIS_OAUTH_URL, HEMIS_OAUTH_CLIENT_ID, HEMIS_OAUTH_CLIENT_SECRET (universitet IT bo'limi beradi).
"""
import json
import secrets
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import StaffSession, User

from . import get_client

ID_FIELDS = ('employee_id_number', 'employee_id', 'id')


def redirect_uri(request) -> str:
    return settings.PUBLIC_SERVER_URL + '/api/auth/hemis/callback'


def _post(url: str, data: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers={'Accept': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=settings.HEMIS_TIMEOUT) as res:  # noqa: S310 — manzil .env'dan
        return json.loads(res.read())


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=settings.HEMIS_TIMEOUT) as res:  # noqa: S310
        body = json.loads(res.read())
    return body.get('data', body) if isinstance(body, dict) else {}


class StatusView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(summary='HEMIS holati: API va kirish (OAuth) ulanganmi')
    def get(self, request):
        synced = get_client().synced_at()
        return Response({
            'api': bool(settings.HEMIS_API_URL and settings.HEMIS_API_TOKEN),
            'oauth': settings.HEMIS_OAUTH_ENABLED,
            'source': 'hemis' if synced else 'namuna',
            'syncedAt': synced.isoformat() if synced else None,
        })


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(summary='HEMIS orqali kirish (yo‘naltiradi)', parameters=[OpenApiParameter('next', str, enum=['admin', 'cabinet'])])
    def get(self, request):
        if not settings.HEMIS_OAUTH_ENABLED:
            return Response({'message': 'HEMIS orqali kirish hali ulanmagan (HEMIS_OAUTH_* sozlamalari yo‘q)'}, status=503)
        state = secrets.token_urlsafe(24)
        request.session['hemis_oauth'] = {'state': state, 'next': 'cabinet' if request.query_params.get('next') == 'cabinet' else 'admin'}
        query = urllib.parse.urlencode({
            'response_type': 'code', 'client_id': settings.HEMIS_OAUTH_CLIENT_ID, 'redirect_uri': redirect_uri(request), 'state': state,
        })
        return HttpResponseRedirect(f'{settings.HEMIS_OAUTH_URL}{settings.HEMIS_OAUTH_AUTHORIZE_PATH}?{query}')


class CallbackView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(summary='HEMIS qaytaradigan manzil (OAuth2 code → sessiya)')
    def get(self, request):
        from apps.panel.auth import record

        saved = request.session.pop('hemis_oauth', None) or {}
        target = saved.get('next', 'admin')
        fail = f'{settings.ADMIN_PANEL_URL}/kirish?hemis=' if target == 'admin' else f'{settings.SITE_URL}/?hemis='
        if not settings.HEMIS_OAUTH_ENABLED or not saved or request.query_params.get('state') != saved.get('state'):
            return HttpResponseRedirect(fail + 'xato')
        try:
            token = _post(f'{settings.HEMIS_OAUTH_URL}{settings.HEMIS_OAUTH_TOKEN_PATH}', {
                'grant_type': 'authorization_code', 'code': request.query_params.get('code', ''),
                'client_id': settings.HEMIS_OAUTH_CLIENT_ID, 'client_secret': settings.HEMIS_OAUTH_CLIENT_SECRET,
                'redirect_uri': redirect_uri(request),
            }).get('access_token')
            info = _get(f'{settings.HEMIS_OAUTH_URL}{settings.HEMIS_OAUTH_USER_PATH}', token) if token else {}
        except Exception:  # noqa: BLE001
            return HttpResponseRedirect(fail + 'javob-yoq')
        hemis_id = next((str(info[k]) for k in ID_FIELDS if info.get(k)), '')
        if not hemis_id:
            return HttpResponseRedirect(fail + 'xato')

        if target == 'cabinet':
            # Saytdagi xodim kabineti: sessiya tokeni cookie'da (bazada faqat hash)
            session_token = StaffSession.issue(hemis_id)
            res = HttpResponseRedirect(f'{settings.SITE_URL}/dashboard')
            res.set_cookie(settings.STAFF_SESSION_COOKIE, session_token, max_age=settings.STAFF_SESSION_TTL_HOURS * 3600,
                           httponly=True, secure=not settings.DEBUG, samesite='Lax')
            return res

        # Admin panel: faqat superadmin tayinlagan (HEMIS ID biriktirilgan) xodim kiradi
        user = User.objects.filter(hemis_id=hemis_id).first()
        if not user or user.status == 'disabled':
            record(request, user, info.get('login') or hemis_id, 'denied', method='hemis')
            return HttpResponseRedirect(fail + 'ruxsat-yoq')
        # Profil HEMIS'dan yangilanadi: F.I.Sh., lavozim, bo'lim
        person = next((s for s in get_client().staff('uz') if s['id'] == hemis_id), None)
        user.name = info.get('name') or (person or {}).get('name') or user.name
        if person and person['employments']:
            user.position = person['employments'][0]['position']['name'][:200]
            user.department = person['employments'][0]['department']['name'][:200]
        user.status, user.last_login = 'active', timezone.now()
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        record(request, user, info.get('login') or hemis_id, 'success', method='hemis')
        return HttpResponseRedirect(settings.ADMIN_PANEL_URL + '/')
