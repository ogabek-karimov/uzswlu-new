"""Soʻrov xavfsizligi: `where`/`sort` orqali yashirin maydonlarni tekshirib bo‘lmaydi."""

from django.test import override_settings
from tests.support import Base, api, jwt_for


class QueryInjectionTests(Base):
    """`where`/`sort` orqali parol xeshi kabi yashirin maydonlarni tekshirib bo'lmaydi."""

    def test_password_filter_rejected(self):
        h = jwt_for('root')
        for url in ('/api/cms/users?where[password][like]=pbkdf2',
                    '/api/cms/media?where[uploadedBy.password][like]=pbkdf2',
                    '/api/cms/users?where[lastLogin][exists]=true',
                    '/api/cms/posts?where[author.password][contains]=a'):
            self.assertEqual(api('get', url, h).status_code, 400, url)

    def test_relation_traversal_rejected(self):
        h = jwt_for('root')
        self.assertEqual(api('get', '/api/cms/departments?where[image.file][like]=a', h).status_code, 400)

    def test_sort_by_secret_is_ignored(self):
        h = jwt_for('root')
        res = api('get', '/api/cms/users?sort=password', h)
        self.assertEqual(res.status_code, 200)

    def test_normal_filters_still_work(self):
        h = jwt_for('root')
        res = api('get', '/api/cms/faculties?where[name.uz][like]=B fak&sort=-id', h)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['totalDocs'], 1)

    def test_too_complex_filter_rejected(self):
        h = jwt_for('root')
        q = '&'.join(f'where[and][{i}][id][equals]={i}' for i in range(60))
        self.assertEqual(api('get', f'/api/cms/faculties?{q}', h).status_code, 400)

    def test_limit_is_capped(self):
        h = jwt_for('root')
        with override_settings(ADMIN_MAX_LIMIT=1):
            self.assertEqual(len(api('get', '/api/cms/faculties?limit=100', h).json()['docs']), 1)
            self.assertEqual(len(api('get', '/api/cms/faculties?limit=0', h).json()['docs']), 1)
