"""Vue admin panel kolleksiyalari: Django modeli ↔ Payload shaklidagi JSON.

Har bir kolleksiya uchun:
  out()    — model → admin panel kutgan JSON (camelCase, 4 tilli guruhlar, `depth` bo'yicha bog'liq yozuvlar);
  write()  — admin yuborgan JSON → modelning maydonlari (saqlashdan oldin);
  after()  — ichki ro'yxatlar (biriktirmalar, galereya, bo'limlar …) saqlangandan keyin;
  can()    — rol bo'yicha ruxsat (Payload'dagi `access` bilan bir xil).
"""
import re
from datetime import timezone as dt_timezone
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.accounts.models import User
from apps.content.models import (
    Category, DocCategory, Document, Leader, Post, PostAttachment, PostGalleryImage, Slide, Video, VideoCategory,
)
from apps.core.fields import LANGS
from apps.core.models import Activity, Media
from apps.pages.models import Page, PageAttachment, PageFact, PageTimeline, SdgGoal, SdgGoalReport, SdgSection
from apps.structure.models import Department, Faculty, StaffProfile

from .models import LoginEvent

SUPER = frozenset({'superadmin'})
EDITORS = frozenset({'superadmin', 'editor', 'faculty', 'pages'})
PAGES = frozenset({'superadmin', 'pages'})
FACULTY = frozenset({'superadmin', 'faculty'})
SDG = frozenset({'superadmin', 'sdg'})
MEDIA_ROLES = EDITORS | {'sdg'}
ALL = EDITORS | {'sdg'}


class Forbidden(Exception):
    """403: yozuv foydalanuvchining doirasidan (masalan, boshqa fakultet) tashqarida."""


def in_scope(user, value: str | None) -> bool:
    """Fakultet admini faqat o'z fakultetiga (`User.scope` = fakultet manzili) tegishli yozuvni o'zgartira oladi.
    Doirasi belgilanmagan fakultet admini hech narsani o'zgartira olmaydi (xavfsiz sukut). Boshqa rollar — cheklanmagan."""
    if user.role != 'faculty':
        return True
    return bool(user.scope) and value == user.scope


# ─── Yordamchilar ────────────────────────────────────────────────────────────

def i18n_out(value) -> dict:
    value = value if isinstance(value, dict) else {}
    return {lang: (value.get(lang) or None) for lang in LANGS}


def i18n_in(value) -> dict:
    if not isinstance(value, dict):
        return {}
    return {lang: str(value[lang]).strip() for lang in LANGS if value.get(lang) is not None and str(value[lang]).strip()}


def dt(value):
    """ISO 8601, UTC (Payload'dagi kabi: 2026-11-04T10:00:00Z)."""
    if not value:
        return None
    return value.astimezone(dt_timezone.utc).isoformat().replace('+00:00', 'Z')


def parse_dt(value):
    if not value:
        return None
    parsed = parse_datetime(str(value))
    if parsed is None:
        raise ValidationError(f'Sana noto‘g‘ri: {value}')
    return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)


def ref_id(value):
    """Bog'liq yozuv: 5, '5', {'id': 5} yoki None."""
    if isinstance(value, dict):
        value = value.get('id')
    if value in (None, '', 0, '0'):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'ID noto‘g‘ri: {value}') from None


def mime_of(m: Media) -> str:
    name = (m.file.name or '').lower()
    if m.kind == 'pdf' or name.endswith('.pdf'):
        return 'application/pdf'
    if m.kind == 'audio' or name.endswith('.mp3'):
        return 'audio/mpeg'
    ext = name.rsplit('.', 1)[-1] if '.' in name else 'webp'
    return {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'svg': 'image/svg+xml'}.get(ext, f'image/{ext}')


def media_out(m: Media | None, depth: int = 1):
    if m is None:
        return None
    if depth <= 0:
        return m.pk
    return {
        'id': m.pk,
        'url': m.url,
        'filename': m.file.name.rsplit('/', 1)[-1] if m.file else None,
        'mimeType': mime_of(m),
        'filesize': m.filesize,
        'width': m.width,
        'height': m.height,
        'alt': i18n_out(m.alt),
        'folder': m.folder,
        'sizes': {name: {'url': m.size_url(name)} for name in (m.sizes or {})},
        'originalSize': m.original_size,
        'uploadedBy': ({'id': m.uploaded_by_id, 'name': m.uploaded_by.name} if depth > 1 and m.uploaded_by_id else m.uploaded_by_id),
        'createdAt': dt(m.created_at),
        'updatedAt': dt(m.created_at),
    }


def media_ref(value):
    pk = ref_id(value)
    if pk is None:
        return None
    m = Media.objects.filter(pk=pk).first()
    if m is None:
        raise ValidationError(f'Fayl topilmadi: #{pk}')
    return m


