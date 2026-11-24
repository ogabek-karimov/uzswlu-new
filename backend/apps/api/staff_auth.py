"""Xodim kabineti autentifikatsiyasi: HEMIS (my.gov) orqali kirgan xodimning sessiyasi.

Token `session` cookie'sida yoki `Authorization: Bearer <token>` sarlavhasida keladi.
Kirmagan bo'lsa — 401. Sessiyani yaratish: `StaffSession.issue(hemis_id)` (HEMIS/my.gov kirishidan keyin).
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import BasePermission

from apps.accounts.models import StaffSession
from apps.core.utils import sha256


class StaffPrincipal:
    is_authenticated = True

    def __init__(self, hemis_id: str):
        self.hemis_id = hemis_id
        self.pk = hemis_id  # so'rov cheklovlari (throttle) foydalanuvchini shu bo'yicha ajratadi

    def __str__(self):
        return f'staff:{self.hemis_id}'


class StaffSessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get(settings.STAFF_SESSION_COOKIE)
        scheme, _, value = request.META.get('HTTP_AUTHORIZATION', '').partition(' ')
        if scheme.lower() == 'bearer' and value.strip():
            token = value.strip()
        if not token:
            return None
        now = timezone.now()
        session = StaffSession.objects.filter(token_hash=sha256(token), expires_at__gt=now).first()
        if not session:
            raise AuthenticationFailed('Session expired or invalid')
        if not session.last_used or now - session.last_used > timedelta(minutes=5):
            StaffSession.objects.filter(pk=session.pk).update(last_used=now)
        return StaffPrincipal(session.hemis_id), token

    def authenticate_header(self, request):
        return 'Bearer realm="staff"'


class IsStaff(BasePermission):
    """HEMIS orqali kirgan xodim (rolidan qat'i nazar): kabinet bosh sahifasini (Dashboard) ko'ra oladi."""

    def has_permission(self, request, view):
        return isinstance(request.user, StaffPrincipal)


class HasCabinetRole(IsStaff):
    """Kabinetda biror narsa qilish (profil, rasm, hujjatlar): faqat superadmin bergan rol egasi (Foydalanuvchilar → rol + HEMIS ID).
    HEMIS lavozimi rol bermaydi. Rolsiz xodim — 403 (`code: no_role`), u faqat Dashboard va KPI'ni ko'radi."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        from apps.hemis.access import cabinet_allowed
        if not cabinet_allowed(request.user.hemis_id):
            raise PermissionDenied('Admin panelda rol berilmagan — bu amal faqat rol egalariga', code='no_role')
        return True
