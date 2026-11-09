"""Kesh va bosim: cache-busting, kesh to'qnashuvi, token bilan himoyalangan javob keshi, statistika/yuklab olish suiiste'moli."""
import re
from pathlib import Path

from django.core.cache import cache
from django.test import Client, override_settings

from apps.api.common import CACHE_PARAMS, _cache_key
from apps.content.models import Post
from tests.support import HOST, Base, SeededTestCase

API_DIR = Path(__file__).resolve().parents[2] / 'apps' / 'api'


class CacheKeyTests(Base):
    def key(self, path, qs):
        from django.test import RequestFactory
        return _cache_key(RequestFactory().get(f'{path}?{qs}'), 'x')

    def test_unknown_params_do_not_create_new_cache_entries(self):
        base = self.key('/api/posts', 'page=2&lang=ru')
        for junk in ('x=1', 'x=2&y=3', '_=1699999999', 'utm_source=abc', 'cb=' + 'a' * 500):
            self.assertEqual(self.key('/api/posts', f'page=2&lang=ru&{junk}'), base, junk)

    def test_param_order_does_not_matter_but_values_do(self):
        self.assertEqual(self.key('/api/posts', 'lang=uz&page=1'), self.key('/api/posts', 'page=1&lang=uz'))
        for a, b in (('page=1', 'page=2'), ('lang=uz', 'lang=ru'), ('q=abc', 'q=abd'), ('type=news', 'type=events')):
            self.assertNotEqual(self.key('/api/posts', a), self.key('/api/posts', b))

    def test_long_keys_do_not_collide(self):
        a = self.key('/api/search', 'q=' + 'a' * 150 + 'X')
        b = self.key('/api/search', 'q=' + 'a' * 150 + 'Y')
        self.assertNotEqual(a, b)
        self.assertLessEqual(len(a), 240)

    def test_every_query_param_read_by_api_is_part_of_cache_key(self):
        """Yangi parametr qo'shilib, kesh kalitiga unutilsa — turli natijalar bir xil keshdan qaytib ketardi (jiddiy xato)."""
        used = set()
        for f in API_DIR.glob('*.py'):
            src = f.read_text(encoding='utf-8')
            used |= set(re.findall(r"""(?:\bp|\bparams|query_params)(?:\.get|\.getlist)?[\(\[]\s*['"]([A-Za-z_]+)['"]""", src))
        used -= {'id', 'name', 'employments'}   # bular so'rov parametri emas (lug'at kalitlari)
        self.assertLessEqual(used, set(CACHE_PARAMS), f'kesh kalitida yo‘q parametrlar: {sorted(used - set(CACHE_PARAMS))}')

    def test_cached_responses_differ_by_param_values(self):
        for i in range(3):
            Post.objects.create(type='news', slug=f'n{i}', title={'uz': f'N{i}'}, status='published')
        c = Client(**HOST)
        one = c.get('/api/posts?perPage=1&page=1').json()
        two = c.get('/api/posts?perPage=1&page=2&cb=zzz').json()
        self.assertNotEqual(one, two)
        self.assertEqual(c.get('/api/posts?perPage=1&page=2&cb=other').json(), two)   # begona parametr — bir xil yozuv


class CachePrivacyTests(Base):
    @override_settings(API_TOKEN='tok-abcdefghijklmnop')
    def test_token_gated_responses_are_not_public_cacheable_and_not_served_without_token(self):
        c = Client(**HOST)
        ok = c.get('/api/posts', HTTP_AUTHORIZATION='Bearer tok-abcdefghijklmnop')
        self.assertEqual(ok.status_code, 200)
        self.assertIn('private', ok['Cache-Control'])
        self.assertIn('Authorization', ok['Vary'])
        for headers in ({}, {'HTTP_AUTHORIZATION': 'Bearer nope'}, {'HTTP_AUTHORIZATION': 'Bearer '}):
            self.assertIn(c.get('/api/posts', **headers).status_code, (401, 403), 'kesh tokensiz mijozga berib yubordi')

    @override_settings(API_TOKEN='')
    def test_open_site_endpoints_stay_public(self):
        res = Client(**HOST).get('/api/site/posts')
        self.assertEqual(res.status_code, 200)
        self.assertIn('public', res['Cache-Control'])

    def test_get_on_post_only_endpoint_is_405_not_500(self):
        for url in ('/api/appeals', '/api/hit'):
            self.assertEqual(Client(**HOST).get(url).status_code, 405, url)