def lines_to_lists(value) -> dict:
    """I18n matn (har qatorda bitta) → {lang: [..]} (Payload'dagi hasMany matn)."""
    value = value if isinstance(value, dict) else {}
    return {lang: [ln.strip() for ln in str(value.get(lang) or '').splitlines() if ln.strip()] for lang in LANGS}


def lists_to_lines(value) -> dict:
    if not isinstance(value, dict):
        return {}
    out = {}
    for lang in LANGS:
        items = value.get(lang)
        if isinstance(items, list):
            text = '\n'.join(str(x).strip() for x in items if str(x).strip())
            if text:
                out[lang] = text
    return out


def put(obj, data: dict, mapping: dict):
    """Oddiy maydonlar: {payload_kalit: (model_maydoni, aylantirish)}."""
    for key, (field, conv) in mapping.items():
        if key in data:
            setattr(obj, field, conv(data[key]) if conv else data[key])


def text(v):
    return '' if v is None else str(v).strip()


def num(v, default=0):
    if v in (None, ''):
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        raise ValidationError(f'Raqam noto‘g‘ri: {v}') from None


def flag(v):
    return v in (True, 'true', '1', 1, 'on')


def attachment_out(a, depth, meta_plain=False):
    return {
        'id': str(a.pk),
        'file': media_out(a.file, depth) if a.file_id else None,
        'url': a.url or None,
        'title': i18n_out(a.title),
        'meta': (a.meta or {}).get('uz') if meta_plain else i18n_out(a.meta),
        'display': a.display,
        'height': a.height,
    }


def replace_attachments(manager, model, parent_field: str, parent, items, meta_plain=False):
    if items is None:
        return
    manager.all().delete()
    for i, a in enumerate(items or []):
        if not isinstance(a, dict):
            continue
        file = media_ref(a.get('file'))
        url = text(a.get('url'))
        if not file and not url:
            continue
        meta = a.get('meta')
        model.objects.create(**{
            parent_field: parent,
            'file': file,
            'url': url,
            'title': i18n_in(a.get('title')),
            'meta': ({'uz': text(meta)} if text(meta) else {}) if meta_plain else i18n_in(meta),
            'display': a.get('display') or 'open',
            'height': num(a.get('height'), 680),
            'order': i,
        })


# ─── Asos ────────────────────────────────────────────────────────────────────

class Collection:
    slug = ''
    model = None
    entity = None
    tags: tuple = ()
    fields: dict = {}
    default_sort = ['-id']
    select_related: tuple = ()
    prefetch: tuple = ()
    versions = 0
    access = {'read': ALL, 'create': SUPER, 'update': SUPER, 'delete': SUPER}

    def can(self, user, action: str, obj=None) -> bool:
        return bool(user and user.is_authenticated and user.status != 'disabled' and user.role in self.access.get(action, ()))

    def queryset(self, request):
        return self.model.objects.select_related(*self.select_related).prefetch_related(*self.prefetch)

    def scope(self, request, qs):
        return qs

    def label(self, obj) -> str:
        title = getattr(obj, 'title', None)
        if isinstance(title, dict):
            return title.get('uz') or str(obj)
        return str(obj)

    def out(self, obj, depth: int) -> dict:
        raise NotImplementedError

    def write(self, obj, data: dict, request, creating: bool):
        raise NotImplementedError

    def after(self, obj, data: dict, request, creating: bool):
        pass

    def action_for(self, before: dict, after: dict, changes: dict) -> str:
        return 'hide' if after.get('hidden') and 'hidden' in changes else 'show' if 'hidden' in changes else 'edit'


# ─── Foydalanuvchilar ───────────────────────────────────────────────────────

