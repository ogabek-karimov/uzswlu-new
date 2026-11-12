"""Vue admin panel API'si (/api/cms/*): kolleksiyalar, globallar, versiyalar — Payload REST bilan bir xil shakl."""
import json

from django.conf import settings
from django.core.exceptions import FieldError, ObjectDoesNotExist, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.activity import log_activity, purge_site_cache, short
from apps.core.models import Media, validate_upload
from apps.core.throttles import ScopedThrottle

from .auth import PANEL_AUTH, error
from .collections import REGISTRY, Collection, Forbidden
from .globals_ import GLOBALS, save_global
from .models import Version
from .query import nested_params, order_by, paginate, where_q
from .usage import media_usage

SKIP_DIFF = {'id', 'createdAt', 'updatedAt', 'views', 'downloads', 'collection', 'globalType', 'loginAttempts', 'lockUntil'}
LONG = {'body', 'description', 'about', 'bio', 'lead', 'sections', 'reports', 'attachments', 'gallery', 'facts', 'timeline'}

LIST_PARAMS = [
    OpenApiParameter('where', OpenApiTypes.OBJECT, description='Payload filtri: where[title.uz][like]=…, where[and][0][status][equals]=published'),
    OpenApiParameter('sort', str, description='Saralash: -publishedAt, order'),
    OpenApiParameter('limit', int), OpenApiParameter('page', int),
    OpenApiParameter('depth', int, description='0 — bog‘liq yozuvlar ID, 1+ — to‘liq obyekt'),
]


def depth_of(request) -> int:
    try:
        return max(0, min(3, int(request.query_params.get('depth', 2))))
    except ValueError:
        return 2


def collection_or_404(slug: str) -> Collection | None:
    return REGISTRY.get(slug)


def diff(before: dict, after: dict) -> dict:
    """Faollik jurnali uchun o'zgarishlar: 4 tilli maydonlar tilma-til, uzun matnlar — '…'."""
    out = {}
    for key in after:
        if key in SKIP_DIFF:
            continue
        a, b = after.get(key), before.get(key)
        if a == b:
            continue
        if isinstance(a, dict) and isinstance(b, dict) and set(a) <= {'uz', 'ru', 'en', 'zh'}:
            for lang in a:
                if a.get(lang) != b.get(lang):
                    long = key in LONG
                    out[f'{key}.{lang}'] = {'before': '…' if long else short(b.get(lang) or ''), 'after': '…' if long else short(a.get(lang) or '')}
            continue
        long = key in LONG or isinstance(a, (list, dict))
        out[key] = {'before': '…' if long else short(b), 'after': '…' if long else short(a)}
    return out


def keep_version(entity: str, entity_id, data: dict, user, limit: int):
    Version.objects.create(entity=entity, entity_id=str(entity_id), data=data, user=user if user and user.is_authenticated else None)
    stale = Version.objects.filter(entity=entity, entity_id=str(entity_id)).order_by('-created_at', '-id').values_list('id', flat=True)[limit:]
    Version.objects.filter(id__in=list(stale)).delete()


class Conflict(ValidationError):
    """409: yozuv boshqa joyda ishlatilmoqda (Payload'dagi kabi)."""


def save_doc(coll: Collection, obj, data: dict, request, creating: bool, log: bool = True):
    """Saqlash: maydonlar → model → ichki ro'yxatlar, keyin faollik jurnali, versiya va sayt keshi."""
    before = None if creating else coll.out(obj, 0)
    with transaction.atomic():
        coll.write(obj, data, request, creating)
        obj.save()
        coll.after(obj, data, request, creating)
    obj = coll.queryset(request).get(pk=obj.pk)
    after = coll.out(obj, 0)
    entity = coll.entity or coll.slug
    if not log:
        pass
    elif creating:
        action = 'publish' if after.get('status') == 'published' else 'create'
        log_activity(request, action=action, entity=entity, entity_id=obj.pk, label=coll.label(obj))
    else:
        changes = diff(before, after)
        if changes:
            if coll.slug == 'users' and ({'role', 'status'} & set(changes)):
                action = 'role'
            else:
                action = coll.action_for(before, after, changes)
            log_activity(request, action=action, entity=entity, entity_id=obj.pk, label=coll.label(obj), changes=changes)
    if coll.versions:
        keep_version(coll.slug, obj.pk, after, request.user, coll.versions)
    purge_site_cache(coll.tags)
    return obj


