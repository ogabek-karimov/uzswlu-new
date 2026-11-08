"""Kirish: JWT, parol almashganda bekor qilish, 2FA (TOTP)."""
import json

from django.core.cache import cache
from django.test import Client, override_settings
from tests.support import HOST, Base, api, jwt_for, loose


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


@loose()
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
