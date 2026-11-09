"""Admin panel yig'ma ma'lumotlari (/api/cms/panel/*): bosh sahifa, statistika, media, YouTube, HEMIS, BRM."""
import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.db.models import Count, F, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response

from apps.content.models import Post
from apps.core.models import Activity, Media
from apps.hemis import get_client
from apps.hemis.models import HemisSnapshot

from .auth import error
from .collections import ALL, MEDIA_ROLES, SDG, SUPER, youtube_id
from .models import LoginEvent
from .usage import media_usage, used_media_ids
from .views import PanelView

TAG = ['Admin panel: yig‘ma ma’lumot']


def role_in(request, roles) -> bool:
    u = request.user
    return bool(u and u.is_authenticated and u.status != 'disabled' and u.role in roles)


class OverviewView(PanelView):
    @extend_schema(tags=TAG, summary='Boshqaruv paneli raqamlari', responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, ALL):
            return error('Ruxsat yo‘q', 401)
        now = timezone.now()
        local = timezone.localtime(now)
        month_start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        day_start = local.replace(hour=0, minute=0, second=0, microsecond=0)
        posts = Post.objects.filter(deleted_at__isnull=True)
        pub = posts.filter(status='published', published_at__gte=month_start, published_at__lte=now)
        recent = posts.select_related('author').order_by('-updated_at')[:6]
        result = {
            'posts': {
                'month': {t: pub.filter(type=t).count() for t in ('news', 'announcements', 'events')},
                'drafts': posts.filter(status='draft').count(),
                'scheduled': posts.filter(status='published', published_at__gt=now).count(),
                'hidden': posts.filter(hidden=True).count(),
                'total': posts.count(),
            },
            'recent': [{
                'id': p.pk, 'type': p.type, 'title': p.title.get('uz') or '', 'sdg': p.sdg, 'status': p.status, 'hidden': p.hidden,
                'publishedAt': p.published_at.isoformat() if p.published_at else None,
                'author': p.author.name if p.author_id else None,
            } for p in recent],
        }
        if request.user.role == 'superadmin':
            result['logins'] = {
                'today': LoginEvent.objects.filter(result='success', created_at__gte=day_start).count(),
                'failed24h': LoginEvent.objects.exclude(result='success').filter(created_at__gte=now - timedelta(days=1)).count(),
            }
            result['activity'] = [
                {'id': a.pk, 'who': a.user_name, 'action': a.action, 'label': a.label, 'at': a.created_at.isoformat()}
                for a in Activity.objects.order_by('-created_at')[:6]
            ]
        return Response(result)


class MediaStatsView(PanelView):
    @extend_schema(tags=TAG, summary='Media: papkalar, turlar, joy va WebP tejami', responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, MEDIA_ROLES):
            return error('Ruxsat yo‘q', 401)
        folders = dict(Media.objects.values_list('folder').annotate(n=Count('id')))
        kinds = {'image': 0, 'pdf': 0, 'audio': 0} | dict(Media.objects.values_list('kind').annotate(n=Count('id')))
        used = Media.objects.aggregate(s=Sum('filesize'))['s'] or 0
        saved = Media.objects.filter(original_size__gt=F('filesize')).aggregate(s=Sum(F('original_size') - F('filesize')))['s'] or 0
        try:
            du = shutil.disk_usage(settings.MEDIA_ROOT)
            disk = {'total': du.total, 'free': du.free}
        except OSError:
            disk = None
        return Response({'total': Media.objects.count(), 'folders': folders, 'kinds': kinds, 'used': used, 'saved': saved, 'disk': disk})


class MediaUsageView(PanelView):
    @extend_schema(tags=TAG, summary='Fayl qayerda ishlatilgan', responses=OpenApiTypes.OBJECT)
    def get(self, request, pk):
        if not role_in(request, MEDIA_ROLES):
            return error('Ruxsat yo‘q', 401)
        return Response({'used': media_usage(pk)})


class MediaUsedView(PanelView):
    @extend_schema(tags=TAG, summary='Ishlatilayotgan fayllar ID’lari', responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, MEDIA_ROLES):
            return error('Ruxsat yo‘q', 401)
        return Response({'ids': sorted(used_media_ids())})


def _fetch(url: str, timeout: int = 6) -> bytes:
    req = urllib.request.Request(url, headers={'accept-language': 'en', 'user-agent': 'Mozilla/5.0 (UzSWLU admin)'})
    with urllib.request.urlopen(req, timeout=timeout) as res:  # noqa: S310 — faqat youtube.com
        return res.read()