def parse_body(request) -> dict:
    data = request.data
    if hasattr(data, 'get') and data.get('_payload'):
        try:
            return json.loads(data['_payload'])
        except (TypeError, ValueError):
            return {}
    return data if isinstance(data, dict) else dict(data)


def run(fn):
    """Model xatolari → Payload shaklidagi javob."""
    try:
        return fn()
    except (ValueError, TypeError) as exc:
        if 'expected a number' in str(exc):  # where[id][equals]=abc, [] yoki {} qiymat — Django qidiruv qiymatini aylantira olmadi
            return error('Filtr qiymati noto‘g‘ri: raqam kutilgan', status.HTTP_400_BAD_REQUEST)
        raise
    except Forbidden as exc:
        return error(str(exc) or 'Ruxsat yo‘q', status.HTTP_403_FORBIDDEN)
    except Conflict as exc:
        return error('; '.join(exc.messages), status.HTTP_409_CONFLICT)
    except ValidationError as exc:
        msgs = exc.messages if hasattr(exc, 'messages') else [str(exc)]
        return error('; '.join(msgs))
    except ProtectedError:
        return error('Bu yozuv boshqa joyda ishlatilmoqda — avval o‘sha joydan olib tashlang', status.HTTP_409_CONFLICT)
    except IntegrityError:
        return error('Bunday qiymat allaqachon bor (takrorlanmasligi kerak)')
    except ObjectDoesNotExist:
        return error('Topilmadi', status.HTTP_404_NOT_FOUND)


class PanelView(APIView):
    authentication_classes = PANEL_AUTH
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        u = request.user
        # Majburiy 2FA (REQUIRE_2FA_ROLES): yoqmaguncha panel ma'lumotlariga kirib bo'lmaydi (profil/2FA sozlash yo'llari PanelView emas)
        if u and u.is_authenticated and u.role in settings.REQUIRE_2FA_ROLES and not u.totp_enabled:
            raise PermissionDenied('Rolingiz uchun ikki bosqichli tasdiq (2FA) majburiy — Profil bo‘limida yoqing')

    def get_throttle_scope(self, request):
        return 'panel-read' if request.method in ('GET', 'HEAD', 'OPTIONS') else 'panel-write'

    def user_ok(self, request) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and u.status != 'disabled')


def run_list(coll: Collection, request) -> list:
    """Ommaviy amal uchun yozuvlar (ko'pi bilan 500). `where` majburiy: tasodifan butun jadvalga tegib ketmasligi uchun."""
    if not nested_params(request.query_params).get('where'):
        raise ValidationError('Ommaviy amal uchun `where` shart (masalan: where[id][in]=1,2,3)')
    return list(filtered(coll, request)[:500])


def filtered(coll: Collection, request):
    params = nested_params(request.query_params)
    qs = coll.scope(request, coll.queryset(request))
    qs = qs.filter(where_q(params.get('where'), coll.fields, coll.model))
    try:
        return qs.order_by(*order_by(request.query_params.get('sort'), coll.fields, coll.default_sort, coll.model))
    except FieldError:  # bu kolleksiyada yo'q maydon bo'yicha saralash so'raldi — standart tartib (500 emas)
        return qs.order_by(*order_by(None, coll.fields, coll.default_sort))