class Users(Collection):
    slug = 'users'
    model = User
    default_sort = ['name']
    select_related = ('avatar',)
    access = {'read': ALL, 'create': SUPER, 'update': ALL, 'delete': SUPER}
    fields = {'hemisId': 'hemis_id', 'lockUntil': 'lock_until', 'createdAt': 'date_joined', 'updatedAt': 'date_joined'}

    def can(self, user, action, obj=None):
        if not super().can(user, action, obj):
            return False
        if action == 'update' and user.role != 'superadmin':
            return obj is not None and obj.pk == user.pk
        return True

    def scope(self, request, qs):
        return qs if request.user.role == 'superadmin' else qs.filter(pk=request.user.pk)

    def label(self, obj):
        return obj.name or obj.username

    def out(self, u, depth):
        return {
            'id': u.pk, 'name': u.name, 'username': u.username, 'email': u.email or None, 'role': u.role, 'status': u.status,
            'position': u.position or None, 'department': u.department or None, 'scope': u.scope or None,
            'hemisId': u.hemis_id or None, 'avatar': media_out(u.avatar, depth) if u.avatar_id else None,
            'loginAttempts': u.login_attempts, 'lockUntil': dt(u.lock_until),
            'createdAt': dt(u.date_joined), 'updatedAt': dt(u.date_joined), 'collection': 'users',
        }

    @staticmethod
    def require_current_password(u, current) -> None:
        """O'z parolini almashtirishda joriy parol shart: o'g'irlangan sessiya/JWT bilan parolni almashtirib bo'lmaydi.
        Noto'g'ri urinishlar keshda sanaladi (tranzaksiya bekor bo'lsa ham yo'qolmaydi): 15 daqiqada 5 tadan keyin to'xtatiladi."""
        from django.core.cache import cache

        from apps.accounts.models import check_any_password
        key = f'pwchange:{u.pk}'
        if cache.get(key, 0) >= 5:
            raise Forbidden('Juda ko‘p noto‘g‘ri urinish — 15 daqiqadan keyin urinib ko‘ring')
        if not current:
            raise ValidationError('Hozirgi parolni kiriting')
        if not check_any_password(u, str(current)):
            cache.add(key, 0, 900)
            cache.incr(key)
            raise ValidationError('Hozirgi parol noto‘g‘ri')
        cache.delete(key)

    def write(self, u, data, request, creating):
        is_super = request.user.role == 'superadmin'
        put(u, data, {'name': ('name', text), 'position': ('position', text), 'department': ('department', text)})
        if is_super:
            put(u, data, {
                'username': ('username', text), 'email': ('email', text), 'scope': ('scope', text),
                'hemisId': ('hemis_id', text),
            })
            if 'role' in data:
                if data['role'] not in dict(User.ROLES):
                    raise ValidationError('Rol noto‘g‘ri')
                u.role = data['role']
                u.is_superuser = data['role'] == 'superadmin'
            if 'status' in data:
                if data['status'] not in dict(User.STATUSES):
                    raise ValidationError('Holat noto‘g‘ri')
                u.status = data['status']
        if 'avatar' in data:
            u.avatar = media_ref(data['avatar'])
        if creating and not u.username:
            raise ValidationError('Login majburiy')
        if not u.name:
            u.name = u.username
        if data.get('password'):
            if not creating and u.pk == request.user.pk:
                self.require_current_password(u, data.get('currentPassword'))
            from django.contrib.auth.password_validation import validate_password
            validate_password(data['password'], u)
            u.set_password(data['password'])
            u.login_attempts, u.lock_until = 0, None
        elif creating:
            raise ValidationError('Parol majburiy')


# ─── Media ──────────────────────────────────────────────────────────────────

def _media_kind(op, value):
    from django.db.models import Q
    v = str(value or '')
    kind = 'pdf' if 'pdf' in v else 'audio' if v.startswith('audio') else 'image' if v.startswith('image') else None
    if kind is None:
        return Q()
    q = Q(kind=kind)
    return ~q if op in ('not_equals', 'not_in') else q


class Medias(Collection):
    slug = 'media'
    model = Media
    entity = 'media'
    default_sort = ['-created_at', '-id']
    select_related = ('uploaded_by',)
    access = {'read': ALL, 'create': MEDIA_ROLES, 'update': MEDIA_ROLES, 'delete': SUPER}
    fields = {'filename': 'file', 'mimeType': _media_kind, 'filesize': 'filesize', 'createdAt': 'created_at', 'alt.uz': 'alt__uz'}

    def label(self, m):
        return str(m)

    def out(self, m, depth):
        return media_out(m, max(depth, 1))

    def write(self, m, data, request, creating):
        if 'alt' in data:
            m.alt = i18n_in(data['alt'])
        if data.get('folder') in dict(Media.FOLDERS):
            m.folder = data['folder']
        if creating and request.user.is_authenticated:
            m.uploaded_by = request.user


# ─── Postlar ────────────────────────────────────────────────────────────────

class Categories(Collection):
    slug = 'categories'
    model = Category
    default_sort = ['key']

    def out(self, c, depth):
        return {'id': c.pk, 'key': c.key, 'name': i18n_out(c.name)}

    def write(self, c, data, request, creating):
        put(c, data, {'key': ('key', text), 'name': ('name', i18n_in)})


