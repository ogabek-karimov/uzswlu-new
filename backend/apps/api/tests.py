"""Xavfsizlik testlari: id almashtirib begona ma'lumot olish (IDOR), parol "oracle"i, so'rov cheklovi, kesh.

Ishga tushirish:  python manage.py test apps.api
"""
import json

from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from apps.accounts.models import StaffSession, User
from apps.structure.models import Department, Faculty, StaffDocument

HOST = {'HTTP_HOST': 'localhost'}


def jwt_for(username: str, password: str = 'Pw-12345678!') -> dict:
    res = Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': username, 'password': password}),
                              content_type='application/json')
    assert res.status_code == 200, res.content
    return {'HTTP_AUTHORIZATION': f"Bearer {res.json()['token']}", **HOST}


def api(method: str, url: str, headers: dict, body: dict | None = None):
    c = Client()
    kw = dict(headers)
    if body is not None:
        kw.update(data=json.dumps(body), content_type='application/json')
    return getattr(c, method)(url, **kw)


class Base(TestCase):
    def setUp(self):
        cache.clear()
        mk = User.objects.create_user
        self.admin = mk('root', password='Pw-12345678!', role='superadmin', name='Root')
        self.editor = mk('ed', password='Pw-12345678!', role='editor', name='Editor')
        self.fa = Faculty.objects.create(slug='fa', name={'uz': 'A fakultet'})
        self.fb = Faculty.objects.create(slug='fb', name={'uz': 'B fakultet'})
        self.da = Department.objects.create(hemis_id='d-a', faculty_slug='fa', name={'uz': 'A kafedra'})
        self.db = Department.objects.create(hemis_id='d-b', faculty_slug='fb', name={'uz': 'B kafedra'})


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


class ObjectLevelAccessTests(Base):
    """Fakultet admini faqat o'z fakultetini o'zgartira oladi; boshqasi id orqali ham mumkin emas."""

    def setUp(self):
        super().setUp()
        User.objects.create_user('fac_a', password='Pw-12345678!', role='faculty', name='A admin', scope='fa')
        User.objects.create_user('fac_none', password='Pw-12345678!', role='faculty', name='Doirasiz')

    def test_own_faculty_ok_other_forbidden(self):
        h = jwt_for('fac_a')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'phone': '1'}).status_code, 200)
        res = api('patch', f'/api/cms/faculties/{self.fb.pk}', h, {'phone': '2'})
        self.assertEqual(res.status_code, 403)
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.phone, '')

    def test_faculty_without_scope_can_edit_nothing(self):
        h = jwt_for('fac_none')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'phone': '1'}).status_code, 403)
        self.assertEqual(api('patch', f'/api/cms/departments/{self.da.pk}', h, {'room': '1'}).status_code, 403)

    def test_department_scope(self):
        h = jwt_for('fac_a')
        self.assertEqual(api('patch', f'/api/cms/departments/{self.da.pk}', h, {'room': '12'}).status_code, 200)
        self.assertEqual(api('patch', f'/api/cms/departments/{self.db.pk}', h, {'room': '12'}).status_code, 403)

    def test_cannot_move_department_to_other_faculty(self):
        h = jwt_for('fac_a')
        res = api('patch', f'/api/cms/departments/{self.da.pk}', h, {'faculty': 'fb'})
        self.assertEqual(res.status_code, 403)
        self.da.refresh_from_db()
        self.assertEqual(self.da.faculty_slug, 'fa')

    def test_cannot_create_department_in_other_faculty(self):
        h = jwt_for('fac_a')
        res = api('post', '/api/cms/departments', h, {'hemisId': 'new', 'faculty': 'fb', 'name': {'uz': 'X'}})
        self.assertEqual(res.status_code, 403)
        self.assertFalse(Department.objects.filter(hemis_id='new').exists())
        res = api('post', '/api/cms/departments', h, {'hemisId': 'new', 'faculty': 'fa', 'name': {'uz': 'X'}})
        self.assertEqual(res.status_code, 201)

    def test_bulk_patch_respects_scope(self):
        h = jwt_for('fac_a')
        res = api('patch', '/api/cms/departments?where[hemisId][like]=d-', h, {'room': '99'})
        self.assertEqual(res.status_code, 200)
        self.da.refresh_from_db()
        self.db.refresh_from_db()
        self.assertEqual(self.da.room, '99')
        self.assertEqual(self.db.room, '')
        self.assertEqual(len(res.json()['errors']), 1)

    def test_editor_cannot_touch_faculty_at_all(self):
        h = jwt_for('ed')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'phone': '1'}).status_code, 403)


