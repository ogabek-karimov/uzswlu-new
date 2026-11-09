"""Chiqishdan oldingi audit topilmalari: har biri uchun regressiya testi (hujum so'rovi → xavfsiz javob)."""
import io
import json
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ParseError

from apps.accounts.models import User
from apps.content.models import Slide
from apps.core.parsers import clean, clean_querydict
from apps.structure.models import Appeal
from tests.support import HOST, PASSWORD, Base, api, jwt_for, loose

APPEAL = {'name': 'Test Foydalanuvchi', 'phone': '+998901234567', 'email': 'a@b.uz', 'recipient': 'rektor',
          'message': 'Salom, bu sinov murojaati.', 'consent': 'yes'}


class ParserTests(SimpleTestCase):
    def test_nul_bytes_are_removed_recursively(self):
        self.assertEqual(clean({'a\x00': ['x\x00y', {'k': 'v\x00'}], 'n': 5}), {'a': ['xy', {'k': 'v'}], 'n': 5})

    def test_depth_is_limited(self):
        deep = cur = {}
        for _ in range(60):
            cur['a'] = cur = {}
        with self.assertRaises(ParseError):
            clean(deep)

    def test_querydict_is_cleaned_and_stays_immutable(self):
        from django.http import QueryDict
        out = clean_querydict(QueryDict('a=x%00y&a=z&b=1'))
        self.assertEqual(out.getlist('a'), ['xy', 'z'])
        with self.assertRaises(AttributeError):
            out['c'] = '1'


class BadBodyTests(Base):
    def setUp(self):
        super().setUp()
        with loose():
            self.h = jwt_for('root')

    def post(self, data, ct='application/json', url='/api/cms/posts', headers=None):
        return Client(**(headers or self.h)).post(url, data=data, content_type=ct)

    def test_json_must_be_an_object_never_500(self):
        for body in ('[1,2,3]', 'null', '5', '"text"', '[' * 4000 + ']' * 4000, '{"a":' * 300 + '1' + '}' * 300):
            with self.subTest(body=body[:20]):
                self.assertEqual(self.post(body).status_code, 400)

    def test_nul_bytes_are_stripped_before_database(self):
        r = self.post(json.dumps({'type': 'news', 'title': {'uz': 'a\x00b'}}))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['doc']['title']['uz'], 'ab')

    def test_public_appeal_with_nul_bytes_is_stored_clean(self):
        cache.clear()
        r = Client(**HOST).post('/api/appeals', data={**APPEAL, 'message': 'Salom\x00 sinov murojaati'})   # multipart
        self.assertEqual(r.status_code, 200, r.content)
        self.assertNotIn('\x00', Appeal.objects.get().message)
        r = Client(**HOST).post('/api/appeals', data=json.dumps({**APPEAL, 'email': 'c@d.uz', 'name': 'Ism\x00Familiya'}), content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(Appeal.objects.filter(email='c@d.uz', name='IsmFamiliya').exists())


class BodyLimitTests(Base):
    def test_public_endpoints_reject_large_json_before_parsing(self):
        c = Client(**HOST)
        big = json.dumps({'message': 'x' * 200_000})
        for url, cap in (('/api/appeals', 64), ('/api/hit', 16), ('/api/site/hit', 16), ('/api/cms/users/login', 16), ('/api/auth/hemis/login', 16)):
            with self.subTest(url=url):
                r = c.post(url, data=big, content_type='application/json')
                self.assertEqual(r.status_code, 413, f'{url}: {r.status_code}')
                self.assertIn(f'{cap} KB', r.json()['message'])

    def test_panel_json_limit_is_bigger_but_bounded(self):
        with loose():
            h = jwt_for('root')
        ok = Client(**h).post('/api/cms/posts', data=json.dumps({'type': 'news', 'title': {'uz': 'x'}, 'excerpt': {'uz': 'e' * 100_000}}), content_type='application/json')
        self.assertEqual(ok.status_code, 201)
        too_big = Client(**h).post('/api/cms/posts', data='{"a":"' + 'x' * (9 * 1024 * 1024) + '"}', content_type='application/json')
        self.assertEqual(too_big.status_code, 413)


class BadFilterTests(Base):
    def test_non_numeric_filter_values_are_400_not_500(self):
        with loose():
            h = jwt_for('root')
        c = Client(**h)
        for slug, qs in [('posts', 'where[id][equals]=abc'), ('posts', 'where[id][equals][]=1&where[id][equals][]=2'),
                         ('posts', 'where[id][greater_than]=x'), ('posts', 'where[id][in]=a,b'), ('posts', 'where[id][in][a][b]=1'),
                         ('faculties', 'where[order][equals]=x'), ('users', 'where[id][in][0][x]=1')]:
            with self.subTest(qs=qs):
                self.assertEqual(c.get(f'/api/cms/{slug}?{qs}').status_code, 400)
        self.assertEqual(c.get('/api/cms/posts?where[id][in]=1,2').status_code, 200)
        self.assertEqual(c.patch('/api/cms/posts?where[id][equals]=abc', data='{}', content_type='application/json').status_code, 400)


class HeaderTests(Base):
    def test_admin_and_auth_responses_are_never_cached(self):
        with loose():
            h = jwt_for('root')
            login = Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': 'root', 'password': PASSWORD}), content_type='application/json')
        for label, res in (('login', login), ('list', Client(**h).get('/api/cms/posts')), ('me', Client(**h).get('/api/cms/users/me')),
                           ('404', Client(**h).get('/api/cms/nope')), ('401', Client(**HOST).get('/api/me'))):
            with self.subTest(label):
                self.assertEqual(res['Cache-Control'], 'private, no-store')

    def test_public_api_stays_cacheable_and_json_has_csp(self):
        r = Client(**HOST).get('/api/site')
        self.assertIn('max-age', r['Cache-Control'])
        self.assertNotIn('no-store', r['Cache-Control'])
        self.assertEqual(r['Content-Security-Policy'], "default-src 'none'; frame-ancestors 'none'")

    def test_html_pages_do_not_get_the_json_csp(self):
        r = Client(**HOST).get('/api/docs/')
        self.assertNotEqual(r.get('Content-Security-Policy'), "default-src 'none'; frame-ancestors 'none'")


class LoginOracleTests(Base):
    def login(self, u, p):
        return Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': u, 'password': p}), content_type='application/json')

    def test_unknown_username_locks_exactly_like_a_real_one(self):
        """423 faqat haqiqiy loginlarga chiqsa, loginlarni shu orqali topib olish mumkin bo'lardi."""
        with loose():
            cache.clear()
            codes = {name: [self.login(name, 'wrong').status_code for _ in range(13)] for name in ('ed', 'nobody-here')}
        self.assertEqual(codes['ed'], codes['nobody-here'])
        self.assertEqual(codes['ed'][-1], 423)
        self.assertEqual(codes['ed'][0], 401)

    def test_ghost_lock_is_case_insensitive_and_independent_per_name(self):
        with loose():
            cache.clear()
            for _ in range(12):
                self.login('Ghost', 'x')
            self.assertEqual(self.login('ghost', 'x').status_code, 423)
            self.assertEqual(self.login('other-ghost', 'x').status_code, 401)


class TokenStateTests(Base):
    def test_disabled_user_loses_access_immediately_and_role_comes_from_db(self):
        with loose():
            h = jwt_for('ed')
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 200)
        self.editor.role = 'sdg'
        self.editor.save()
        self.assertEqual(api('post', '/api/cms/posts', h, {'type': 'news', 'title': {'uz': 'x'}}).status_code, 403)   # token ichidagi eski rol hisobga olinmaydi
        self.editor.status = 'disabled'
        self.editor.save()
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 401)


