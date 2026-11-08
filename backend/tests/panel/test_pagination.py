"""Sahifalash: har bir kolleksiyada barcha sahifalarni aylanib chiqqanda yozuvlar yo'qolmaydi va takrorlanmaydi;
noto'g'ri `limit`/`page` qiymatlari xato bermaydi. Ochiq API va admin API uchun."""
from django.test import tag

from apps.panel.collections import REGISTRY
from tests.support import SeededTestCase


@tag('slow')
class PanelPaginationTests(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.superadmin)

    def walk(self, slug, limit, extra=''):
        seen, page, total = [], 1, 0
        for _ in range(500):
            r = self.client.get(f'/api/cms/{slug}?limit={limit}&page={page}{extra}')
            if r.status_code != 200:
                return None
            d = r.json()
            total = d['totalDocs']
            seen += [x['id'] for x in d['docs']]
            if not d['hasNextPage']:
                return seen, total
            page = d['nextPage']
        self.fail(f'{slug}: sahifalash cheksiz aylanyapti')

    def test_every_collection_pages_are_complete_and_unique(self):
        for slug in REGISTRY:
            for limit in (2, 7):
                for sort in ('', '&sort=-createdAt'):
                    with self.subTest(collection=slug, limit=limit, sort=sort or 'default'):
                        res = self.walk(slug, limit, sort)
                        if res is None:
                            self.assertNotEqual(sort, '', f'{slug}: standart tartibda ro‘yxat ochilmadi')
                            continue
                        seen, total = res
                        self.assertEqual(len(seen), total)
                        self.assertEqual(len(set(seen)), len(seen), 'takroriy yozuv')

    def test_bad_limit_and_page_values_are_clamped(self):
        for q in ('limit=0', 'limit=abc&page=xyz', 'page=-5', 'limit=3&page=0', 'limit=100000', 'pagination=false'):
            with self.subTest(query=q):
                r = self.client.get('/api/cms/posts?' + q)
                self.assertEqual(r.status_code, 200)
                d = r.json()
                self.assertGreaterEqual(d['page'], 1)
                if not q.startswith(('limit=0', 'pagination')):
                    self.assertLessEqual(len(d['docs']), max(d['limit'], 1))


@tag('slow')
class PublicPaginationTests(SeededTestCase):
    def walk(self, url, per, key='items'):
        seen, page = [], 1
        while page < 200:
            d = self.client.get(f'{url}&perPage={per}&page={page}').json()
            if not d[key]:
                break
            seen += [x.get('slug') or x.get('id') or x.get('url') or x.get('title') for x in d[key]]
            if page * per >= d['total']:
                break
            page += 1
        return seen, d['total']

    def test_public_lists_walk_without_duplicates(self):
        for url in ('/api/posts?type=news', '/api/posts?type=announcements', '/api/posts?type=events',
                    '/api/staff?x=1', '/api/search?q=universitet'):
            for per in (1, 5, 24):
                with self.subTest(url=url, per=per):
                    seen, total = self.walk(url, per)
                    self.assertEqual(len(seen), total)
                    self.assertEqual(len(set(seen)), len(seen))

    def test_public_bad_values_are_clamped(self):
        for q in ('page=0', 'page=-1', 'page=abc', 'perPage=0', 'perPage=1000', 'perPage=abc'):
            with self.subTest(query=q):
                r = self.client.get('/api/posts?type=news&' + q)
                self.assertEqual(r.status_code, 200)
                d = r.json()
                self.assertGreaterEqual(d['page'], 1)
                self.assertTrue(1 <= d['perPage'] <= 48)

    def test_post_detail_has_translations_and_docs_pages_open(self):
        slug = self.client.get('/api/posts?type=news&lang=uz').json()['items'][0]['slug']
        p = self.client.get(f'/api/posts/news/{slug}?lang=uz').json()
        self.assertTrue(p['translations'] and p['translations'][0]['lang'] == 'uz')
        for u in ('/api/docs/', '/api/schema/', '/api/redoc/'):
            self.assertEqual(self.client.get(u).status_code, 200, u)