class UserRecordTests(Base):
    def test_editor_sees_only_self(self):
        h = jwt_for('ed')
        res = api('get', '/api/cms/users', h)
        self.assertEqual(res.json()['totalDocs'], 1)
        self.assertEqual(api('get', f'/api/cms/users/{self.admin.pk}', h).status_code, 404)
        self.assertEqual(api('patch', f'/api/cms/users/{self.admin.pk}', h, {'name': 'x'}).status_code, 404)

    def test_editor_cannot_raise_own_role(self):
        h = jwt_for('ed')
        api('patch', f'/api/cms/users/{self.editor.pk}', h, {'role': 'superadmin'})
        self.editor.refresh_from_db()
        self.assertEqual(self.editor.role, 'editor')

    def test_login_history_only_superadmin(self):
        self.assertEqual(api('get', '/api/cms/login-events', jwt_for('ed')).status_code, 403)


class CabinetIsolationTests(Base):
    """Xodim kabineti: boshqa xodim hujjatini id raqamini o'zgartirib ko'rib/o'chirib bo'lmaydi."""

    def setUp(self):
        super().setUp()
        self.tok_a, self.tok_b = StaffSession.issue('1001'), StaffSession.issue('1002')
        self.doc_b = StaffDocument.objects.create(hemis_id='1002', section='articles', title={'uz': 'B maqolasi'}, url='https://example.org/b')
        self.doc_a = StaffDocument.objects.create(hemis_id='1001', section='articles', title={'uz': 'A maqolasi'}, url='https://example.org/a')

    def h(self, token):
        return {'HTTP_AUTHORIZATION': f'Bearer {token}', **HOST}

    def test_cannot_delete_foreign_document(self):
        res = api('delete', f'/api/me/documents/articles/{self.doc_b.pk}', self.h(self.tok_a))
        self.assertEqual(res.status_code, 404)
        self.assertTrue(StaffDocument.objects.filter(pk=self.doc_b.pk).exists())

    def test_wrong_section_is_not_found(self):
        res = api('delete', f'/api/me/documents/books/{self.doc_a.pk}', self.h(self.tok_a))
        self.assertEqual(res.status_code, 404)

    def test_list_contains_only_own(self):
        res = api('get', '/api/me/documents/articles', self.h(self.tok_a))
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('B maqolasi', res.content.decode())

    def test_no_session_no_access(self):
        self.assertEqual(api('get', '/api/me', HOST).status_code, 401)
        self.assertEqual(api('get', '/api/me', self.h('yaroqsiz-token')).status_code, 401)

    def test_admin_jwt_is_not_a_staff_session(self):
        self.assertEqual(api('get', '/api/me', jwt_for('root')).status_code, 401)


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


class PanelAuthTests(Base):
    def test_requests_without_credentials_are_rejected(self):
        for url in ('/api/cms/posts', '/api/cms/users', '/api/cms/media', '/api/cms/panel/overview'):
            self.assertIn(Client(**HOST).get(url).status_code, (401, 403), url)

    def test_forged_jwt_is_rejected(self):
        self.assertIn(Client(**HOST).get('/api/cms/posts', HTTP_AUTHORIZATION='Bearer a.b.c').status_code, (401, 403))

    def test_jwt_dies_after_password_change(self):
        h = jwt_for('ed')
        self.editor.set_password('Another-Pass-987!')
        self.editor.save()
        self.assertEqual(api('get', '/api/cms/users/me', h).status_code, 401)
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 401)