class SeedFirstRunTests(TestCase):
    def run_seed(self, *args):
        call_command('seed_demo', *args, verbosity=0, stdout=io.StringIO(), stderr=io.StringIO())

    def test_first_run_flag_does_not_resurrect_deleted_content(self):
        with override_settings(DEBUG=True), mock.patch.dict('os.environ', {'SUPERADMIN_PASSWORD': 'Str0ng!Pass#2026-test'}):
            self.run_seed('--first-run')
            self.assertTrue(Slide.objects.exists())
            Slide.objects.all().delete()
            self.run_seed('--first-run')          # keyingi ishga tushish (deploy/restart)
            self.assertFalse(Slide.objects.exists(), 'admin o‘chirgan slaydlar qaytib kelmasligi kerak')
            self.run_seed()                       # qo'lda, bayroqsiz — avvalgidek bo'sh bo'limlarni to'ldiradi
            self.assertTrue(Slide.objects.exists())


class ProductionCheckTests(SimpleTestCase):
    def test_localhost_origins_warn_in_production(self):
        from apps.core.checks import security_settings
        with override_settings(DEBUG=False, TRUSTED_ORIGINS=['http://localhost:5173', 'https://admin.uz']):
            self.assertIn('uzswlu.W007', [w.id for w in security_settings(None)])
        with override_settings(DEBUG=False, TRUSTED_ORIGINS=['https://admin.uz', 'https://uz']):
            self.assertNotIn('uzswlu.W007', [w.id for w in security_settings(None)])