class YoutubeView(PanelView):
    @extend_schema(tags=TAG, summary='YouTube videodan nom, muqova va davomiylik', parameters=[OpenApiParameter('url', str)], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, MEDIA_ROLES):
            return error('Ruxsat yo‘q', 401)
        vid = youtube_id(request.query_params.get('url', ''))
        if not vid:
            return error('YouTube havolasi noto‘g‘ri')
        watch = f'https://www.youtube.com/watch?v={vid}'
        out = {'id': vid, 'url': watch, 'title': None, 'author': None, 'thumbnail': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg', 'duration': None}
        try:
            data = json.loads(_fetch(f'https://www.youtube.com/oembed?url={urllib.parse.quote(watch)}&format=json'))
            out['title'], out['author'] = data.get('title'), data.get('author_name')
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 404):
                return error('Video topilmadi yoki yopiq', 404)
            return error('YouTube javob bermadi — keyinroq urinib ko‘ring', 502)
        except Exception:  # noqa: BLE001
            return error('YouTube javob bermadi — keyinroq urinib ko‘ring', 502)
        try:
            m = re.search(rb'"lengthSeconds":"(\d+)"', _fetch(watch))
            if m:
                sec = int(m.group(1))
                h, rest = divmod(sec, 3600)
                mnt, s = divmod(rest, 60)
                out['duration'] = f'{h}:{mnt:02d}:{s:02d}' if h else f'{mnt}:{s:02d}'
        except Exception:  # noqa: BLE001 — davomiylik ixtiyoriy
            pass
        return Response(out)


class HemisView(PanelView):
    @extend_schema(tags=TAG, summary='HEMIS ma’lumoti (faqat o‘qish): fakultetlar, xodimlar', responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, ALL):
            return error('Ruxsat yo‘q', 401)
        client = get_client()
        synced = client.synced_at()
        faculties = []
        for f in client.faculties():
            dean = (f.get('dean') or {}).get('uz') or {}
            faculties.append({
                'slug': f['slug'], 'name': (f.get('name') or {}).get('uz', ''), 'stats': f.get('stats') or {},
                'dean': dean.get('name', '') if isinstance(dean, dict) else '',
                'departments': [{'id': d['id'], 'name': (d.get('name') or {}).get('uz', ''), 'head': d.get('head')} for d in f.get('departments', [])],
            })
        staff = [{
            'id': s['id'], 'name': s['name'], 'patronymic': s.get('patronymic'), 'group': s.get('group'),
            'employments': [{'department': e['department'], 'position': (e.get('position') or {}).get('name', '')} for e in s.get('employments', [])],
        } for s in client.staff('uz')]
        # Sinxronlash holati: nusxa 30 soatdan eski bo'lsa (kechagi o'tmagan) — `stale`; xato matni faqat superadmin'ga (ichki manzil bo'lishi mumkin)
        snap = HemisSnapshot.objects.filter(pk=1).only('error').first()
        stale = bool(settings.HEMIS_API_URL and synced and timezone.now() - synced > timedelta(hours=30))
        last_error = (snap.error or None) if snap and role_in(request, SUPER) else None
        return Response({
            'syncedAt': synced.isoformat() if synced else None, 'stale': stale, 'lastError': last_error,
            'faculties': faculties, 'staff': staff,
            'staffDepartments': client.staff_departments('uz'),
        })


class SdgCountsView(PanelView):
    @extend_schema(tags=TAG, summary='Har bir BRM maqsadiga bog‘langan postlar soni', responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, ALL | SDG):
            return error('Ruxsat yo‘q', 401)
        rows = Post.objects.filter(deleted_at__isnull=True, sdg__gt=0).values_list('sdg').annotate(n=Count('id'))
        return Response({str(sdg): n for sdg, n in rows})


SOURCES = [
    (r'(^|\.)google\.', 'Google'), (r'(^|\.)yandex\.', 'Yandex'), (r'(^|\.)bing\.com$', 'Bing'), (r'(^|\.)t\.me$|telegram', 'Telegram'),
    (r'facebook\.com$|fb\.com$', 'Facebook'), (r'instagram\.com$', 'Instagram'), (r'youtube\.com$', 'YouTube'), (r'uzswlu\.uz$|localhost', 'Sayt ichidan'),
]
RANGES = {'1': timedelta(days=1), '7': timedelta(days=7), '30': timedelta(days=30), '365': timedelta(days=365)}