class PasswordAndRevocationTests(Base):
    def test_own_password_change_needs_current_password(self):
        h = jwt_for('ed')
        url = f'/api/cms/users/{self.editor.pk}'
        self.assertEqual(api('patch', url, h, {'password': 'Yangi-parol-12345!'}).status_code, 400)
        self.assertEqual(api('patch', url, h, {'password': 'Yangi-parol-12345!', 'currentPassword': 'xato'}).status_code, 400)
        self.editor.refresh_from_db()
        self.assertTrue(self.editor.check_password('Pw-12345678!'))
        self.assertEqual(api('patch', url, h, {'password': 'Yangi-parol-12345!', 'currentPassword': 'Pw-12345678!'}).status_code, 200)
        self.editor.refresh_from_db()
        self.assertTrue(self.editor.check_password('Yangi-parol-12345!'))

    def test_current_password_guessing_is_stopped(self):
        h = jwt_for('ed')
        url = f'/api/cms/users/{self.editor.pk}'
        codes = [api('patch', url, h, {'password': 'Yangi-parol-12345!', 'currentPassword': f'x{i}'}).status_code for i in range(7)]
        self.assertEqual(codes[:5], [400] * 5)
        self.assertEqual(codes[5], 403)
        # to'xtatilgandan keyin to'g'ri parol ham qabul qilinmaydi
        self.assertEqual(api('patch', url, h, {'password': 'Yangi-parol-12345!', 'currentPassword': 'Pw-12345678!'}).status_code, 403)

    def test_superadmin_can_reset_other_users_password(self):
        h = jwt_for('root')
        res = api('patch', f'/api/cms/users/{self.editor.pk}', h, {'password': 'Tiklangan-parol-1!'})
        self.assertEqual(res.status_code, 200)

    def test_logout_revokes_jwt(self):
        h = jwt_for('ed')
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 200)
        self.assertEqual(api('post', '/api/cms/users/logout', h).status_code, 200)
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 401)

    def test_refresh_revokes_old_token_and_new_works(self):
        h = jwt_for('ed')
        res = api('post', '/api/cms/users/refresh-token', h)
        self.assertEqual(res.status_code, 200)
        new = {'HTTP_AUTHORIZATION': f"Bearer {res.json()['token']}", **HOST}
        self.assertEqual(api('get', '/api/cms/posts', new).status_code, 200)
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 401)

    def test_revocation_survives_cache_clear(self):
        h = jwt_for('ed')
        api('post', '/api/cms/users/logout', h)
        cache.clear()
        self.assertEqual(api('get', '/api/cms/posts', h).status_code, 401)

    def test_other_tokens_of_same_user_stay_valid(self):
        h1, h2 = jwt_for('ed'), jwt_for('ed')
        api('post', '/api/cms/users/logout', h1)
        self.assertEqual(api('get', '/api/cms/posts', h2).status_code, 200)


class HiddenStaffTests(Base):
    def test_hidden_list_needs_token_when_configured(self):
        from apps.structure.models import StaffProfile
        StaffProfile.objects.create(hemis_id='777', hidden=True)
        with override_settings(API_TOKEN='site-secret'):
            self.assertEqual(Client(**HOST).get('/api/site/staff-hidden').status_code, 403)
            ok = Client(**HOST).get('/api/site/staff-hidden', HTTP_AUTHORIZATION='Bearer site-secret')
            self.assertEqual(ok.json()['ids'], ['777'])

    def test_hidden_staff_not_in_public_list_or_detail(self):
        from apps.structure.models import StaffProfile
        StaffProfile.objects.create(hemis_id='888', hidden=True)
        self.assertNotIn('888', Client(**HOST).get('/api/staff').content.decode())
        self.assertEqual(Client(**HOST).get('/api/staff/888').status_code, 404)


class PostOwnershipTests(Base):
    def setUp(self):
        super().setUp()
        from apps.content.models import Post
        self.pages = User.objects.create_user('pg', password='Pw-12345678!', role='pages', name='Pages')
        self.fac = User.objects.create_user('fc', password='Pw-12345678!', role='faculty', name='Fac', scope='fa')
        self.mine = Post.objects.create(type='news', slug='mine', title={'uz': 'Meniki'}, author=self.pages)
        self.other = Post.objects.create(type='news', slug='other', title={'uz': 'Boshqaniki'}, author=self.editor)
        self.orphan = Post.objects.create(type='news', slug='orphan', title={'uz': 'Egasiz'})

    def test_pages_role_edits_only_own_posts(self):
        h = jwt_for('pg')
        self.assertEqual(api('patch', f'/api/cms/posts/{self.mine.pk}', h, {'title': {'uz': 'Yangi'}}).status_code, 200)
        self.assertEqual(api('patch', f'/api/cms/posts/{self.other.pk}', h, {'title': {'uz': 'Buzildi'}}).status_code, 403)
        self.assertEqual(api('patch', f'/api/cms/posts/{self.orphan.pk}', h, {'title': {'uz': 'Buzildi'}}).status_code, 403)
        self.other.refresh_from_db()
        self.assertEqual(self.other.title['uz'], 'Boshqaniki')

    def test_cannot_delete_foreign_post(self):
        from apps.content.models import Post
        h = jwt_for('fc')
        self.assertEqual(api('delete', f'/api/cms/posts/{self.other.pk}', h).status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.other.pk).exists())

    def test_bulk_patch_only_touches_own_posts(self):
        h = jwt_for('pg')
        res = api('patch', '/api/cms/posts?where[type][equals]=news', h, {'category': None, 'title': {'uz': 'Ommaviy'}})
        self.other.refresh_from_db()
        self.assertEqual(self.other.title['uz'], 'Boshqaniki')

    def test_editor_and_superadmin_manage_all(self):
        self.assertEqual(api('patch', f'/api/cms/posts/{self.mine.pk}', jwt_for('ed'), {'title': {'uz': 'E'}}).status_code, 200)
        self.assertEqual(api('patch', f'/api/cms/posts/{self.other.pk}', jwt_for('root'), {'title': {'uz': 'R'}}).status_code, 200)

    def test_new_post_belongs_to_creator(self):
        from apps.content.models import Post
        h = jwt_for('pg')
        res = api('post', '/api/cms/posts', h, {'type': 'news', 'title': {'uz': 'Yangi post'}, 'slug': 'yangi-post'})
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(Post.objects.get(slug='yangi-post').author_id, self.pages.pk)


