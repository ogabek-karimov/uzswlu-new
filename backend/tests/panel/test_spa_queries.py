"""Admin SPA yuboradigan murakkab so'rovlar (`where[and][0][...]`, `like`, `not_in`, `exists`, `trash` ...):
barchasi 200 va to'g'ri shaklda javob berishi kerak. Ro'yxat `admin/src/pages/*` dagi haqiqiy so'rovlardan olingan."""
from urllib.parse import quote

from tests.support import SeededTestCase

NOW = '2026-11-06T00:00:00.000Z'


def qs(params, prefix=''):
    """admin/src/lib/api.ts dagi `qs` bilan bir xil kodlash."""
    parts = []
    for k, v in params.items():
        if v is None or v == '':
            continue
        name = f'{prefix}[{k}]' if prefix else k
        if isinstance(v, dict):
            parts.append(qs(v, name))
        elif isinstance(v, list):
            for i, x in enumerate(v):
                parts.append(qs(x, f'{name}[{i}]') if isinstance(x, dict) else f'{quote(f"{name}[{i}]")}={quote(str(x))}')
        else:
            parts.append(f'{quote(name)}={quote(str(v))}')
    return '&'.join(p for p in parts if p)


class SpaQueryTests(SeededTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.superadmin)

    def ok(self, path, expect=None, **params):
        r = self.client.get(f'{path}?{qs(params)}')
        self.assertEqual(r.status_code, 200, f'{path} {params}: {r.content[:200]!r}')
        data = r.json()
        if expect:
            self.assertTrue(expect(data), f'{path}: kutilgan shakl yo‘q: {list(data)[:8]}')
        return data

    def test_posts_filters_for_every_type(self):
        for t in ('news', 'announcements', 'events'):
            base = {'type': {'equals': t}}
            published = {'status': {'equals': 'published'}}
            cases = {
                'barchasi': ({'and': [base]}, {}),
                'e’lon qilingan': ({'and': [base, published, {'publishedAt': {'less_than_equal': NOW}}]}, {'page': 2, 'limit': 5}),
                'rejalashtirilgan': ({'and': [base, published, {'publishedAt': {'greater_than': NOW}}]}, {'limit': 5}),
                'qoralama': ({'and': [base, {'status': {'equals': 'draft'}}]}, {}),
                'yashirin': ({'and': [base, {'hidden': {'equals': True}}]}, {}),
                'sdg=0': ({'and': [base, {'sdg': {'equals': 0}}]}, {}),
                'sdg=6': ({'and': [base, {'sdg': {'equals': 6}}]}, {}),
                'qidiruv': ({'and': [base, {'or': [{f'title.{lg}': {'like': 'a'}} for lg in ('uz', 'ru', 'en', 'zh')]}]}, {'limit': 5}),
            }
            for label, (where, extra) in cases.items():
                with self.subTest(type=t, case=label):
                    self.ok('/api/cms/posts', where=where, sort='-publishedAt', **{'limit': 20, 'page': 1, 'depth': 1, **extra})
            with self.subTest(type=t, case='chiqindi'):
                self.ok('/api/cms/posts', where={'and': [base, {'deletedAt': {'exists': True}}]}, sort='-publishedAt', limit=20, page=1, trash='true')
            with self.subTest(type=t, case='count'):
                self.ok('/api/cms/posts/count', lambda d: 'totalDocs' in d, where=base)

    def test_media_queries(self):
        self.ok('/api/cms/media', where={'and': [{'mimeType': {'like': 'image/'}}]}, sort='-createdAt', limit=40, page=1, depth=1)
        self.ok('/api/cms/media', where={'and': [{'or': [{'filename': {'like': 'a'}}, {'alt.uz': {'like': 'a'}}]}]}, sort='-filesize', limit=40, page=1, depth=1)
        self.ok('/api/cms/media', where={'and': [{'folder': {'equals': 'posts'}}]}, sort='-createdAt', limit=40, page=1)
        self.ok('/api/cms/media', where={'and': [{'id': {'not_in': [1, 2, 3]}}]}, sort='-createdAt', limit=40, page=1)
        self.ok('/api/cms/panel/media-used', lambda d: 'ids' in d)

    def test_activity_and_login_events(self):
        self.ok('/api/cms/activity', sort='-createdAt', limit=40, page=1)
        self.ok('/api/cms/activity', where={'action': {'equals': 'create'}}, sort='-createdAt', limit=40, page=1)
        self.ok('/api/cms/login-events', where={'and': [{'result': {'not_equals': 'success'}}]}, sort='-createdAt', limit=30, page=1, depth=1)
        self.ok('/api/cms/login-events', where={'and': [{'or': [{'username': {'like': 'a'}}, {'ip': {'like': 'a'}}]}]}, sort='-createdAt', limit=30, page=1, depth=1)
        self.ok('/api/cms/login-events/count', lambda d: 'totalDocs' in d,
                where={'and': [{'result': {'equals': 'success'}}, {'createdAt': {'greater_than_equal': NOW}}]})

    def test_lists_used_by_selectors(self):
        self.ok('/api/cms/users', limit=200, sort='name', depth=0)
        self.ok('/api/cms/staff-profiles', limit=5000, depth=0)
        self.ok('/api/cms/documents', sort='order', limit=1000, depth=1)
        self.ok('/api/cms/posts/versions', where={'parent': {'equals': 1}}, sort='-createdAt', limit=10)
