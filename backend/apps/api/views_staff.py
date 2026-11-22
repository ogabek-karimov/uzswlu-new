"""Xodimlar (ommaviy) va xodim kabineti (/me — faqat HEMIS orqali kirgan xodim)."""
import re

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttles import ScopedThrottle
from apps.structure.models import StaffProfile

from . import builders_staff as bst
from . import cabinet_tasks as ct
from .common import PublicView, lang_of
from .staff_auth import IsStaff, StaffSessionAuthentication


def _int(value, default: int, lo: int, hi: int) -> int:
    try:
        return min(hi, max(lo, int(value)))
    except (TypeError, ValueError):
        return default


class StaffListView(PublicView):
    def get(self, request):
        p = request.query_params
        group = p.get('group') or 'all'
        return Response(bst.staff_list_out(
            lang_of(request),
            q=(p.get('q') or '').strip()[:100],
            department=(p.get('department') or '').strip()[:120],
            group=group if group in ('all', *bst.GROUPS) else 'all',
            page=_int(p.get('page'), 1, 1, 10_000),
            per_page=_int(p.get('perPage'), 24, 1, 48),
        ))


class StaffDetailView(PublicView):
    def get(self, request, pk):
        if not re.fullmatch(r'\d{1,10}', pk):
            raise NotFound('Staff member not found')
        return Response(bst.staff_public_out(pk, lang_of(request)))


class StaffOverlayView(PublicView):
    """Payload bilan mos: /site/staff/:id."""

    def get(self, request, pk):
        return Response(bst.staff_overlay_out(pk, lang_of(request)))


class StaffHiddenView(PublicView):
    """Payload bilan mos: /site/staff-hidden."""

    def get(self, request):
        return Response({'ids': list(StaffProfile.objects.filter(hidden=True).values_list('hemis_id', flat=True))})


class CabinetView(APIView):
    authentication_classes = [StaffSessionAuthentication]
    permission_classes = [IsStaff]
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'cabinet'

    @property
    def hemis_id(self) -> str:
        return self.request.user.hemis_id


class MeView(CabinetView):
    def get(self, request):
        return Response(bst.cabinet_out(self.hemis_id, lang_of(request)))

    def patch(self, request):
        bst.patch_cabinet(self.hemis_id, request.data)
        return Response(bst.cabinet_out(self.hemis_id, lang_of(request)))


class MeAvatarView(CabinetView):
    throttle_scope = 'cabinet-upload'

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            raise bst.Unprocessable('JPG, PNG yoki WEBP, 10 MB gacha')
        bst.set_avatar(self.hemis_id, file)
        return Response({'ok': True})

    def delete(self, request):
        bst.remove_avatar(self.hemis_id)
        return Response({'ok': True})


def _section(value: str) -> str:
    if value not in bst.SECTIONS:
        raise NotFound('Unknown section')
    return value


class MeDocumentsView(CabinetView):
    def get_throttle_scope(self, request):
        # Yuklash (POST) qattiqroq cheklanadi, ro'yxat — umumiy kabinet chegarasi bilan
        return 'cabinet-upload' if request.method == 'POST' else 'cabinet'

    def get(self, request, section):
        return Response(bst.docs_list_out(self.hemis_id, _section(section)))

    def post(self, request, section):
        return Response(bst.add_document(self.hemis_id, _section(section), request.data, request.FILES))


class MeDocumentDetailView(CabinetView):
    def delete(self, request, section, pk):
        bst.delete_document(self.hemis_id, _section(section), pk)
        return Response({'ok': True})


class MeTasksView(CabinetView):
    def get(self, request):
        return Response(ct.tasks_out(self.hemis_id))

    def post(self, request):
        return Response(ct.create_task(self.hemis_id, request.data), status=201)


class MeTaskDetailView(CabinetView):
    def patch(self, request, pk):
        return Response(ct.set_status(self.hemis_id, pk, str(request.data.get('status') or '')))

    def delete(self, request, pk):
        ct.delete_task(self.hemis_id, pk)
        return Response({'ok': True})


class MeAdminLinkView(CabinetView):
    """Kabinetdagi «Admin panel» tugmasi va saytdagi profil menyusi («Mening bo'limlarim»): xodimning admin hisobi bo'lsa
    (yoki lavozimi «HEMIS roli» ga bog'langan bo'lsa) rol nomi, bo'limlari va 60 soniyalik bir martalik havola qaytaradi;
    bo'lmasa available=false. `?list=1` — havolasiz (faqat ro'yxat); `?next=<bo'lim kaliti>` — havola shu bo'limga olib boradi."""

    def get(self, request):
        from secrets import token_urlsafe

        from django.conf import settings
        from django.core import signing
        from django.core.cache import cache

        from apps.hemis import access
        from apps.hemis.views import HANDOFF_SALT, HANDOFF_TTL

        from apps.accounts.roles import SECTION_PATHS, sections_of

        acc = access.panel_access(self.hemis_id)
        if not acc:
            return Response({'available': False, 'url': None, 'role': None, 'sections': []})
        role_name, perms = acc
        sections = sections_of(perms)
        out = {'available': True, 'url': None, 'role': role_name, 'sections': sections}
        if request.query_params.get('list'):
            return Response(out)
        key = str(request.query_params.get('next') or '')
        if key and key not in {s['key'] for s in sections}:
            raise NotFound('Bo‘lim topilmadi')  # rolda yo'q bo'lim uchun havola berilmaydi
        nonce = token_urlsafe(12)
        cache.set(f'hemis-handoff:{nonce}', 1, HANDOFF_TTL + 5)
        token = signing.dumps({'h': self.hemis_id, 'n': nonce, 'p': SECTION_PATHS.get(key, '/')}, salt=HANDOFF_SALT)
        out['url'] = f'{settings.PUBLIC_SERVER_URL}/api/auth/hemis/handoff?t={token}'
        return Response(out)
