"""Admin panel API (`/api/cms/*`): har bir kolleksiya uchun o'qish → o'zini PATCH → nusxa yaratish → o'chirish aylanishi,
globallar, versiyalar, ommaviy tahrir va sessiya hayoti. Admin SPA aynan shu so'rovlarni yuboradi."""
import json

from django.db import connection
from django.test import tag

from apps.panel.collections import REGISTRY
from tests.support import SeededTestCase

ORIGIN = {'HTTP_ORIGIN': 'http://127.0.0.1:5173'}
SKIP_COPY = {'users', 'media'}                     # ularni nusxalab bo'lmaydi (parol, fayl)
READ_ONLY = {'activity', 'login-events'}           # faqat o'qiladi
DROP = ('id', 'createdAt', 'updatedAt')
UNIQUE = ('slug', 'hemisId', 'n', 'key', 'email', 'username')


class PanelBase(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.client.defaults.update(ORIGIN)
        self.client.force_login(self.superadmin)

    def j(self, resp):
        return json.loads(resp.content) if resp.content else None

    def send(self, method, url, body=None):
        kw = {'data': json.dumps(body), 'content_type': 'application/json'} if body is not None else {}
        return getattr(self.client, method)(url, **kw)


@tag('slow')
class CollectionRoundTripTests(PanelBase):
    def test_every_collection_list_detail_patch_copy_delete(self):
        for slug in REGISTRY:
            if slug in READ_ONLY:
                continue
            with self.subTest(collection=slug):
                r = self.client.get(f'/api/cms/{slug}?limit=2&depth=1')
                self.assertEqual(r.status_code, 200, r.content[:200])
                docs = self.j(r)['docs']
                if not docs:
                    continue
                doc = docs[0]
                self.assertEqual(self.client.get(f"/api/cms/{slug}/{doc['id']}?depth=1").status_code, 200)

                body = {k: v for k, v in doc.items() if k not in DROP}
                r = self.send('patch', f"/api/cms/{slug}/{doc['id']}", body)
                self.assertEqual(r.status_code, 200, r.content[:300])
                if slug in SKIP_COPY:
                    continue

                copy = {k: v for k, v in doc.items() if k not in DROP + UNIQUE}
                r = self.send('post', f'/api/cms/{slug}', copy)
                self.assertIn(r.status_code, (200, 201, 400, 403, 422), r.content[:300])   # biznes qoidalari rad etishi mumkin
                if r.status_code in (200, 201):
                    created = self.j(r)['doc']['id']
                    self.assertEqual(self.client.delete(f'/api/cms/{slug}/{created}').status_code, 200)

    def test_stats_needs_postgres(self):
        r = self.client.get('/api/cms/panel/stats')
        # Statistika SQL (date_trunc) bilan hisoblanadi: PostgreSQL'da 200, SQLite'da ochiq aytilgan 501
        self.assertEqual(r.status_code, 200 if connection.vendor == 'postgresql' else 501, r.content[:150])

    def test_read_only_collections_reject_writes(self):
        for slug in READ_ONLY:
            with self.subTest(collection=slug):
                self.assertEqual(self.client.get(f'/api/cms/{slug}?limit=2').status_code, 200)
                self.assertIn(self.send('post', f'/api/cms/{slug}', {'x': 1}).status_code, (400, 403, 404, 405))

    def test_utility_endpoints(self):
        paths = ['/panel/overview', '/panel/media-stats', '/panel/media-used', '/panel/sdg-counts',
                 '/panel/media-usage/1', '/globals/settings', '/globals/symbols', '/globals/sdg-page', '/globals/video-page',
                 '/globals/settings/versions?limit=5', '/posts/versions?limit=5', '/posts/count', '/login-events/count', '/categories']
        for p in paths:
            with self.subTest(path=p):
                r = self.client.get('/api/cms' + p)
                self.assertIn(r.status_code, (200, 404), f'{p}: {r.content[:150]!r}')


class GlobalsAndVersionsTests(PanelBase):
    def test_globals_roundtrip(self):
        for g in ('settings', 'symbols', 'sdg-page', 'video-page'):
            with self.subTest(glob=g):
                r = self.client.get(f'/api/cms/globals/{g}')
                if r.status_code != 200:
                    continue
                r = self.send('post', f'/api/cms/globals/{g}', self.j(r))
                self.assertEqual(r.status_code, 200, r.content[:200])

    def test_global_version_restore(self):
        self.send('post', '/api/cms/globals/settings', self.j(self.client.get('/api/cms/globals/settings')))
        versions = self.j(self.client.get('/api/cms/globals/settings/versions?limit=5'))['docs']
        if versions:
            self.assertEqual(self.client.post(f'/api/cms/globals/settings/versions/{versions[0]["id"]}').status_code, 200)

    def test_post_versions_are_created_and_restorable(self):
        pid = self.j(self.client.get('/api/cms/posts?limit=1'))['docs'][0]['id']
        self.send('patch', f'/api/cms/posts/{pid}', {'title': {'uz': 'Yangi sarlavha'}})
        r = self.client.get(f'/api/cms/posts/versions?where[parent][equals]={pid}&sort=-createdAt&limit=10')
        versions = self.j(r)['docs']
        self.assertGreaterEqual(len(versions), 1)
        self.assertEqual(self.client.post(f'/api/cms/posts/versions/{versions[0]["id"]}').status_code, 200)

    def test_bulk_patch(self):
        pid = self.j(self.client.get('/api/cms/posts?limit=1'))['docs'][0]['id']
        r = self.send('patch', f'/api/cms/posts?where[id][in][0]={pid}', {'hidden': False})
        self.assertEqual(r.status_code, 200, r.content[:200])


class SessionLifecycleTests(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.client.defaults.update(ORIGIN)

    def login(self, **over):
        body = {'username': 'superadmin', 'password': 'Str0ng!Pass#2026-test', **over}
        return self.client.post('/api/cms/users/login', json.dumps(body), content_type='application/json')

    def test_unauthenticated_and_bad_login(self):
        me = self.client.get('/api/cms/users/me')
        self.assertEqual((me.status_code, me.json().get('user')), (200, None))        # kirmagan: user=null
        self.assertIn(self.login(password='wrong').status_code, (400, 401))
        self.assertIn(self.client.get('/api/cms/posts').status_code, (401, 403))

    def test_login_me_logout(self):
        r = self.login()
        self.assertEqual(r.status_code, 200, r.content[:200])
        me = self.client.get('/api/cms/users/me')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['user']['username'] if 'user' in me.json() else me.json()['username'], 'superadmin')
        self.assertEqual(self.client.post('/api/cms/users/logout').status_code, 200)
        self.assertIn(self.client.get('/api/cms/posts').status_code, (401, 403))