class Posts(Collection):
    slug = 'posts'
    model = Post
    tags = ('posts', 'home')
    versions = 30
    default_sort = ['-published_at', '-id']
    select_related = ('category', 'author', 'author__avatar', 'cover', 'cover_ru', 'cover_en', 'cover_zh')
    prefetch = ('attachments__file', 'gallery__image')
    access = {'read': ALL, 'create': EDITORS, 'update': EDITORS, 'delete': EDITORS}
    fields = {
        'publishedAt': 'published_at', 'startsAt': 'starts_at', 'endsAt': 'ends_at', 'deletedAt': 'deleted_at',
        'createdAt': 'created_at', 'updatedAt': 'updated_at', 'label': 'title__uz',
    }

    def queryset(self, request):
        qs = super().queryset(request)
        return qs if request.query_params.get('trash') == 'true' else qs.filter(deleted_at__isnull=True)

    def out(self, p, depth):
        author = None
        if p.author_id:
            author = p.author_id if depth <= 0 else {
                'id': p.author_id, 'name': p.author.name, 'position': p.author.position or None,
                'avatar': media_out(p.author.avatar, depth - 1) if p.author.avatar_id else None,
            }
        return {
            'id': p.pk, 'type': p.type, 'title': i18n_out(p.title), 'excerpt': i18n_out(p.excerpt), 'body': i18n_out(p.body),
            'label': p.title.get('uz') or '', 'slug': p.slug or None,
            'category': (p.category_id if depth <= 0 else {'id': p.category_id, 'key': p.category.key, 'name': i18n_out(p.category.name)}) if p.category_id else None,
            'sdg': p.sdg,
            'cover': media_out(p.cover, depth) if p.cover_id else None,
            'coverByLang': {
                'ru': media_out(p.cover_ru, depth) if p.cover_ru_id else None,
                'en': media_out(p.cover_en, depth) if p.cover_en_id else None,
                'zh': media_out(p.cover_zh, depth) if p.cover_zh_id else None,
            },
            'gallery': [media_out(g.image, depth) for g in p.gallery.all()],
            'attachments': [attachment_out(a, depth) for a in p.attachments.all()],
            'tags': lines_to_lists(p.tags),
            'author': author,
            'publishedAt': dt(p.published_at), 'status': p.status, 'hidden': p.hidden,
            'startsAt': dt(p.starts_at), 'endsAt': dt(p.ends_at), 'location': i18n_out(p.location), 'views': p.views,
            'createdAt': dt(p.created_at), 'updatedAt': dt(p.updated_at), 'deletedAt': dt(p.deleted_at),
        }

    def write(self, p, data, request, creating):
        put(p, data, {
            'title': ('title', i18n_in), 'excerpt': ('excerpt', i18n_in), 'body': ('body', i18n_in), 'location': ('location', i18n_in),
            'slug': ('slug', text), 'sdg': ('sdg', num), 'status': ('status', text), 'hidden': ('hidden', flag),
            'publishedAt': ('published_at', parse_dt), 'startsAt': ('starts_at', parse_dt), 'endsAt': ('ends_at', parse_dt),
            'deletedAt': ('deleted_at', parse_dt),
        })
        if 'type' in data and data['type'] in dict(Post.TYPES):
            p.type = data['type']
        if 'tags' in data:
            p.tags = lists_to_lines(data['tags'])
        if 'category' in data:
            cid = ref_id(data['category'])
            p.category = Category.objects.filter(pk=cid).first() if cid else None
        if 'cover' in data:
            p.cover = media_ref(data['cover'])
        by_lang = data.get('coverByLang')
        if isinstance(by_lang, dict):
            for lang in ('ru', 'en', 'zh'):
                if lang in by_lang:
                    setattr(p, f'cover_{lang}', media_ref(by_lang[lang]))
        if creating and not p.author_id and request.user.is_authenticated:
            p.author = request.user
        if not p.title.get('uz'):
            raise ValidationError('O‘zbekcha sarlavha majburiy')
        if p.status not in dict(Post.STATUSES):
            raise ValidationError('Holat noto‘g‘ri')
        p.clean()

    def after(self, p, data, request, creating):
        if 'gallery' in data:
            p.gallery.all().delete()
            for i, item in enumerate(data.get('gallery') or []):
                m = media_ref(item)
                if m:
                    PostGalleryImage.objects.create(post=p, image=m, order=i)
        if 'attachments' in data:
            replace_attachments(p.attachments, PostAttachment, 'post', p, data.get('attachments'))

    def action_for(self, before, after, changes):
        if 'hidden' in changes:
            return 'hide' if after.get('hidden') else 'show'
        if 'status' in changes and after.get('status') == 'published':
            return 'publish'
        return 'edit'


# ─── Karusel, rahbariyat, hujjatlar, video ──────────────────────────────────

