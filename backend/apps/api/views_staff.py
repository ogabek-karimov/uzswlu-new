"""Xodimlar (ommaviy) va xodim kabineti (/me — faqat HEMIS orqali kirgan xodim)."""
import re

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttles import ScopedThrottle
from apps.structure.models import StaffProfile

from . import builders_staff as bst
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
