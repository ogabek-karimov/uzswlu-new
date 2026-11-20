"""HEMIS orqali kirish (OAuth2): xodim universitet login-paroli bilan kiradi.

  /api/auth/hemis/status                  — HEMIS ulanganmi (API va OAuth)
  /api/auth/hemis/login?next=admin        — admin panelga (faqat superadmin tayinlagan xodim)
  /api/auth/hemis/login?next=cabinet      — saytdagi xodim kabinetiga
  /api/auth/hemis/callback                — HEMIS qaytaradigan manzil (OAuth client'da shu yoziladi)

.env: HEMIS_OAUTH_URL, HEMIS_OAUTH_CLIENT_ID, HEMIS_OAUTH_CLIENT_SECRET (universitet IT bo'limi beradi).
"""
import hmac
import html
import json
import secrets
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import StaffSession, User
from apps.core.throttles import ScopedThrottle

from . import get_client
from .guard import call as guarded

ID_FIELDS = ('employee_id_number', 'employee_id', 'id')


def redirect_uri(request) -> str:
    return settings.PUBLIC_SERVER_URL + '/api/auth/hemis/callback'


MAX_BODY = 1024 * 1024  # HEMIS javobi 1 MB dan oshmasin (xotirani to'ldirib yubormasin)


def _post(url: str, data: dict) -> dict:
    def run():
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers={'Accept': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=settings.HEMIS_OAUTH_TIMEOUT) as res:  # noqa: S310 — manzil .env'dan
            return json.loads(res.read(MAX_BODY))
    return guarded(run)


def _get(url: str, token: str) -> dict:
    def run():
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=settings.HEMIS_OAUTH_TIMEOUT) as res:  # noqa: S310
            return json.loads(res.read(MAX_BODY))
    body = guarded(run)
    return body.get('data', body) if isinstance(body, dict) else {}


class StatusView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'open'

    @extend_schema(summary='HEMIS holati: API va kirish (OAuth) ulanganmi')
    def get(self, request):
        synced = get_client().synced_at()
        return Response({
            'api': bool(settings.HEMIS_API_URL and settings.HEMIS_API_TOKEN),
            'oauth': settings.HEMIS_OAUTH_ENABLED,
            'source': 'hemis' if synced else 'namuna',
            'syncedAt': synced.isoformat() if synced else None,
        })


def dev_login_enabled() -> bool:
    return bool(settings.DEBUG and getattr(settings, 'STAFF_DEV_LOGIN', False) and not settings.HEMIS_OAUTH_ENABLED)


def dev_login(request):
    """Lokal sinov: namunaviy xodimlardan rol tanlab kabinetga kirish (productionda o'chiq)."""
    from apps.api.cabinet_roles import detect_role

    staff = get_client().staff('uz')
    chosen = str(request.query_params.get('as') or '')
    if chosen:
        if not any(str(p['id']) == chosen for p in staff):
            return HttpResponse('Xodim topilmadi', status=404)
        res = HttpResponseRedirect('/dashboard')
        res.set_cookie(settings.STAFF_SESSION_COOKIE, StaffSession.issue(chosen), max_age=settings.STAFF_SESSION_TTL_HOURS * 3600,
                       httponly=True, secure=False, samesite='Lax')
        return res
    names = {'dean': 'Dekan', 'chair_head': 'Kafedra mudiri', 'teacher': 'O‘qituvchi', 'staff': 'Boshqa xodim'}
    by: dict[str, list] = {k: [] for k in names}
    for p in staff:
        role, emp = detect_role(p)
        if role in by and len(by[role]) < 4:
            by[role].append((p, emp))
    rows = []
    for role, label in names.items():
        for p, emp in by[role]:
            pos = ((emp or {}).get('position') or {}).get('name') or ''
            dep = ((emp or {}).get('department') or {}).get('name') or ''
            href = '?next=cabinet&as=' + urllib.parse.quote(str(p['id']))
            rows.append(f'<li><a href="{html.escape(href)}"><b>{html.escape(label)}</b> — {html.escape(p["name"])}<br><small>{html.escape(pos)} · {html.escape(dep)} · ID {html.escape(str(p["id"]))}</small></a></li>')
    page = ('<!doctype html><meta charset="utf-8"><title>Sinov kirishi</title>'
            '<style>body{font:16px system-ui;max-width:640px;margin:40px auto;padding:0 16px}li{list-style:none;margin:8px 0}'
            'a{display:block;padding:12px 16px;border:1px solid #ddd;border-radius:12px;color:#222;text-decoration:none}a:hover{background:#f3f0ff}</style>'
            '<h1>Xodim kabineti — sinov kirishi</h1><p>Faqat lokal sinov (DEBUG). Rolni tanlang:</p><ul style="padding:0">' + ''.join(rows) + '</ul>')
    return HttpResponse(page)


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'hemis-auth'

    @extend_schema(summary='HEMIS orqali kirish (yo‘naltiradi)', parameters=[OpenApiParameter('next', str, enum=['admin', 'cabinet'])])
    def get(self, request):
        if request.query_params.get('next') == 'cabinet' and dev_login_enabled():
            return dev_login(request)
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
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'hemis-auth'

    @extend_schema(summary='HEMIS qaytaradigan manzil (OAuth2 code → sessiya)')
    def get(self, request):
        from apps.panel.auth import record

        saved = request.session.pop('hemis_oauth', None) or {}
        target = saved.get('next', 'admin')
        fail = f'{settings.ADMIN_PANEL_URL}/kirish?hemis=' if target == 'admin' else f'{settings.SITE_URL}/?hemis='
        if not settings.HEMIS_OAUTH_ENABLED or not saved or not hmac.compare_digest(str(request.query_params.get('state') or ''), str(saved.get('state') or '')):
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
