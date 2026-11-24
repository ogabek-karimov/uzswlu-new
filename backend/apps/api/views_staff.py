"""Xodimlar (ommaviy) va xodim kabineti (/me — faqat HEMIS orqali kirgan xodim)."""
import re

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttles import ScopedThrottle
from apps.structure.models import StaffProfile

from . import builders_staff as bst
from .common import PublicView, lang_of
from .staff_auth import HasCabinetRole, IsStaff, StaffSessionAuthentication


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
    permission_classes = [HasCabinetRole]  # sukut: faqat rol egasi; ko'rish (GET /me, admin-link) — har qanday kirgan xodim
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'cabinet'

    @property
    def hemis_id(self) -> str:
        return self.request.user.hemis_id


class MeView(CabinetView):
    def get_permissions(self):
        # Dashboard'ni rolsiz xodim ham ko'radi (faqat o'qish); o'zgartirish — faqat rol egasi
        return [IsStaff()] if self.request.method in ('GET', 'HEAD', 'OPTIONS') else super().get_permissions()

    def get(self, request):
        from apps.hemis.access import cabinet_allowed
        return Response({**bst.cabinet_out(self.hemis_id, lang_of(request)), 'hasRole': cabinet_allowed(self.hemis_id)})

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


class MeLogoutView(CabinetView):
    """Kabinetdan chiqish: shu sessiya bazadan o'chiriladi (cookie'ni sayt serveri o'chiradi) — token qayta ishlamaydi."""
    permission_classes = [IsStaff]

    def post(self, request):
        from apps.accounts.models import StaffSession
        from apps.core.utils import sha256
        StaffSession.objects.filter(token_hash=sha256(str(request.auth or ''))).delete()
        return Response({'ok': True})


class MeNotificationsView(CabinetView):
    """Kabinet qo'ng'iroqchasi: xodimning admin hisobi (HEMIS ID) bildirishnomalari; hisobi yo'q (rolsiz) — bo'sh.
    Foydalanuvchi sessiyadan aniqlanadi — so'rovdagi ID bilan boshqa birovnikini olib bo'lmaydi."""
    permission_classes = [IsStaff]

    def get(self, request):
        from apps.core.notify import listing
        from apps.hemis.access import account
        return Response(listing(account(self.hemis_id), 20))

    def post(self, request):
        from apps.core.notify import mark_read
        from apps.hemis.access import account
        ids = request.data.get('ids') if isinstance(request.data, dict) else None
        return Response({'updated': mark_read(account(self.hemis_id), ids if isinstance(ids, list) else None)})


class MeAdminLinkView(CabinetView):
    """Kabinetdagi «Admin panel» tugmasi va saytdagi profil menyusi («Mening bo'limlarim»): xodimning admin hisobi bo'lsa
    (admin bergan, HEMIS ID biriktirilgan) rol nomi, bo'limlari va 60 soniyalik bir martalik havola qaytaradi;
    bo'lmasa available=false. `?list=1` — havolasiz (faqat ro'yxat); `?next=<bo'lim kaliti>` — havola shu bo'limga olib boradi."""
    permission_classes = [IsStaff]  # rolsiz xodimga ham javob beradi: available=false

    def post_stats(self) -> dict:
        """Kabinet bosh sahifasidagi rol paneli uchun: shu xodimning admin hisobi yozgan postlar (hisob hali yaratilmagan bo'lsa — 0)."""
        from django.utils import timezone

        from apps.accounts.models import User
        from apps.content.models import Post
        acc = User.objects.filter(hemis_id=str(self.hemis_id)).first()
        if not acc:
            return {'published': 0, 'drafts': 0, 'month': 0}
        mine = Post.objects.filter(author=acc, deleted_at__isnull=True)
        month_start = timezone.localtime().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return {
            'published': mine.filter(status='published').count(),
            'drafts': mine.filter(status='draft').count(),
            'month': mine.filter(status='published', published_at__gte=month_start).count(),
        }

    def get(self, request):
        from apps.hemis import access
        from apps.hemis.views import handoff_url

        from apps.accounts.roles import SECTION_PATHS, sections_of

        acc = access.panel_access(self.hemis_id)
        if not acc:
            return Response({'available': False, 'url': None, 'role': None, 'sections': []})
        role_name, perms = acc
        sections = sections_of(perms)
        out = {'available': True, 'url': None, 'role': role_name, 'sections': sections}
        if request.query_params.get('list'):
            out['stats'] = self.post_stats()
            return Response(out)
        key = str(request.query_params.get('next') or '')
        if key and key not in {s['key'] for s in sections}:
            raise NotFound('Bo‘lim topilmadi')  # rolda yo'q bo'lim uchun havola berilmaydi
        out['url'] = handoff_url(self.hemis_id, SECTION_PATHS.get(key, '/'))  # admin panel domenida — o'sha domenda sessiya ochiladi
        return Response(out)
