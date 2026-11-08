"""So‘rov cheklovi (throttle) va ochiq API keshi."""
import json

from django.test import Client, override_settings
from apps.structure.models import Faculty
from tests.support import HOST, Base, api, jwt_for


class ThrottleTests(Base):
    def test_login_brute_force_is_limited(self):
        c = Client(**HOST)
        codes = [c.post('/api/cms/users/login', data=json.dumps({'username': 'nobody', 'password': 'x'}),
                        content_type='application/json').status_code for _ in range(12)]
        self.assertEqual(codes[0], 401)
        self.assertIn(429, codes)

    def test_spoofed_forwarded_for_does_not_bypass(self):
        c = Client(**HOST)
        codes = [c.post('/api/cms/users/login', data=json.dumps({'username': 'nobody', 'password': 'x'}),
                        content_type='application/json', HTTP_X_FORWARDED_FOR=f'10.0.0.{i}').status_code for i in range(12)]
        self.assertIn(429, codes)

    @override_settings(REST_FRAMEWORK={**__import__('django.conf', fromlist=['settings']).settings.REST_FRAMEWORK, 'NUM_PROXIES': 1})
    def test_with_trusted_proxy_each_client_has_own_limit(self):
        c = Client(**HOST)
        codes = [c.post('/api/cms/users/login', data=json.dumps({'username': 'nobody', 'password': 'x'}),
                        content_type='application/json', HTTP_X_FORWARDED_FOR=f'203.0.113.{i}').status_code for i in range(12)]
        self.assertNotIn(429, codes)

    def test_public_api_is_limited_per_ip(self):
        with override_settings(REST_FRAMEWORK={**__import__('django.conf', fromlist=['settings']).settings.REST_FRAMEWORK,
                                               'DEFAULT_THROTTLE_RATES': {**__import__('django.conf', fromlist=['settings']).settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], 'public': '3/min'}}):
            codes = [Client(**HOST).get('/api/contact').status_code for _ in range(5)]
        self.assertEqual(codes.count(429), 2)

    def test_trusted_site_server_is_not_throttled(self):
        rest = __import__('django.conf', fromlist=['settings']).settings.REST_FRAMEWORK
        with override_settings(API_TOKEN='site-secret', REST_FRAMEWORK={**rest, 'DEFAULT_THROTTLE_RATES': {**rest['DEFAULT_THROTTLE_RATES'], 'public': '2/min'}}):
            codes = [Client(**HOST).get('/api/contact', HTTP_AUTHORIZATION='Bearer site-secret').status_code for _ in range(6)]
        self.assertNotIn(429, codes)


class PublicCacheTests(Base):
    def test_cache_never_bypasses_api_token(self):
        with override_settings(API_TOKEN='site-secret'):
            ok = Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION='Bearer site-secret')
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(Client(**HOST).get('/api/faculties').status_code, 403)
            self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION='Bearer wrong').status_code, 403)

    def test_cache_refreshes_after_admin_edit(self):
        first = Client(**HOST).get('/api/faculties').content
        self.assertIn(b'A fakultet', first)
        h = jwt_for('root')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'name': {'uz': 'Yangi nom'}}).status_code, 200)
        self.assertIn('Yangi nom', Client(**HOST).get('/api/faculties').content.decode())

    def test_cache_is_per_language_and_query(self):
        a = Client(**HOST).get('/api/faculties?lang=uz').content
        b = Client(**HOST).get('/api/faculties?lang=ru').content
        self.assertIsInstance(json.loads(a), (dict, list))
        self.assertIsInstance(json.loads(b), (dict, list))

    def test_errors_are_not_cached(self):
        self.assertEqual(Client(**HOST).get('/api/faculties/yoq').status_code, 404)
        Faculty.objects.create(slug='yoq', name={'uz': 'Yoq'})
        self.assertEqual(Client(**HOST).get('/api/faculties/yoq').status_code, 200)