class Slides(Collection):
    slug = 'slides'
    model = Slide
    tags = ('home',)
    default_sort = ['order', 'id']
    select_related = ('image',)
    fields = {'startsAt': 'starts_at', 'endsAt': 'ends_at'}

    def label(self, s):
        return s.name

    def out(self, s, depth):
        return {
            'id': s.pk, 'name': s.name, 'image': media_out(s.image, depth) if s.image_id else None, 'alt': i18n_out(s.alt),
            'link': s.link or None, 'startsAt': dt(s.starts_at), 'endsAt': dt(s.ends_at), 'order': s.order,
        }

    def write(self, s, data, request, creating):
        put(s, data, {'name': ('name', text), 'alt': ('alt', i18n_in), 'link': ('link', text),
                      'startsAt': ('starts_at', parse_dt), 'endsAt': ('ends_at', parse_dt), 'order': ('order', num)})
        if 'image' in data:
            s.image = media_ref(data['image'])
        if not s.image_id:
            raise ValidationError('Rasm majburiy')


class Leaders(Collection):
    slug = 'leaders'
    model = Leader
    tags = ('leadership', 'contact')
    default_sort = ['order', 'id']
    select_related = ('photo',)
    fields = {'staffId': 'staff_id'}

    def label(self, x):
        return x.name

    def out(self, x, depth):
        return {
            'id': x.pk, 'kind': x.kind, 'name': x.name, 'staffId': x.staff_id or None,
            'photo': media_out(x.photo, depth) if x.photo_id else None, 'role': i18n_out(x.role), 'hours': i18n_out(x.hours),
            'phone': x.phone or None, 'ext': x.ext or None, 'email': x.email or None, 'reception': x.reception, 'order': x.order,
        }

    def write(self, x, data, request, creating):
        put(x, data, {'kind': ('kind', text), 'name': ('name', text), 'staffId': ('staff_id', text), 'role': ('role', i18n_in),
                      'hours': ('hours', i18n_in), 'phone': ('phone', text), 'ext': ('ext', text), 'email': ('email', text),
                      'reception': ('reception', flag), 'order': ('order', num)})
        if 'photo' in data:
            x.photo = media_ref(data['photo'])


class DocCategories(Collection):
    slug = 'doc-categories'
    model = DocCategory
    tags = ('documents',)
    default_sort = ['order', 'id']
    access = {'read': ALL, 'create': PAGES, 'update': PAGES, 'delete': SUPER}

    def out(self, c, depth):
        return {'id': c.pk, 'title': i18n_out(c.title), 'order': c.order}

    def write(self, c, data, request, creating):
        put(c, data, {'title': ('title', i18n_in), 'order': ('order', num)})


class Documents(Collection):
    slug = 'documents'
    model = Document
    tags = ('documents',)
    default_sort = ['order', 'id']
    select_related = ('category', 'file_uz', 'file_ru', 'file_en', 'file_zh')
    access = {'read': ALL, 'create': PAGES, 'update': PAGES, 'delete': PAGES}

    def out(self, d, depth):
        return {
            'id': d.pk, 'title': i18n_out(d.title),
            'category': (d.category_id if depth <= 0 else {'id': d.category_id, 'title': i18n_out(d.category.title)}),
            'number': d.number or None,
            'files': {lang: media_out(getattr(d, f'file_{lang}'), depth) if getattr(d, f'file_{lang}_id') else None for lang in LANGS},
            'url': d.url or None, 'display': d.display, 'height': d.height, 'pages': d.page_list,
            'downloads': d.downloads, 'order': d.order, 'updatedAt': dt(getattr(d, 'updated_at', None)),
        }

    def write(self, d, data, request, creating):
        put(d, data, {'title': ('title', i18n_in), 'number': ('number', text), 'url': ('url', text), 'display': ('display', text),
                      'height': ('height', num), 'order': ('order', num)})
        if 'category' in data:
            cid = ref_id(data['category'])
            d.category = DocCategory.objects.filter(pk=cid).first() if cid else None
            if d.category is None:
                raise ValidationError('Toifani tanlang')
        files = data.get('files')
        if isinstance(files, dict):
            for lang in LANGS:
                if lang in files:
                    setattr(d, f'file_{lang}', media_ref(files[lang]))
        if 'pages' in data:
            d.pages = ','.join(str(x).strip().lstrip('/') for x in (data['pages'] or []) if str(x).strip())
        if not d.title.get('uz'):
            raise ValidationError('O‘zbekcha nomi majburiy')
        d.clean()


def youtube_id(url: str) -> str | None:
    m = re.search(r'(?:youtu\.be/|v=|/shorts/|/embed/|/live/)([\w-]{11})', url or '')
    return m.group(1) if m else None


class VideoCategories(Collection):
    slug = 'video-categories'
    model = VideoCategory
    tags = ('videos',)
    default_sort = ['order', 'id']
    access = {'read': ALL, 'create': PAGES, 'update': PAGES, 'delete': SUPER}

    def out(self, c, depth):
        return {'id': c.pk, 'key': c.key, 'title': i18n_out(c.title), 'greeting': c.greeting or None, 'order': c.order}

    def write(self, c, data, request, creating):
        put(c, data, {'key': ('key', text), 'title': ('title', i18n_in), 'greeting': ('greeting', text), 'order': ('order', num)})


