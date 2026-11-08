"""JWT va rollar: soxta/muddati o'tgan token, rol cheklovlari, yopilgan hisob, Swagger ruxsati."""
import importlib
import json

from django.test import Client, override_settings
from django.urls import clear_url_caches

from apps.accounts.models import User
from apps.panel import jwt
from tests.support import HOST, PASSWORD, Base, api, jwt_for


class JwtTests(Base):
    def login(self, username='root', password=PASSWORD):
        return Client(**HOST).post('/api/cms/users/login', json.dumps({'username': username, 'password': password}),
                                   content_type='application/json')

    def test_login_returns_three_part_token_that_works_without_cookie_or_origin(self):
        res = self.login()
        self.assertEqual(res.status_code, 200)
        token = res.json()['token']
        self.assertEqual(token.count('.'), 2)
        h = {'HTTP_AUTHORIZATION': f'Bearer {token}', **HOST}
        fresh = Client(**HOST)   # sessiyasiz mijoz — faqat JWT
        self.assertIn(fresh.get('/api/cms/faculties?limit=1').status_code, (401, 403))
        self.assertEqual(fresh.get('/api/cms/faculties?limit=1', **h).status_code, 200)
        self.assertEqual(fresh.get('/api/cms/users/me', **h).json()['user']['role'], 'superadmin')
        # yozish ham Origin va cookie siz, faqat JWT bilan
        r = api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'name': {'uz': 'A fakultet'}})
        self.assertEqual(r.status_code, 200, r.content)

    def test_tampered_none_alg_and_garbage_tokens_rejected(self):
        token = self.login().json()['token']
        tampered = token[:-3] + ('AAA' if not token.endswith('AAA') else 'BBB')
        none_alg = 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0.'
        for label, bad in (('imzo buzilgan', tampered), ('tasodifiy', 'a.b.c'), ('alg none', none_alg), ('JWT emas', 'notajwt')):
            res = Client(**HOST).get('/api/cms/faculties?limit=1', HTTP_AUTHORIZATION=f'Bearer {bad}')
            self.assertIn(res.status_code, (401, 403), label)

    def test_expired_token_rejected(self):
        old, _ = jwt.issue(self.admin, ttl=-10)
        self.assertEqual(Client(**HOST).get('/api/cms/faculties?limit=1', HTTP_AUTHORIZATION=f'Bearer {old}').status_code, 401)

    def test_disabled_account_token_dies(self):
        h = jwt_for('ed')
        self.assertEqual(api('get', '/api/cms/faculties?limit=1', h).status_code, 200)
        User.objects.filter(pk=self.editor.pk).update(status='disabled')
        self.assertEqual(api('get', '/api/cms/faculties?limit=1', h).status_code, 401)

    def test_api_token_and_jwt_never_mix(self):
        h = jwt_for('root')
        with override_settings(API_TOKEN='secret-token'):
            self.assertIn(Client(**HOST).get('/api/home', **h).status_code, (401, 403))                       # JWT — ochiq API tokeni emas
            self.assertEqual(Client(**HOST).get('/api/home', HTTP_AUTHORIZATION='Bearer secret-token').status_code, 200)
            self.assertIn(Client(**HOST).get('/api/cms/faculties?limit=1', HTTP_AUTHORIZATION='Bearer secret-token').status_code, (401, 403))  # API tokeni — panel uchun emas


class EditorRoleLimitsTests(Base):
    def test_editor_reads_content_but_cannot_manage_users_slides_or_logs(self):
        h = jwt_for('ed')
        self.assertEqual(api('get', '/api/cms/faculties?limit=1', h).status_code, 200)
        self.assertEqual(api('post', '/api/cms/users', h, {'name': 'X', 'username': 'x1', 'password': 'Pass-12345-xx', 'role': 'editor'}).status_code, 403)
        self.assertEqual(api('post', '/api/cms/slides', h, {}).status_code, 403)
        self.assertEqual(api('get', '/api/cms/login-events?limit=1', h).status_code, 403)


class DocsAccessTests(Base):
    """Swagger: ishlab chiqishda ochiq; productionda (API_DOCS_PUBLIC=false) faqat panelga kirganlarga."""

    def reload_urls(self):
        import config.urls
        importlib.reload(config.urls)
        clear_url_caches()

    def test_docs_closed_in_production_open_with_login(self):
        h = jwt_for('root')
        self.addCleanup(self.reload_urls)
        with override_settings(API_DOCS_PUBLIC=False):
            self.reload_urls()
            self.assertIn(Client(**HOST).get('/api/docs/').status_code, (401, 403))
            self.assertEqual(Client(**HOST).get('/api/schema/', **h).status_code, 200)
            self.assertEqual(Client(**HOST).get('/api/docs/', **h).status_code, 200)
        self.reload_urls()
        self.assertEqual(Client(**HOST).get('/api/docs/').status_code, 200)

    def test_django_admin_is_gone_and_root_redirects_to_docs(self):
        self.assertEqual(Client(**HOST).get('/admin/').status_code, 404)
        r = Client(**HOST).get('/')
        self.assertEqual((r.status_code, r['Location']), (302, '/api/docs/'))