class AbuseTests(Base):
    def setUp(self):
        super().setUp()
        cache.clear()

    def test_document_downloads_counted_once_per_ip_per_hour(self):
        from apps.content.models import DocCategory, Document
        from apps.core.models import Media
        cat = DocCategory.objects.create(title={'uz': 'C'})
        m = Media.objects.create(file='x.pdf', kind='pdf', folder='docs')
        d = Document.objects.create(title={'uz': 'D'}, category=cat, file_uz=m)
        c = Client(**HOST)
        for _ in range(25):
            self.assertEqual(c.get(f'/api/documents/{d.pk}/file').status_code, 302)
        d.refresh_from_db()
        self.assertEqual(d.downloads, 1, 'bitta IP yuklab olishlar sonini sun’iy oshirdi')
        c2 = Client(**HOST, REMOTE_ADDR='203.0.113.9')
        c2.get(f'/api/documents/{d.pk}/file')
        d.refresh_from_db()
        self.assertEqual(d.downloads, 2)

    def test_identical_hits_are_deduplicated(self):
        from apps.core.models import Hit
        c = Client(**HOST, HTTP_USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) Firefox/120')
        body = '{"kind":"pageview","path":"/uz/news","lang":"uz"}'
        for _ in range(30):
            self.assertEqual(c.post('/api/hit', data=body, content_type='text/plain').status_code, 204)
        self.assertEqual(Hit.objects.count(), 1)
        c.post('/api/hit', data='{"kind":"pageview","path":"/uz/other","lang":"uz"}', content_type='text/plain')
        self.assertEqual(Hit.objects.count(), 2)

    def test_hit_retention_prunes_in_batches(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.core import nightly
        from apps.core.models import Hit
        old = [Hit.objects.create(visitor='v', kind='pageview', path=f'/{i}') for i in range(12)]
        Hit.objects.filter(pk__in=[h.pk for h in old]).update(ts=timezone.now() - timedelta(days=900))
        fresh = Hit.objects.create(visitor='v', kind='pageview', path='/fresh')
        with override_settings(HIT_RETENTION_DAYS=730):
            nightly.prune_hits()
        self.assertEqual(list(Hit.objects.values_list('pk', flat=True)), [fresh.pk])
        with override_settings(HIT_RETENTION_DAYS=0):
            Hit.objects.filter(pk=fresh.pk).update(ts=timezone.now() - timedelta(days=5000))
            nightly.prune_hits()
        self.assertTrue(Hit.objects.filter(pk=fresh.pk).exists())


class QueryCostTests(SeededTestCase):
    """So'rov xarajati: sahifa kattalashganda bazaga so'rovlar soni oshmasligi kerak (N+1 yo'q) — serverga bosim."""

    SLACK = 3

    def count(self, fn):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            res = fn()
        return len(ctx), res

    def test_panel_lists_do_not_have_n_plus_one(self):
        from apps.panel.collections import REGISTRY
        from tests.support import api, jwt_for, loose
        from apps.accounts.models import User
        from tests.support import PASSWORD
        User.objects.create_user('qc_root', password=PASSWORD, role='superadmin', name='QC')
        with loose():
            h = jwt_for('qc_root')
        worst = []
        for slug, coll in REGISTRY.items():
            if 'read' not in coll.access:
                continue
            small, r1 = self.count(lambda: api('get', f'/api/cms/{slug}?limit=2&depth=2', h))
            big, r2 = self.count(lambda: api('get', f'/api/cms/{slug}?limit=60&depth=2', h))
            self.assertEqual(r2.status_code, 200, slug)
            if r2.json().get('totalDocs', 0) > 4 and big > small + self.SLACK:
                worst.append((slug, small, big))
        self.assertEqual(worst, [], f'N+1 (kolleksiya, 2 ta yozuv, 60 ta yozuv so‘rovlari soni): {worst}')

    def test_public_endpoints_are_bounded(self):
        c = Client(**HOST)
        slow = []
        for url in ('/api/home', '/api/posts?perPage=48', '/api/staff?perPage=48', '/api/faculties', '/api/documents', '/api/leadership',
                    '/api/search?q=universitet', '/api/site/latest', '/api/site/menu', '/api/sdg', '/api/videos', '/api/programs'):
            cache.clear()
            n, res = self.count(lambda: c.get(url))
            self.assertEqual(res.status_code, 200, url)
            if n > 25:
                slow.append((url, n))
        self.assertEqual(slow, [], f'bitta ochiq so‘rovga 25 dan ko‘p SQL: {slow}')


class PanelPressureTests(Base):
    """Admin panelga og'ir so'rovlar bilan bosim: murakkab filtrlar rad etiladi, ulkan ro'yxat kesiladi."""

    def setUp(self):
        super().setUp()
        from tests.support import jwt_for, loose
        with loose():
            self.h = jwt_for('root')

    def test_complex_filters_are_rejected_not_executed(self):
        from tests.support import api
        many = '&'.join(f'where[and][{i}][title.uz][like]=a' for i in range(60))
        deep = 'where' + ''.join(f'[and][0]' for _ in range(8)) + '[title.uz][like]=a'
        for name, qs in (('60 shart', many), ('juda chuqur', deep)):
            self.assertEqual(api('get', f'/api/cms/posts?{qs}', self.h).status_code, 400, name)

    def test_huge_in_list_and_limit_are_clamped(self):
        from tests.support import api
        ids = ','.join(str(i) for i in range(50000))
        self.assertIn(api('get', f'/api/cms/posts?where[id][in]={ids}', self.h).status_code, (200, 400, 414))
        res = api('get', '/api/cms/posts?limit=99999999', self.h)
        self.assertEqual(res.status_code, 200)
        from django.conf import settings
        self.assertLessEqual(res.json()['limit'], settings.ADMIN_MAX_LIMIT)