class TokenRotationAndChecksTests(Base):
    def test_old_and_new_api_token_both_work_during_rotation(self):
        with override_settings(API_TOKEN='new-token-value,old-token-value'):
            for t in ('new-token-value', 'old-token-value'):
                self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION=f'Bearer {t}').status_code, 200)
            self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION='Bearer third').status_code, 403)
            self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION='Bearer new-token-value,old-token-value').status_code, 403)

    def test_production_checks_warn_about_weak_settings(self):
        from apps.core.checks import security_settings
        with override_settings(DEBUG=False, API_TOKEN='short', API_DOCS_PUBLIC=True, ALLOWED_HOSTS=['*']):
            ids = {w.id for w in security_settings(None)}
        self.assertTrue({'uzswlu.W002', 'uzswlu.W004', 'uzswlu.W005', 'uzswlu.W006'} <= ids)
        with override_settings(DEBUG=True):
            self.assertEqual(security_settings(None), [])


def _loose(scope='login', rate='1000/min'):
    from django.conf import settings as st
    rf = {**st.REST_FRAMEWORK, 'DEFAULT_THROTTLE_RATES': {**st.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], scope: rate}}
    return override_settings(REST_FRAMEWORK=rf)


@_loose()
class TwoFactorTests(Base):
    """TOTP: yoqish, kirishdagi 2-qadam, zaxira kodlar, qayta ishlatish va brute-force himoyasi."""

    def setUp(self):
        super().setUp()
        self.h = jwt_for('ed')

    def totp(self, user, offset=0):
        import time

        from apps.panel.twofactor import _code
        user.refresh_from_db()
        return _code(user.totp_secret, int(time.time() // 30) + offset)

    def enroll(self):
        res = api('post', '/api/cms/users/2fa/setup', self.h)
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn('otpauth://totp/', res.json()['otpauthUri'])
        res = api('post', '/api/cms/users/2fa/enable', self.h, {'code': self.totp(self.editor)})
        self.assertEqual(res.status_code, 200, res.content)
        return res.json()['recoveryCodes']

    def login(self, password='Pw-12345678!'):
        return Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': 'ed', 'password': password}), content_type='application/json')

    def second(self, challenge, code):
        return Client(**HOST).post('/api/cms/users/login/2fa', data=json.dumps({'challenge': challenge, 'code': code}), content_type='application/json')

    def test_setup_does_not_enable_until_code_confirmed(self):
        api('post', '/api/cms/users/2fa/setup', self.h)
        self.editor.refresh_from_db()
        self.assertFalse(self.editor.totp_enabled)
        self.assertEqual(self.login().json().get('twoFactorRequired'), None)
        self.assertEqual(api('post', '/api/cms/users/2fa/enable', self.h, {'code': '000000'}).status_code, 400)

    def test_login_needs_second_step(self):
        self.enroll()
        res = self.login()
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body['twoFactorRequired'])
        self.assertNotIn('token', body)
        self.assertNotIn('user', body)
        self.assertNotIn('sessionid', res.cookies)  # sessiya berilmagan
        done = self.second(body['challenge'], self.totp(self.editor, 1))
        self.assertEqual(done.status_code, 200, done.content)
        self.assertIn('token', done.json())

    def test_wrong_code_and_replay_rejected(self):
        self.enroll()
        ch = self.login().json()['challenge']
        self.assertEqual(self.second(ch, '123456').status_code, 401)
        code = self.totp(self.editor, 1)
        self.assertEqual(self.second(ch, code).status_code, 200)
        ch2 = self.login().json()['challenge']
        self.assertEqual(self.second(ch2, code).status_code, 401)  # bir kod ikki marta ishlamaydi

    def test_forged_or_foreign_challenge_rejected(self):
        self.enroll()
        self.assertEqual(self.second('abc.def', '123456').status_code, 401)
        ch = self.login().json()['challenge']
        body, sig = ch.split('.')
        self.assertEqual(self.second(f'{body}.{sig[::-1]}', self.totp(self.editor)).status_code, 401)

    def test_recovery_code_works_once(self):
        codes = self.enroll()
        ch = self.login().json()['challenge']
        self.assertEqual(self.second(ch, codes[0]).status_code, 200)
        ch = self.login().json()['challenge']
        self.assertEqual(self.second(ch, codes[0]).status_code, 401)
        self.assertEqual(self.second(ch, codes[1]).status_code, 200)

    def test_code_guessing_locks_account(self):
        self.enroll()
        ch = self.login().json()['challenge']
        codes = [self.second(ch, f'{i:06d}').status_code for i in range(6)]
        self.assertEqual(codes[:5], [401] * 5)
        self.assertEqual(codes[5], 423)
        self.assertEqual(self.login().status_code, 423)

    def test_password_alone_is_not_enough(self):
        self.enroll()
        res = self.login()
        self.assertNotIn('token', res.json())
        self.assertEqual(Client(**HOST).get('/api/cms/posts').status_code in (401, 403), True)

    def test_disable_needs_password_and_code(self):
        self.enroll()
        url = '/api/cms/users/2fa/disable'
        self.assertEqual(api('post', url, self.h, {'password': 'xato', 'code': self.totp(self.editor, 1)}).status_code, 400)
        self.assertEqual(api('post', url, self.h, {'password': 'Pw-12345678!', 'code': '111111'}).status_code, 400)
        self.assertEqual(api('post', url, self.h, {'password': 'Pw-12345678!', 'code': self.totp(self.editor, 1)}).status_code, 200)
        self.editor.refresh_from_db()
        self.assertFalse(self.editor.totp_enabled)
        self.assertEqual(self.editor.totp_secret, '')

    def test_superadmin_can_reset_lost_device(self):
        self.enroll()
        self.assertEqual(api('post', '/api/cms/users/2fa/reset', self.h, {'username': 'root'}).status_code, 403)
        self.assertEqual(api('post', '/api/cms/users/2fa/reset', jwt_for('root'), {'username': 'ed'}).status_code, 200)
        self.assertNotIn('twoFactorRequired', self.login().json())

    def test_secret_never_exposed(self):
        self.enroll()
        res = api('get', f'/api/cms/users/{self.editor.pk}', self.h).content.decode()
        self.assertIn('twoFactorEnabled', res)
        self.editor.refresh_from_db()
        self.assertNotIn(self.editor.totp_secret, res)
        self.assertEqual(api('get', '/api/cms/users?where[totpSecret][like]=A', jwt_for('root')).status_code, 400)

    def test_required_role_blocked_until_enrolled(self):
        with override_settings(REQUIRE_2FA_ROLES=['editor']):
            self.assertEqual(api('get', '/api/cms/posts', self.h).status_code, 403)
            self.assertEqual(api('post', '/api/cms/users/2fa/setup', self.h).status_code, 200)  # sozlash yo'li ochiq
            api('post', '/api/cms/users/2fa/enable', self.h, {'code': self.totp(self.editor)})
            self.assertEqual(api('get', '/api/cms/posts', self.h).status_code, 200)
            self.assertEqual(api('post', '/api/cms/users/2fa/disable', self.h, {'password': 'Pw-12345678!', 'code': self.totp(self.editor, 1)}).status_code, 403)

    def test_totp_matches_rfc6238_vector(self):
        from apps.panel.twofactor import _code
        import base64
        secret = base64.b32encode(b'12345678901234567890').decode()
        self.assertEqual(_code(secret, 59 // 30), '287082')  # RFC 6238 (T=59, SHA1, 6 xona: 94287082 -> 287082)