@extend_schema(tags=['Admin panel: kolleksiyalar'])
class CollectionView(PanelView):
    @extend_schema(summary='Ro‘yxat (Payload shaklida)', parameters=LIST_PARAMS, responses=OpenApiTypes.OBJECT)
    def get(self, request, slug):
        coll = collection_or_404(slug)
        if not coll:
            return error('Topilmadi', 404)
        if not coll.can(request.user, 'read'):
            return error('Ruxsat yo‘q', 403)
        depth = depth_of(request)
        return run(lambda: Response(paginate(filtered(coll, request), request.query_params, lambda o: coll.out(o, depth))))

    @extend_schema(summary='Yangi yozuv (media — multipart: file + _payload)', request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, slug):
        coll = collection_or_404(slug)
        if not coll:
            return error('Topilmadi', 404)
        if not coll.can(request.user, 'create'):
            return error('Ruxsat yo‘q', 403)
        data = parse_body(request)

        def create():
            obj = coll.model()
            if coll.slug == 'media':
                upload = request.FILES.get('file')
                if not upload:
                    raise ValidationError('Fayl tanlanmagan')
                validate_upload(upload)
                obj.file = upload
            obj = save_doc(coll, obj, data, request, creating=True)
            return Response({'doc': coll.out(obj, depth_of(request)), 'message': 'Saqlandi'}, status=201)
        return run(create)

    @extend_schema(summary='Ommaviy o‘zgartirish (where bo‘yicha)', request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def patch(self, request, slug):
        coll = collection_or_404(slug)
        if not coll or not coll.can(request.user, 'update'):
            return error('Ruxsat yo‘q', 403)
        data = parse_body(request)
        docs, errors = [], []
        try:
            objs = run(lambda: run_list(coll, request))   # noto'g'ri filtr qiymati → 400
        except ValidationError as exc:
            return error('; '.join(exc.messages))
        if isinstance(objs, Response):
            return objs
        for obj in objs:
            if not coll.can(request.user, 'update', obj):
                errors.append({'id': obj.pk, 'message': 'Ruxsat yo‘q'})
                continue
            res = run(lambda o=obj: save_doc(coll, o, data, request, creating=False))
            if isinstance(res, Response):
                errors.append({'id': obj.pk, 'message': res.data['errors'][0]['message']})
            else:
                docs.append(coll.out(res, 0))
        return Response({'docs': docs, 'errors': errors})

    @extend_schema(summary='Ommaviy o‘chirish (postlar — savatga)', responses=OpenApiTypes.OBJECT)
    def delete(self, request, slug):
        coll = collection_or_404(slug)
        if not coll or not coll.can(request.user, 'delete'):
            return error('Ruxsat yo‘q', 403)
        docs, errors = [], []
        try:
            objs = run(lambda: run_list(coll, request))   # noto'g'ri filtr qiymati → 400
        except ValidationError as exc:
            return error('; '.join(exc.messages))
        if isinstance(objs, Response):
            return objs
        for obj in objs:
            if not coll.can(request.user, 'delete', obj):
                errors.append({'id': obj.pk, 'message': 'Ruxsat yo‘q'})
                continue
            res = run(lambda o=obj: delete_doc(coll, o, request))
            (errors.append({'id': obj.pk, 'message': res.data['errors'][0]['message']}) if isinstance(res, Response) else docs.append({'id': obj.pk}))
        return Response({'docs': docs, 'errors': errors})


def delete_doc(coll: Collection, obj, request):
    label = coll.label(obj)
    if coll.slug == 'posts' and obj.deleted_at is None:
        # Postlar avval savatga tushadi (qayta tiklash mumkin)
        obj.deleted_at = timezone.now()
        obj.save(update_fields=['deleted_at'])
    elif coll.slug == 'media':
        used = media_usage(obj.pk)
        if used:
            raise Conflict(f"Fayl ishlatilmoqda: {'; '.join(used[:3])}")
        for path in (obj.sizes or {}).values():
            obj.file.storage.delete(path)
        obj.file.delete(save=False)
        obj.delete()
    else:
        obj.delete()
    log_activity(request, action='delete', entity=coll.entity or coll.slug, entity_id=obj.pk, label=label)
    purge_site_cache(coll.tags)
    return obj


@extend_schema(tags=['Admin panel: kolleksiyalar'])
class CollectionCountView(PanelView):
    @extend_schema(summary='Soni (where bo‘yicha)', parameters=LIST_PARAMS[:1], responses=OpenApiTypes.OBJECT)
    def get(self, request, slug):
        coll = collection_or_404(slug)
        if not coll or not coll.can(request.user, 'read'):
            return error('Ruxsat yo‘q', 403)
        return run(lambda: Response({'totalDocs': filtered(coll, request).count()}))


@extend_schema(tags=['Admin panel: kolleksiyalar'])
class DocView(PanelView):
    def get_obj(self, coll, request, pk):
        return coll.scope(request, coll.queryset(request)).get(pk=pk)

    @extend_schema(summary='Bitta yozuv', responses=OpenApiTypes.OBJECT)
    def get(self, request, slug, pk):
        coll = collection_or_404(slug)
        if not coll or not coll.can(request.user, 'read'):
            return error('Ruxsat yo‘q', 403)
        return run(lambda: Response(coll.out(self.get_obj(coll, request, pk), depth_of(request))))

    @extend_schema(summary='O‘zgartirish', request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def patch(self, request, slug, pk):
        coll = collection_or_404(slug)
        if not coll:
            return error('Topilmadi', 404)

        def update():
            obj = self.get_obj(coll, request, pk)
            if not coll.can(request.user, 'update', obj):
                return error('Ruxsat yo‘q', 403)
            obj = save_doc(coll, obj, parse_body(request), request, creating=False)
            return Response({'doc': coll.out(obj, depth_of(request)), 'message': 'Saqlandi'})
        return run(update)

    @extend_schema(summary='O‘chirish (postlar — savatga, savatdagisi — butunlay)', responses=OpenApiTypes.OBJECT)
    def delete(self, request, slug, pk):
        coll = collection_or_404(slug)
        if not coll or not coll.can(request.user, 'delete'):
            return error('Ruxsat yo‘q', 403)

        def remove():
            obj = self.get_obj(coll, request, pk)
            if not coll.can(request.user, 'delete', obj):
                return error('Ruxsat yo‘q', 403)
            return Response({'doc': {'id': delete_doc(coll, obj, request).pk}, 'message': 'O‘chirildi'})
        return run(remove)


def version_out(v: Version) -> dict:
    stamp = v.created_at.isoformat().replace('+00:00', 'Z')
    parent = int(v.entity_id) if str(v.entity_id).isdigit() else v.entity_id
    return {'id': v.pk, 'parent': parent, 'version': v.data, 'createdAt': stamp, 'updatedAt': stamp, 'latest': False}


VERSION_FIELDS = {'parent': 'entity_id', 'createdAt': 'created_at', 'updatedAt': 'created_at'}


@extend_schema(tags=['Admin panel: versiyalar'])
class VersionsView(PanelView):
    @extend_schema(summary='Saqlangan holatlar (post, sahifa)', parameters=LIST_PARAMS, responses=OpenApiTypes.OBJECT)
    def get(self, request, slug):
        coll = collection_or_404(slug)
        if not coll or not coll.versions or not coll.can(request.user, 'read'):
            return error('Ruxsat yo‘q', 403)
        params = nested_params(request.query_params)
        qs = Version.objects.filter(entity=slug).filter(where_q(params.get('where'), VERSION_FIELDS, Version))
        qs = qs.order_by(*order_by(request.query_params.get('sort'), VERSION_FIELDS, ['-created_at', '-id'], Version))
        return Response(paginate(qs, request.query_params, version_out))

    @extend_schema(summary='Shu holatga qaytarish', request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, slug, vid):
        coll = collection_or_404(slug)
        if not coll or not coll.versions or not coll.can(request.user, 'update'):
            return error('Ruxsat yo‘q', 403)

        def restore():
            v = Version.objects.get(pk=vid, entity=slug)
            obj = coll.queryset(request).get(pk=v.entity_id)
            if not coll.can(request.user, 'update', obj):
                return error('Ruxsat yo‘q', 403)
            data = {k: val for k, val in v.data.items() if k not in SKIP_DIFF and k != 'author'}
            before = coll.out(obj, 0)
            obj = save_doc(coll, obj, data, request, creating=False, log=False)
            log_activity(request, action='restore', entity=coll.slug, entity_id=obj.pk, label=coll.label(obj), changes=diff(before, coll.out(obj, 0)))
            return Response({'doc': coll.out(obj, 1), 'message': 'Qaytarildi'})
        return run(restore)


@extend_schema(tags=['Admin panel: globallar'])
class GlobalView(PanelView):
    @extend_schema(summary='Global sozlama (settings, video-page, symbols, sdg-page, home-banner)', responses=OpenApiTypes.OBJECT)
    def get(self, request, slug):
        g = GLOBALS.get(slug)
        if not g:
            return error('Topilmadi', 404)
        if not g.can(request.user, 'read'):
            return error('Ruxsat yo‘q', 403)
        return Response(g.out(g.load(), depth_of(request)))

    @extend_schema(summary='Global sozlamani saqlash', request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request, slug):
        g = GLOBALS.get(slug)
        if not g or not g.can(request.user, 'update'):
            return error('Ruxsat yo‘q', 403)

        def save():
            obj = g.load()
            before = g.out(obj, 0)
            if g.versions:
                ensure_first_version(g, before)
            with transaction.atomic():
                g.write(obj, parse_body(request), request)
                save_global(g, obj)
            obj = g.load()
            after = g.out(obj, 0)
            changes = {k: {'before': '…', 'after': '…'} for k in after if k not in SKIP_DIFF and after.get(k) != before.get(k)}
            if changes:
                log_activity(request, action='settings', entity=g.entity, label=g.label, changes=changes)
            if g.versions:
                keep_version(g.slug, '', after, request.user, g.versions)
            purge_site_cache(g.tags)
            return Response({'result': g.out(obj, depth_of(request)), 'message': 'Saqlandi'})
        return run(save)


def ensure_first_version(g, current: dict):
    """Birinchi saqlashdan oldin "asl holat" versiyasi."""
    if not Version.objects.filter(entity=g.slug).exists():
        Version.objects.create(entity=g.slug, entity_id='', data=current)


@extend_schema(tags=['Admin panel: versiyalar'])
class GlobalVersionsView(PanelView):
    @extend_schema(summary='Sozlamalar tarixi', parameters=LIST_PARAMS, responses=OpenApiTypes.OBJECT)
    def get(self, request, slug):
        g = GLOBALS.get(slug)
        if not g or not g.versions or not g.can(request.user, 'update'):
            return error('Ruxsat yo‘q', 403)
        ensure_first_version(g, g.out(g.load(), 0))
        params = nested_params(request.query_params)
        qs = Version.objects.filter(entity=slug).filter(where_q(params.get('where'), VERSION_FIELDS, Version))
        qs = qs.order_by(*order_by(request.query_params.get('sort'), VERSION_FIELDS, ['-created_at', '-id'], Version))
        return Response(paginate(qs, request.query_params, version_out))

    @extend_schema(summary='Shu holatga qaytarish', request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, slug, vid):
        g = GLOBALS.get(slug)
        if not g or not g.versions or not g.can(request.user, 'update'):
            return error('Ruxsat yo‘q', 403)

        def restore():
            v = Version.objects.get(pk=vid, entity=slug)
            obj = g.load()
            with transaction.atomic():
                g.write(obj, v.data, request)
                save_global(g, obj)
            after = g.out(g.load(), 0)
            keep_version(g.slug, '', after, request.user, g.versions)
            log_activity(request, action='settings', entity=g.entity, label=f'{g.label} — oldingi holatga qaytarildi')
            purge_site_cache(g.tags)
            return Response({'doc': after, 'message': 'Qaytarildi'})
        return run(restore)


class MediaFileCompat(APIView):
    """Payload'dagi /api/media/file/<nom> manzili — eski havolalar ishlayversin (faylning o'ziga yo'naltiradi)."""

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'open'

    SIZES = {400: 'thumb', 900: 'card', 1920: 'hero'}

    @extend_schema(exclude=True)
    def get(self, request, name):
        import os
        import re

        from django.http import Http404, HttpResponseRedirect
        from django.utils.text import slugify

        stem = os.path.splitext(os.path.basename(name))[0]
        size = None
        found = re.match(r'^(.+)-(\d+)x\d+$', stem)  # Payload o'lchamlari: slide-2-1920x1080.webp
        candidates = [(stem, None)] + ([(found.group(1), self.SIZES.get(int(found.group(2))))] if found else [])
        for base, size in candidates:
            # Django fayl nomi: <papka>/<yil>/<oy>/<nom>-<8 belgi>.<kengaytma>
            m = Media.objects.filter(file__regex=rf'/{re.escape(slugify(base))}-[0-9a-f]{{8}}\.[a-z0-9]+$').first()
            if m:
                return HttpResponseRedirect(m.size_url(size) if size else m.url)
        raise Http404


class PrivateFileView(APIView):
    """Yopiq fayllar (murojaat ilovalari). Faqat superadmin; har doim yuklab olinadi (`attachment`), brauzerda bajarilmaydi."""

    authentication_classes = PANEL_AUTH
    permission_classes: list = []
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'panel-read'

    @extend_schema(
        tags=['Admin: Statistika va yordamchi'], summary='Yopiq faylni yuklab olish (murojaat ilovalari)',
        description='Faqat **superadmin**. Fayl har doim `attachment` sifatida, `nosniff` va `no-store` bilan beriladi. '
                    '`name` — masalan `appeals/2026/11/<uuid>.pdf`. Ochiq `/media/` da bu fayllar yo‘q.',
        responses={200: OpenApiTypes.BINARY, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, name):
        import os

        from django.core.exceptions import SuspiciousFileOperation
        from django.http import FileResponse, Http404
        from django.utils._os import safe_join

        u = request.user
        if not (u and u.is_authenticated and u.status != 'disabled' and u.role == 'superadmin'):
            return error('Ruxsat yo‘q', 403 if u and u.is_authenticated else 401)
        try:
            path = safe_join(settings.PRIVATE_ROOT, name)
        except SuspiciousFileOperation:
            raise Http404 from None
        if not os.path.isfile(path):
            raise Http404
        response = FileResponse(open(path, 'rb'), as_attachment=True, filename=os.path.basename(path))
        response['Content-Type'] = 'application/octet-stream'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Content-Security-Policy'] = "default-src 'none'; sandbox"
        response['Cache-Control'] = 'private, no-store'
        return response