class Videos(Collection):
    slug = 'videos'
    model = Video
    tags = ('videos',)
    default_sort = ['order', 'id']
    select_related = ('category',)
    access = {'read': ALL, 'create': PAGES, 'update': PAGES, 'delete': PAGES}

    def out(self, v, depth):
        return {
            'id': v.pk, 'url': v.url, 'title': i18n_out(v.title),
            'category': v.category_id if depth <= 0 else {'id': v.category_id, 'key': v.category.key, 'title': i18n_out(v.category.title)},
            'teacher': v.teacher or None, 'duration': v.duration or None, 'thumbnail': v.thumbnail or None, 'order': v.order,
        }

    def write(self, v, data, request, creating):
        put(v, data, {'url': ('url', text), 'title': ('title', i18n_in), 'teacher': ('teacher', text), 'duration': ('duration', text),
                      'thumbnail': ('thumbnail', text), 'order': ('order', num)})
        if 'category' in data:
            v.category = VideoCategory.objects.filter(pk=ref_id(data['category'])).first()
            if v.category is None:
                raise ValidationError('Toifani tanlang')
        vid = youtube_id(v.url)
        if vid and not v.thumbnail:
            v.thumbnail = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'


# ─── Tuzilma ────────────────────────────────────────────────────────────────

class Faculties(Collection):
    slug = 'faculties'
    model = Faculty
    tags = ('faculties', 'home')
    default_sort = ['order', 'id']
    select_related = ('logo', 'cover')
    fields = {'mapUrl': 'map_url'}
    access = {'read': ALL, 'create': SUPER, 'update': FACULTY, 'delete': SUPER}

    def can(self, user, action, obj=None):
        if not super().can(user, action, obj):
            return False
        if action == 'update' and obj is not None:
            return in_scope(user, obj.slug)  # IDOR: boshqa fakultetni id bilan o'zgartirib bo'lmaydi
        return True

    def out(self, f, depth):
        return {
            'id': f.pk, 'slug': f.slug, 'name': i18n_out(f.name), 'logo': media_out(f.logo, depth) if f.logo_id else None,
            'cover': media_out(f.cover, depth) if f.cover_id else None, 'about': i18n_out(f.about), 'phone': f.phone or None,
            'email': f.email or None, 'address': i18n_out(f.address), 'mapUrl': f.map_url or None, 'order': f.order,
        }

    def write(self, f, data, request, creating):
        put(f, data, {'slug': ('slug', text), 'name': ('name', i18n_in), 'about': ('about', i18n_in), 'phone': ('phone', text),
                      'email': ('email', text), 'address': ('address', i18n_in), 'mapUrl': ('map_url', text), 'order': ('order', num)})
        for key in ('logo', 'cover'):
            if key in data:
                setattr(f, key, media_ref(data[key]))


class Departments(Collection):
    slug = 'departments'
    model = Department
    tags = ('faculties',)
    default_sort = ['hemis_id']
    select_related = ('image',)
    fields = {'hemisId': 'hemis_id', 'faculty': 'faculty_slug'}
    access = {'read': ALL, 'create': FACULTY, 'update': FACULTY, 'delete': SUPER}

    def can(self, user, action, obj=None):
        if not super().can(user, action, obj):
            return False
        if action in ('update', 'create') and obj is not None:
            return in_scope(user, obj.faculty_slug)  # IDOR: boshqa fakultet kafedrasi
        return True

    def label(self, d):
        return d.name.get('uz') or d.hemis_id

    def out(self, d, depth):
        return {
            'id': d.pk, 'hemisId': d.hemis_id, 'faculty': d.faculty_slug or None, 'name': i18n_out(d.name),
            'image': media_out(d.image, depth) if d.image_id else None, 'about': i18n_out(d.about), 'room': d.room or None,
            'ext': d.ext or None, 'showStaff': d.show_staff,
        }

    def write(self, d, data, request, creating):
        put(d, data, {'hemisId': ('hemis_id', text), 'faculty': ('faculty_slug', text), 'name': ('name', i18n_in),
                      'about': ('about', i18n_in), 'room': ('room', text), 'ext': ('ext', text), 'showStaff': ('show_staff', flag)})
        if 'image' in data:
            d.image = media_ref(data['image'])
        if not in_scope(request.user, d.faculty_slug):
            # Yangi yozuv yoki kafedrani boshqa fakultetga ko'chirish ham doiradan tashqari
            raise Forbidden('Bu fakultet sizning doirangizda emas')


