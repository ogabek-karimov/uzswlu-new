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
from django.core import signing
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, StaffSession, User
from apps.accounts.roles import SECTION_PATHS
from apps.core.throttles import ScopedThrottle
from apps.hemis import access

from . import get_client
from .guard import call as guarded

ID_FIELDS = ('employee_id_number', 'employee_id', 'id')


def redirect_uri(request) -> str:
    return settings.PUBLIC_SERVER_URL + '/api/auth/hemis/callback'


HANDOFF_SALT = 'hemis-admin-handoff'
HANDOFF_TTL = 60  # soniya


def handoff_url(hemis_id: str, path: str = '/') -> str:
    """Admin panelga kiritish uchun 60 soniyalik bir martalik havola. Havola ADMIN PANEL manzilida (u /api ni backendga uzatadi):
    sessiya cookie'si admin panel domeniga yoziladi. API domenida kiritilsa, admin panel o'sha brauzerdagi eski sessiyani
    (masalan, superadmin) ochib qo'yardi."""
    from secrets import token_urlsafe
    nonce = token_urlsafe(12)
    cache.set(f'hemis-handoff:{nonce}', 1, HANDOFF_TTL + 5)
    token = signing.dumps({'h': str(hemis_id), 'n': nonce, 'p': path}, salt=HANDOFF_SALT)
    return f'{settings.ADMIN_PANEL_URL}/api/auth/hemis/handoff?t={urllib.parse.quote(token)}'

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
    """Lokal sinov: xodimni tanlab kabinetga kirish (productionda o'chiq). Ro'yxat: admin rol bergan hisoblar (HEMIS ID bilan)
    va rolsiz namunaviy xodimlar — ular faqat Dashboard va KPI'ni ko'radi (HEMIS lavozimi saytda rol bermaydi)."""
    staff = get_client().staff('uz')
    chosen = str(request.query_params.get('as') or '')
    if chosen:
        if not (access.cabinet_allowed(chosen) or any(str(p['id']) == chosen for p in staff)):
            return HttpResponse('Xodim topilmadi', status=404)
        # Cookie sayt manzilida bo'lishi kerak (API boshqa domenda bo'lishi mumkin) — token saytning /api/dev-login iga uzatiladi
        return HttpResponseRedirect(f'{settings.SITE_URL}/api/dev-login?token={urllib.parse.quote(StaffSession.issue(chosen))}')
    roles = {r.slug: r.name for r in Role.objects.all()}
    rows = []
    for u in User.objects.exclude(hemis_id='').exclude(status='disabled').order_by('role', 'name'):
        href = '?next=cabinet&as=' + urllib.parse.quote(u.hemis_id)
        rows.append(f'<li><a href="{html.escape(href)}"><b>{html.escape(roles.get(u.role, u.role))}</b> — {html.escape(u.name or u.username)}'
                    f'<br><small>login: {html.escape(u.username)} · HEMIS ID {html.escape(u.hemis_id)}</small></a></li>')
    if not rows:
        rows.append('<li>Hali hech kimga rol berilmagan (HEMIS ID biriktirilmagan). Admin panel → Foydalanuvchilar → hisob qatoridagi '
                    '«HEMIS» tugmasi (yoki yangi hisobda «HEMIS ID» maydoni).</li>')
    given = set(User.objects.exclude(hemis_id='').values_list('hemis_id', flat=True))
    for p in [p for p in staff if str(p['id']) not in given][:4]:
        href = '?next=cabinet&as=' + urllib.parse.quote(str(p['id']))
        rows.append(f'<li><a href="{html.escape(href)}"><b>Rolsiz xodim</b> — {html.escape(p["name"])}'
                    f'<br><small>faqat Dashboard va KPI · HEMIS ID {html.escape(str(p["id"]))}</small></a></li>')
    page = ('<!doctype html><meta charset="utf-8"><title>Sinov kirishi</title>'
            '<style>body{font:16px system-ui;max-width:640px;margin:40px auto;padding:0 16px}li{list-style:none;margin:8px 0}'
            'a{display:block;padding:12px 16px;border:1px solid #ddd;border-radius:12px;color:#222;text-decoration:none}a:hover{background:#f3f0ff}</style>'
            '<h1>Xodim kabineti — sinov kirishi</h1><p>Faqat lokal sinov (DEBUG). Rol egalari kabinetda ishlaydi, rolsiz xodim faqat Dashboard va KPI bo‘limini ko‘radi:</p>'
            '<ul style="padding:0">' + ''.join(rows) + '</ul>')
    return HttpResponse(page)


def admin_login(request, hemis_id: str, label: str, name: str, fail: str, to: str = '/'):
    """HEMIS ID bo'yicha admin panelga kiritadi (OAuth callback ham, kabinetdan o'tish ham shu yerdan)."""
    from apps.panel.auth import record

    user = access.provision(hemis_id, name)
    if not user:
        record(request, User.objects.filter(hemis_id=hemis_id).first(), label, 'denied', method='hemis')
        return HttpResponseRedirect(fail + 'ruxsat-yoq')
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    record(request, user, label, 'success', method='hemis')
    return HttpResponseRedirect(settings.ADMIN_PANEL_URL + to)


class AdminHandoffView(APIView):
    """Kabinetdagi «Admin panel» tugmasi: qisqa muddatli bir martalik havola bilan HEMIS'dan qayta kirmasdan o'tkazadi."""
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'hemis-auth'

    @extend_schema(summary='Kabinetdan admin panelga o‘tish (bir martalik havola, yo‘naltiradi)', parameters=[OpenApiParameter('t', str)], responses={302: None})
    def get(self, request):
        fail = f'{settings.ADMIN_PANEL_URL}/kirish?hemis='
        try:
            data = signing.loads(str(request.query_params.get('t') or ''), salt=HANDOFF_SALT, max_age=HANDOFF_TTL)
        except signing.BadSignature:
            return HttpResponseRedirect(fail + 'xato')
        if not cache.delete(f'hemis-handoff:{data.get("n")}'):  # bir martalik
            return HttpResponseRedirect(fail + 'xato')
        to = data.get('p') if data.get('p') in SECTION_PATHS.values() else '/'  # faqat admin panelning ma'lum sahifalari (ochiq yo'naltirish yo'q)
        return admin_login(request, str(data['h']), f'hemis:{data["h"]}', '', fail, to)


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
            # Saytdagi xodim kabineti: har qanday xodim kiradi (rolsiz — faqat Dashboard va KPI); sessiya tokeni cookie'da (bazada faqat hash)
            session_token = StaffSession.issue(hemis_id)
            res = HttpResponseRedirect(f'{settings.SITE_URL}/dashboard')
            res.set_cookie(settings.STAFF_SESSION_COOKIE, session_token, max_age=settings.STAFF_SESSION_TTL_HOURS * 3600,
                           httponly=True, secure=not settings.DEBUG, samesite='Lax')
            return res

        # Admin panel: faqat admin HEMIS ID biriktirgan hisob egasi (hisob o'zi yaratilmaydi). Callback API domenida —
        # sessiya admin panel domenida ochilishi uchun bir martalik havola orqali o'sha domenga o'tkaziladi
        if not access.eligible(hemis_id):
            from apps.panel.auth import record
            record(request, User.objects.filter(hemis_id=hemis_id).first(), info.get('login') or hemis_id, 'denied', method='hemis')
            return HttpResponseRedirect(fail + 'ruxsat-yoq')
        return HttpResponseRedirect(handoff_url(hemis_id))