def _summary(cur, a, b) -> dict:
    cur.execute('''
        WITH ev AS (SELECT visitor, ts FROM core_hit WHERE kind = 'pageview' AND ts >= %s AND ts < %s),
        s AS (SELECT visitor, ts, CASE WHEN lag(ts) OVER w IS NULL OR ts - lag(ts) OVER w > interval '30 minutes' THEN 1 ELSE 0 END AS fresh
              FROM ev WINDOW w AS (PARTITION BY visitor ORDER BY ts)),
        v AS (SELECT visitor, ts, sum(fresh) OVER (PARTITION BY visitor ORDER BY ts) AS n FROM s),
        visits AS (SELECT count(*) AS views, extract(epoch FROM max(ts) - min(ts)) AS dur FROM v GROUP BY visitor, n)
        SELECT (SELECT count(DISTINCT visitor) FROM ev), count(*), coalesce(sum(views), 0),
               coalesce(avg(dur), 0), coalesce(avg(CASE WHEN views = 1 THEN 1 ELSE 0 END), 0) FROM visits''', [a, b])
    v, visits, pv, dur, bounce = cur.fetchone()
    return {'visitors': int(v), 'visits': int(visits), 'pageviews': int(pv), 'duration': float(dur), 'bounce': float(bounce)}


def _rows(cur, sql, params) -> list[dict]:
    cur.execute(sql, params)
    return [{'k': k, 'v': int(v)} for k, v in cur.fetchall()]


class StatsView(PanelView):
    @extend_schema(tags=TAG, summary='Sayt statistikasi (cookie’siz)', parameters=[OpenApiParameter('range', str, enum=list(RANGES))], responses=OpenApiTypes.OBJECT)
    def get(self, request):
        if not role_in(request, {'superadmin'}):
            return error('Ruxsat yo‘q', 403)
        if connection.vendor != 'postgresql':
            return error('Statistika faqat PostgreSQL bilan ishlaydi', 501)
        rng = request.query_params.get('range') if request.query_params.get('range') in RANGES else '30'
        now = timezone.now()
        frm = now - RANGES[rng]
        prev = frm - RANGES[rng]
        unit = 'hour' if rng == '1' else 'month' if rng == '365' else 'day'
        with connection.cursor() as cur:
            current, previous = _summary(cur, frm, now), _summary(cur, prev, frm)
            cur.execute(f"""SELECT date_trunc('{unit}', ts AT TIME ZONE 'Asia/Tashkent') AS t, count(*), count(DISTINCT visitor)
                            FROM core_hit WHERE kind = 'pageview' AND ts >= %s GROUP BY 1 ORDER BY 1""", [frm])
            series = [{'t': t.isoformat(), 'views': int(v), 'visitors': int(u)} for t, v, u in cur.fetchall()]
            refs = _rows(cur, "SELECT coalesce(referrer, ''), count(DISTINCT visitor) FROM core_hit WHERE kind = 'pageview' AND ts >= %s GROUP BY 1 ORDER BY 2 DESC LIMIT 50", [frm])
            countries = _rows(cur, "SELECT country, count(DISTINCT visitor) FROM core_hit WHERE kind = 'pageview' AND ts >= %s AND country <> '' GROUP BY 1 ORDER BY 2 DESC LIMIT 6", [frm])
            langs = _rows(cur, "SELECT coalesce(nullif(lang, ''), 'uz'), count(*) FROM core_hit WHERE kind = 'pageview' AND ts >= %s GROUP BY 1 ORDER BY 2 DESC", [frm])
            pages = _rows(cur, "SELECT path, count(*) FROM core_hit WHERE kind = 'pageview' AND ts >= %s AND path <> '' GROUP BY 1 ORDER BY 2 DESC LIMIT 8", [frm])
            searches = _rows(cur, "SELECT lower(value), count(*) FROM core_hit WHERE kind = 'search' AND ts >= %s AND value <> '' GROUP BY 1 ORDER BY 2 DESC LIMIT 8", [frm])
            events = _rows(cur, "SELECT name, count(*) FROM core_hit WHERE kind = 'event' AND ts >= %s GROUP BY 1 ORDER BY 2 DESC LIMIT 8", [frm])
        grouped: dict[str, int] = {}
        for r in refs:
            name = 'To‘g‘ridan-to‘g‘ri' if not r['k'] else next((n for pat, n in SOURCES if re.search(pat, r['k'])), r['k'])
            grouped[name] = grouped.get(name, 0) + r['v']
        top = sorted(grouped.items(), key=lambda x: -x[1])
        rest = sum(v for _, v in top[5:])
        sources = [{'k': k, 'v': v} for k, v in top[:5]] + ([{'k': 'Boshqa', 'v': rest}] if rest else [])
        return Response({
            'range': rng, 'from': frm.isoformat(), 'current': current, 'previous': previous, 'unit': unit, 'series': series,
            'sources': sources, 'countries': countries, 'langs': langs, 'pages': pages, 'searches': searches, 'events': events,
        })