SCIENCE = {
    'orcid': (lambda v: v if v.startswith('http') else f'https://orcid.org/{v}', lambda u: re.sub(r'^https?://orcid\.org/', '', u)),
    'scholar': (lambda v: v, lambda u: u),
    'scopus': (lambda v: v if v.startswith('http') else f'https://www.scopus.com/authid/detail.uri?authorId={v}',
               lambda u: (parse_qs(urlparse(u).query).get('authorId') or [u])[0]),
    'researchgate': (lambda v: v, lambda u: u),
}


class StaffProfiles(Collection):
    slug = 'staff-profiles'
    model = StaffProfile
    entity = 'staff-profiles'
    tags = ('staff',)
    default_sort = ['hemis_id']
    fields = {'hemisId': 'hemis_id', 'bio.uz': 'about__uz'}

    def label(self, p):
        return p.name or p.hemis_id

    def out(self, p, depth):
        science = {s.get('network'): s.get('url') for s in (p.science or []) if isinstance(s, dict)}
        doc = {'id': p.pk, 'hemisId': p.hemis_id, 'name': p.name or None, 'bio': i18n_out(p.about), 'hidden': p.hidden}
        for net, (_, back) in SCIENCE.items():
            doc[net] = back(science[net]) if science.get(net) else None
        return doc

    def write(self, p, data, request, creating):
        put(p, data, {'hemisId': ('hemis_id', text), 'name': ('name', text), 'bio': ('about', i18n_in), 'hidden': ('hidden', flag)})
        current = {s.get('network'): s for s in (p.science or []) if isinstance(s, dict)}
        for net, (to_url, _) in SCIENCE.items():
            if net in data:
                value = text(data[net])
                if value:
                    current[net] = {'network': net, 'url': to_url(value)}
                else:
                    current.pop(net, None)
        p.science = [current[n] for n in SCIENCE if n in current] + [v for k, v in current.items() if k not in SCIENCE]


# ─── BRM va sahifalar ───────────────────────────────────────────────────────

class SdgGoals(Collection):
    slug = 'sdg-goals'
    model = SdgGoal
    tags = ('sdg',)
    default_sort = ['n']
    prefetch = ('sections__images', 'reports__file')
    access = {'read': ALL, 'create': SUPER, 'update': SDG, 'delete': SUPER}

    def label(self, g):
        return f"BRM {g.n} — {g.title.get('uz', '')}"

    def out(self, g, depth):
        return {
            'id': g.pk, 'n': g.n, 'title': i18n_out(g.title), 'subtitle': i18n_out(g.subtitle), 'url': g.url,
            'impactRank': g.impact_rank or None, 'impactScore': g.impact_score or None,
            'highlight': {'label': g.highlight_label or None, 'value': i18n_out(g.highlight_value)},
            'sections': [
                {'id': str(s.pk), 'key': s.key or None, 'title': i18n_out(s.title), 'body': i18n_out(s.body),
                 'images': [media_out(m, depth) for m in s.images.all()]}
                for s in g.sections.all()
            ],
            'reports': [attachment_out(r, depth, meta_plain=True) for r in g.reports.all()],
        }

    def write(self, g, data, request, creating):
        put(g, data, {'title': ('title', i18n_in), 'subtitle': ('subtitle', i18n_in), 'url': ('url', text),
                      'impactRank': ('impact_rank', text), 'impactScore': ('impact_score', text)})
        hl = data.get('highlight')
        if isinstance(hl, dict):
            g.highlight_label = text(hl.get('label'))
            g.highlight_value = i18n_in(hl.get('value'))
        if creating:
            g.n = num(data.get('n'))

    def after(self, g, data, request, creating):
        if 'sections' in data:
            g.sections.all().delete()
            for i, s in enumerate(data.get('sections') or []):
                if not isinstance(s, dict):
                    continue
                section = SdgSection.objects.create(goal=g, key=text(s.get('key')), title=i18n_in(s.get('title')) or {'uz': 'Bo‘lim'},
                                                    body=i18n_in(s.get('body')), order=i)
                section.images.set([m for m in (media_ref(x) for x in s.get('images') or []) if m])
        if 'reports' in data:
            replace_attachments(g.reports, SdgGoalReport, 'goal', g, data.get('reports'), meta_plain=True)


