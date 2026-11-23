"""Xodim kabineti → admin panel ko'prigi: sayt ichidagi kabinetdan turib rolga ruxsat etilgan ma'lumotlar bilan ishlash.

Xodim HEMIS orqali kirgan (StaffSession). Ko'prik uning admin hisobini topadi (kerak bo'lsa `access.provision` yaratadi — bu hisob
faqat superadmin lavozimni rolga bog'lagan bo'lsa bo'ladi) va panelning o'sha `CollectionView`/`DocView` kodini ishlatadi: shuning uchun
ruxsatlar (bo'lim × o'qish/yozish), fakultet doirasi, «faqat o'zi yozgan postni tahrirlaydi», versiyalar va faollik jurnali admin paneldagi bilan
BIR XIL. Faqat `CABINET_SLUGS`; ommaviy (where bo'yicha) amallar yo'q; media — faqat yuklash (kutubxonani ko'rish yo'q).
Brauzer bevosita API'ga emas, Nuxt server qatlamiga murojaat qiladi (u sessiyani Bearer sifatida uzatadi) — shuning uchun CSRF xavfi yo'q."""
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied

from apps.accounts import roles as rl
from apps.accounts.models import User
from apps.api.staff_auth import StaffSessionAuthentication
from apps.hemis import access

from . import views as v

CABINET_SLUGS = frozenset({'posts', 'media'})
ACCOUNT_TTL = 60  # soniya: lavozim/rol o'zgarishi shuncha vaqtda kuchga kiradi (HEMIS'ga har so'rovda murojaat qilmaslik uchun)


def account_of(hemis_id: str) -> User | None:
    """Xodimning admin hisobi (yo'q bo'lsa — lavozimga bog'langan rol bo'yicha yaratadi); ruxsat bo'lmasa None."""
    hemis_id = str(hemis_id)
    key = f'cabinet-account:{hemis_id}'
    pk = cache.get(key)
    if pk:
        user = User.objects.filter(pk=pk, hemis_id=hemis_id).exclude(status='disabled').first()
        if user:
            return user
    user = access.provision(hemis_id)
    if user:
        cache.set(key, user.pk, ACCOUNT_TTL)
    return user


class StaffPanelAuth(BaseAuthentication):
    """Kabinet sessiyasi → panel foydalanuvchisi (`request.user` — admin hisob)."""

    def authenticate(self, request):
        res = StaffSessionAuthentication().authenticate(request)
        if not res:
            return None
        principal, token = res
        user = account_of(principal.hemis_id)
        if not user:
            raise PermissionDenied('Admin paneldagi rol berilmagan')
        return user, token

    def authenticate_header(self, request):
        return 'Bearer realm="staff"'


class _Bridge:
    authentication_classes = [StaffPanelAuth]

    def initial(self, request, *args, **kwargs):
        if kwargs.get('slug') not in CABINET_SLUGS:
            raise NotFound()
        super().initial(request, *args, **kwargs)
        if not (request.user and request.user.is_authenticated):
            raise NotAuthenticated()


class CabinetCollectionView(_Bridge, v.CollectionView):
    """GET — ro'yxat (posts), POST — yangi yozuv / media yuklash. Ommaviy PATCH/DELETE yo'q."""
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, slug):
        if slug == 'media':
            raise NotFound()  # kutubxonani ko'rish yo'q — faqat yuklash
        res = super().get(request, slug)
        if slug == 'posts' and res.status_code == 200:
            # `own` — shu hisob tahrirlay/o'chira oladimi (Posts.can bilan bir xil: superadmin va «boshqalarning postlarini ham tahrirlaydi» belgili rollar — hammasi, qolganlar — faqat o'zi yozgan)
            everything = rl.edits_all_posts(request.user)
            for d in res.data.get('docs', []):
                author = d.get('author')
                d['own'] = everything or (author.get('id') if isinstance(author, dict) else author) == request.user.pk
        return res


class CabinetDocView(_Bridge, v.DocView):
    """Bitta yozuv: GET / PATCH / DELETE (media — yo'q)."""

    def initial(self, request, *args, **kwargs):
        if kwargs.get('slug') == 'media':
            raise NotFound()
        super().initial(request, *args, **kwargs)
