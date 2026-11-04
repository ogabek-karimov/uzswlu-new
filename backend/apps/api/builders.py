"""Model → API shakli (frontend/docs/openapi.yaml). Hamma matnli maydon so'ralgan tilda, bo'lmasa o'zbekcha."""
from django.utils import timezone

from apps.content.models import Post
from apps.core.fields import pick, tr
from apps.core.html import text_of
from apps.core.utils import local_date

from .common import attachments_out, img, iso, lines

POST_RELATED = ('category', 'cover', 'cover_ru', 'cover_en', 'cover_zh')


def cover_for(post: Post, lang: str, size: str = 'card'):
    own = getattr(post, f'cover_{lang}', None) if lang != 'uz' else None
    return img(own or post.cover, size)


def post_summary(p: Post, lang: str) -> dict:
    when = p.starts_at if p.type == 'events' and p.starts_at else p.published_at
    return {
        'id': str(p.pk),
        'slug': p.slug,
        'type': p.type,
        'title': tr(p.title, lang),
        'category': tr(p.category.name, lang) if p.category else '',
        'date': local_date(when),
        'image': cover_for(p, lang),
        'excerpt': pick(p.excerpt, lang),
    }


def news_item(p: Post, lang: str) -> dict:
    s = post_summary(p, lang)
    return {k: s[k] for k in ('id', 'slug', 'title', 'category', 'date', 'image')}


def announcement_item(p: Post, lang: str) -> dict:
    return {'id': str(p.pk), 'slug': p.slug, 'title': tr(p.title, lang), 'date': local_date(p.published_at)}


def event_item(p: Post, lang: str) -> dict:
    return {
        'id': str(p.pk),
        'slug': p.slug,
        'title': tr(p.title, lang),
        'category': tr(p.category.name, lang) if p.category else '',
        'startsAt': iso(p.starts_at or p.published_at),
        'endsAt': iso(p.ends_at),
        'location': tr(p.location, lang),
        'image': cover_for(p, lang),
    }


def upcoming_events(lang: str, limit: int = 3):
    return list(Post.visible(lang).filter(type='events', starts_at__gte=timezone.now()).select_related(*POST_RELATED).order_by('starts_at')[:limit])


def latest_posts(lang: str, type_: str, limit: int, exclude_pk=None):
    qs = Post.visible(lang).filter(type=type_).select_related(*POST_RELATED).order_by('-published_at')
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return list(qs[:limit])


def reading_minutes(body_html: str, lang: str) -> int:
    plain = text_of(body_html)
    amount = len(plain) / 400 if lang == 'zh' else len(plain.split()) / 180
    return max(1, round(amount))


def post_detail(p: Post, lang: str) -> dict:
    body = tr(p.body, lang)
    author = None
    if p.author_id:
        a = p.author
        author = {'name': a.name or a.username, 'role': a.position or None, 'avatar': img(a.avatar, 'thumb') if a.avatar_id else None}
    is_event = p.type == 'events'
    return {
        **post_summary(p, lang),
        'image': cover_for(p, lang, 'hero'),
        'body': body,
        'author': author,
        'publishedAt': iso(p.published_at),
        'gallery': [x for x in (img(g.image, 'hero') for g in p.gallery.select_related('image')) if x],
        'attachments': attachments_out(p.attachments.select_related('file'), lang),
        'tags': lines(p.tags, lang),
        'readingMinutes': reading_minutes(body, lang),
        'startsAt': iso(p.starts_at) if is_event else None,
        'endsAt': iso(p.ends_at) if is_event else None,
        'location': pick(p.location, lang),
        'related': [post_summary(x, lang) for x in latest_posts(lang, p.type, 3, p.pk)],
        'latest': [post_summary(x, lang) for x in latest_posts(lang, 'news', 4, p.pk)],
    }