class Pages(Collection):
    slug = 'pages'
    model = Page
    tags = ('menu', 'pages')
    versions = 20
    default_sort = ['order', 'id']
    select_related = ('file',)
    prefetch = ('facts', 'timeline', 'attachments__file')
    fields = {'groupKey': 'group_key', 'inMenu': 'in_menu'}
    access = {'read': ALL, 'create': PAGES, 'update': PAGES, 'delete': PAGES}

    def out(self, p, depth):
        return {
            'id': p.pk, 'title': i18n_out(p.title), 'template': p.template, 'parent': p.parent_id, 'slug': p.slug or None,
            'url': p.url or None, 'file': media_out(p.file, depth) if p.file_id else None, 'groupKey': p.group_key or None,
            'description': i18n_out(p.description), 'overview': p.overview or None, 'sdg': p.sdg, 'inMenu': p.in_menu,
            'published': p.published, 'highlight': p.highlight, 'lead': i18n_out(p.lead),
            'body': {k: (v.replace('<!-- timeline -->', '<p>[[timeline]]</p>') if v else v) for k, v in i18n_out(p.body).items()},
            'facts': [{'id': str(f.pk), 'value': f.value, 'label': i18n_out(f.label)} for f in p.facts.all()],
            'timeline': [{'id': str(t.pk), 'label': i18n_out(t.label), 'text': i18n_out(t.text), 'highlight': t.highlight} for t in p.timeline.all()],
            'attachments': [attachment_out(a, depth) for a in p.attachments.all()],
            'order': p.order, 'updatedAt': dt(p.updated_at),
        }

    def write(self, p, data, request, creating):
        put(p, data, {'title': ('title', i18n_in), 'template': ('template', text), 'slug': ('slug', lambda v: text(v) or None),
                      'url': ('url', text), 'groupKey': ('group_key', text), 'description': ('description', i18n_in),
                      'overview': ('overview', text), 'inMenu': ('in_menu', flag), 'published': ('published', flag),
                      'highlight': ('highlight', flag), 'lead': ('lead', i18n_in), 'body': ('body', i18n_in), 'order': ('order', num)})
        if 'sdg' in data:
            p.sdg = num(data['sdg'], None) or None
        if 'parent' in data:
            pid = ref_id(data['parent'])
            if pid and p.pk and pid == p.pk:
                raise ValidationError('Sahifa o‘zining ichiga qo‘yilmaydi')
            p.parent = Page.objects.filter(pk=pid).first() if pid else None
        if 'file' in data:
            p.file = media_ref(data['file'])
        if not p.title.get('uz'):
            raise ValidationError('O‘zbekcha nomi majburiy')
        if p.slug and Page.objects.filter(slug=p.slug).exclude(pk=p.pk).exists():
            raise ValidationError(f'“/{p.slug}” manzili band — boshqa manzil tanlang')
        p.clean()

    def after(self, p, data, request, creating):
        if 'facts' in data:
            p.facts.all().delete()
            for i, f in enumerate(data.get('facts') or []):
                if isinstance(f, dict) and text(f.get('value')):
                    PageFact.objects.create(page=p, value=text(f['value'])[:40], label=i18n_in(f.get('label')), order=i)
        if 'timeline' in data:
            p.timeline.all().delete()
            for i, t in enumerate(data.get('timeline') or []):
                if isinstance(t, dict):
                    PageTimeline.objects.create(page=p, label=i18n_in(t.get('label')), text=i18n_in(t.get('text')),
                                                highlight=flag(t.get('highlight')), order=i)
        if 'attachments' in data:
            replace_attachments(p.attachments, PageAttachment, 'page', p, data.get('attachments'))


# ─── Faqat o'qish: kirish tarixi va faollik ─────────────────────────────────

class LoginEvents(Collection):
    slug = 'login-events'
    model = LoginEvent
    default_sort = ['-created_at']
    select_related = ('user',)
    access = {'read': SUPER}
    fields = {'createdAt': 'created_at', 'userAgent': 'user_agent'}

    def out(self, e, depth):
        return {
            'id': e.pk, 'user': ({'id': e.user_id, 'name': e.user.name, 'role': e.user.role} if depth > 0 else e.user_id) if e.user_id else None,
            'username': e.username, 'method': e.method, 'result': e.result, 'ip': e.ip, 'network': e.network or None,
            'browser': e.browser or None, 'os': e.os or None, 'device': e.device or None, 'userAgent': e.user_agent or None,
            'createdAt': dt(e.created_at), 'updatedAt': dt(e.created_at),
        }


class Activities(Collection):
    slug = 'activity'
    model = Activity
    default_sort = ['-created_at']
    access = {'read': SUPER}
    fields = {'createdAt': 'created_at', 'entityId': 'entity_id', 'userName': 'user_name'}

    def out(self, a, depth):
        return {
            'id': a.pk, 'user': a.user_id, 'userName': a.user_name, 'action': a.action, 'entity': a.entity,
            'entityId': a.entity_id or None, 'label': a.label or None, 'changes': a.changes or {}, 'ip': a.ip or None,
            'createdAt': dt(a.created_at),
        }


REGISTRY: dict[str, Collection] = {c.slug: c for c in (
    Users(), Medias(), Categories(), Posts(), Slides(), Leaders(), DocCategories(), Documents(), VideoCategories(), Videos(),
    Faculties(), Departments(), StaffProfiles(), SdgGoals(), Pages(), LoginEvents(), Activities(),
)}
