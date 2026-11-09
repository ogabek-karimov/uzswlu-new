"""Hujum simulyatsiyasi: ma'lumot o'g'irlash (oracle, enumeration, IDOR, draft sizishi, token/rol), scraping va suiiste'mol.

Har test — haqiqiy hujumchi qiladigan so'rov; himoya ishlamasa yiqiladi.
"""
import json
import re
from datetime import timedelta

from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.content.models import Post
from apps.panel.collections import REGISTRY
from tests.support import HOST, PASSWORD, Base, api, jwt_for, loose

SECRET_KEYS = re.compile(r'(password|totp|recovery|token_hash|tokenhash|secret|session_key|legacy_password|is_superuser)', re.I)


def walk(node, path=''):
    """JSON ichidagi hamma (yo'l, qiymat) juftligi."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f'{path}.{k}')
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f'{path}[{i}]')
    else:
        yield path, node


class Panel(Base):
    def setUp(self):
        super().setUp()
        mk = User.objects.create_user
        mk('fac', password=PASSWORD, role='faculty', name='Fac', scope='fa')
        mk('pg', password=PASSWORD, role='pages', name='Pg')
        with loose():
            self.h = {u: jwt_for(u) for u in ('root', 'ed', 'fac', 'pg')}
        self.root_hash = self.admin.password

    # ── 1. Filtr/saralash orqali parol xeshini topish (oracle) ──────────────────────
    ATTACKS = [
        'where[password][like]=pbkdf2', 'where[password][contains]=$', 'where[totpSecret][exists]=true', 'where[totp_secret][like]=a',
        'where[recoveryHashes][exists]=true', 'where[legacyPassword][exists]=true', 'where[tokenHash][like]=a', 'where[isSuperuser][equals]=true',
        'where[author.password][like]=pbkdf2', 'where[author__password][like]=pbkdf2', 'where[author][password][like]=p',
        'where[author.totpSecret][exists]=true', 'where[user.password][like]=p', 'where[uploadedBy.password][like]=p',
        'sort=password', 'sort=-password', 'sort=author.password', 'sort=-author__password', 'sort=totpSecret', 'sort=user.password',
        'where[or][0][password][like]=p', 'where[and][0][author.password][like]=p',
    ]

    def test_no_password_hash_oracle_on_any_collection(self):
        for slug in REGISTRY:
            for atk in self.ATTACKS:
                with self.subTest(collection=slug, attack=atk):
                    res = api('get', f'/api/cms/{slug}?limit=1&{atk}', self.h['root'])
                    # 400 (rad etildi) yoki e'tiborsiz qoldirildi — ikkalasida ham natija «filtr ishladi» ma'nosini bermasligi kerak
                    self.assertIn(res.status_code, (200, 400, 403, 404), res.content[:200])
                    if res.status_code == 200 and ('where' in atk):
                        # Filtr ishlagan bo'lsa, "pbkdf2" bilan boshlanuvchi xeshlar bo'yicha bo'sh/to'liq farq oracle bo'lardi
                        self.fail(f'filtr qabul qilindi: {slug} {atk}') if slug in ('users', 'posts', 'media', 'activity') else None

    def test_secrets_never_in_any_response(self):
        """Superadmin hamma kolleksiyani chuqurlik 3 bilan oladi — hech qayerda xesh/TOTP/token chiqmasin."""
        User.objects.filter(username='ed').update(totp_secret='JBSWY3DPEHPK3PXP', totp_enabled=True)
        for slug, coll in REGISTRY.items():
            if 'read' not in coll.access:
                continue
            res = api('get', f'/api/cms/{slug}?limit=50&depth=3', self.h['root'])
            body = res.content.decode()
            with self.subTest(collection=slug):
                for path, value in walk(res.json()):
                    self.assertFalse(SECRET_KEYS.search(path.split('.')[-1]) and value not in (None, False, '', 0), f'{slug}: {path}')
                self.assertNotIn('pbkdf2_', body)
                self.assertNotIn('JBSWY3DPEHPK3PXP', body)
                self.assertNotIn(self.root_hash, body)

    def test_other_roles_see_no_hashes_either(self):
        for role in ('ed', 'fac', 'pg'):
            for slug in ('users', 'posts', 'media', 'activity', 'login-events'):
                res = api('get', f'/api/cms/{slug}?limit=20&depth=3', self.h[role])
                self.assertNotIn('pbkdf2_', res.content.decode(), f'{role} {slug}')
                self.assertNotIn('totp', res.content.decode().lower().replace('totpenabled', ''), f'{role} {slug}')

    # ── 2. IDOR va mass-assignment ─────────────────────────────────────────────────────
    def test_non_admin_cannot_read_or_change_other_users(self):
        for role in ('ed', 'fac', 'pg'):
            res = api('get', f'/api/cms/users/{self.admin.pk}', self.h[role])
            self.assertIn(res.status_code, (403, 404), f'{role} superadmin yozuvini o‘qiy oldi')
            res = api('patch', f'/api/cms/users/{self.admin.pk}', self.h[role], {'name': 'Hack', 'password': 'Hacked-123456!'})
            self.assertIn(res.status_code, (403, 404), role)
            listing = api('get', '/api/cms/users?limit=100', self.h[role]).json()
            self.assertEqual({d['username'] for d in listing['docs']}, {{'ed': 'ed', 'fac': 'fac', 'pg': 'pg'}[role]}, f'{role} boshqalarni ko‘rdi')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.name, 'Root')

    def test_mass_assignment_cannot_escalate_privileges(self):
        me = self.editor.pk
        attack = {'role': 'superadmin', 'status': 'active', 'scope': 'fa', 'isSuperuser': True, 'is_superuser': True, 'isStaff': True,
                  'is_staff': True, 'totpEnabled': False, 'totp_enabled': False, 'lockUntil': None, 'loginAttempts': 0, 'groups': [1], 'username': 'root'}
        res = api('patch', f'/api/cms/users/{me}', self.h['ed'], attack)
        self.assertIn(res.status_code, (200, 400, 403), res.content[:200])
        u = User.objects.get(pk=me)
        self.assertEqual((u.role, u.username, u.is_superuser, u.scope), ('editor', 'ed', False, ''))  # is_staff — panel belgisi, hamma panel foydalanuvchisida True
        self.assertEqual(api('get', '/api/cms/users', self.h['ed']).status_code, 200)
        self.assertEqual(api('post', '/api/cms/users', self.h['ed'], {'username': 'new', 'password': 'Pw-12345678!x', 'role': 'superadmin'}).status_code, 403)

    def test_role_change_takes_effect_with_existing_token(self):
        """Foydalanuvchi pasaytirilsa/bloklansa — eski token darhol kuchini yo'qotsin (token ichidagi rolga ishonilmasin)."""
        User.objects.filter(username='ed').update(role='sdg')
        res = api('post', '/api/cms/posts', self.h['ed'], {'title': {'uz': 'x'}, 'type': 'news'})
        self.assertEqual(res.status_code, 403, 'pasaytirilgan foydalanuvchi eski token bilan post yarata oldi')
        User.objects.filter(username='fac').update(status='disabled')   # bloklash = status 'disabled'
        self.assertIn(api('get', '/api/cms/posts', self.h['fac']).status_code, (401, 403), 'bloklangan foydalanuvchi tokeni ishladi')

    def test_password_change_revokes_other_sessions(self):
        old = self.h['pg']
        res = api('patch', f"/api/cms/users/{User.objects.get(username='pg').pk}", old, {'password': 'New-Pw-1234567!', 'currentPassword': PASSWORD})
        self.assertEqual(res.status_code, 200, res.content[:200])
        self.assertIn(api('get', '/api/cms/posts', old).status_code, (401, 403), 'parol almashgach eski token yaroqli qoldi')

    # ── 3. JWT hujumlari ────────────────────────────────────────────────────────────────
    def test_forged_and_tampered_tokens_rejected(self):
        import base64
        good = self.h['root']['HTTP_AUTHORIZATION'].split()[1]
        head, payload, sig = good.split('.')
        b64 = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b'=').decode()
        claims = json.loads(base64.urlsafe_b64decode(payload + '=='))
        forged = {
            'alg none': f"{b64({'alg': 'none', 'typ': 'JWT'})}.{payload}.",
            'tampered role': f"{head}.{b64({**claims, 'role': 'superadmin', 'id': self.admin.pk})}.{sig}",
            'bad signature': f'{head}.{payload}.{sig[:-4]}AAAA',
            'empty': '', 'garbage': 'a.b.c',
            'expired': f"{head}.{b64({**claims, 'exp': 1})}.{sig}",
        }
        # ed tokeniga root id'sini yozib ko'ramiz
        ed_good = self.h['ed']['HTTP_AUTHORIZATION'].split()[1].split('.')
        forged['ed token + root id'] = f"{ed_good[0]}.{b64({**json.loads(base64.urlsafe_b64decode(ed_good[1] + '==')), 'id': self.admin.pk, 'sub': self.admin.pk})}.{ed_good[2]}"
        for name, tok in forged.items():
            with self.subTest(attack=name):
                res = Client().get('/api/cms/users', HTTP_AUTHORIZATION=f'Bearer {tok}', **HOST)
                self.assertIn(res.status_code, (401, 403), f'{name}: {res.status_code}')

    def test_logout_revokes_token(self):
        h = self.h['ed']
        self.assertEqual(api('get', '/api/cms/posts?limit=1', h).status_code, 200)
        api('post', '/api/cms/users/logout', h, {})
        self.assertIn(api('get', '/api/cms/posts?limit=1', h).status_code, (401, 403), 'logoutdan keyin token ishladi')

    def test_login_does_not_reveal_which_usernames_exist(self):
        def msg(u, p):
            with loose():
                r = Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': u, 'password': p}), content_type='application/json')
            return r.status_code, r.json().get('message')
        self.assertEqual(msg('root', 'wrong-pass-123'), msg('no-such-user', 'wrong-pass-123'))

    def test_sort_never_reaches_orm_with_secret_fields(self):
        """`sort=password` 200 qaytarsa ham, saralash ORM'ga yetib bormasligi kerak (aks holda tartib orqali xesh topiladi)."""
        from unittest import mock

        from django.db.models.query import QuerySet
        seen = []
        real = QuerySet.order_by

        def spy(self_, *fields, **kw):
            seen.extend(str(f) for f in fields)
            return real(self_, *fields, **kw)
        with mock.patch.object(QuerySet, 'order_by', spy):
            for slug in ('users', 'posts', 'media', 'activity', 'login-events'):
                for sort in ('password', '-password', 'author.password', '-author__password', 'totpSecret', 'user.password', 'recoveryHashes', 'uploadedBy.password'):
                    api('get', f'/api/cms/{slug}?limit=5&sort={sort}', self.h['root'])
        bad = [f for f in seen if re.search(r'password|totp|recovery|secret|token_hash', f, re.I)]
        self.assertEqual(bad, [], f'maxfiy maydon bo‘yicha saralash ORM ga yetdi: {bad[:5]}')


class Public(Base):
    def setUp(self):
        super().setUp()
        cache.clear()
        mk = lambda slug, **kw: Post.objects.create(type='news', slug=slug, title={'uz': slug, 'ru': slug, 'en': slug, 'zh': slug}, **kw)
        now = timezone.now()
        mk('published', status='published', published_at=now - timedelta(hours=1))
        mk('draft', status='draft', published_at=now - timedelta(hours=1))
        mk('future', status='published', published_at=now + timedelta(days=3))
        mk('trashed', status='published', published_at=now - timedelta(hours=1), deleted_at=now)
        mk('nodate', status='published', published_at=None)
        self.c = Client(**HOST)

    HIDDEN = ('draft', 'future', 'trashed')

    def test_unpublished_posts_are_invisible_everywhere(self):
        for prefix in ('/api', '/api/site'):
            listing = self.c.get(f'{prefix}/posts?limit=50')
            self.assertEqual(listing.status_code, 200)
            text = listing.content.decode()
            for slug in self.HIDDEN:
                self.assertNotIn(f'"{slug}"', text, f'{prefix}/posts ro‘yxatida {slug}')
                self.assertEqual(self.c.get(f'{prefix}/posts/news/{slug}').status_code, 404, f'{prefix} {slug} to‘g‘ridan-to‘g‘ri ochildi')
        for ep in ('/api/search?q=draft', '/api/search?q=future', '/api/search?q=trashed', '/api/home', '/api/site/latest', '/api/site/index', '/api/events'):
            text = self.c.get(ep).content.decode()
            for slug in self.HIDDEN:
                self.assertNotIn(f'"slug": "{slug}"', text.replace('":"', '": "'), f'{ep} {slug} sizdi')
                self.assertNotIn(f'/{slug}"', text, f'{ep} {slug} sizdi')

    @override_settings(API_TOKEN='s3cret-token-value')
    def test_token_required_on_public_api(self):
        for ep in ('/api/posts', '/api/home', '/api/staff', '/api/faculties', '/api/documents', '/api/search?q=abc', '/api/pages/x', '/api/leadership'):
            with self.subTest(ep=ep):
                self.assertIn(self.c.get(ep).status_code, (401, 403))
                self.assertIn(self.c.get(ep, HTTP_X_API_TOKEN='wrong').status_code, (401, 403))
                self.assertIn(self.c.get(ep + ('&' if '?' in ep else '?') + 'token=s3cret-token-value').status_code, (401, 403), 'token query orqali berilmasin (loglarga tushadi)')

    def test_scraping_limits(self):
        for q in ('limit=100000', 'limit=-1', 'limit=abc', 'page=99999999', 'page=-5', 'limit=0'):
            res = self.c.get(f'/api/posts?{q}')
            self.assertIn(res.status_code, (200, 400, 422), q)
            if res.status_code == 200:
                self.assertLessEqual(len(res.json().get('items', res.json().get('docs', []))), 100, q)
        long_q = 'a' * 20000
        self.assertIn(self.c.get('/api/search', {'q': long_q}).status_code, (200, 400, 414, 422))

    def test_enumeration_returns_uniform_404(self):
        a = self.c.get('/api/posts/news/no-such-slug')
        b = self.c.get('/api/posts/news/draft')            # bor, lekin yashirin
        self.assertEqual((a.status_code, a.content), (b.status_code, b.content), 'mavjud-lekin-yashirin va yo‘q post farqlanadi')
        for url in ('/api/staff/999999', '/api/staff/abc', '/api/staff/1;DROP', '/api/documents/999999/file', '/api/faculties/zzz', '/api/sdg/99'):
            self.assertIn(self.c.get(url).status_code, (404, 400), url)

    @override_settings(REST_FRAMEWORK={**__import__('django.conf', fromlist=['settings']).settings.REST_FRAMEWORK,
                                       'DEFAULT_THROTTLE_RATES': {**__import__('django.conf', fromlist=['settings']).settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], 'public': '5/min'}})
    def test_spoofed_forwarded_for_cannot_evade_throttle(self):
        cache.clear()
        codes = [self.c.get('/api/posts', HTTP_X_FORWARDED_FOR=f'10.0.0.{i}', HTTP_X_REAL_IP=f'10.1.1.{i}').status_code for i in range(9)]
        self.assertIn(429, codes, 'X-Forwarded-For bilan cheklovni aylanib o‘tish mumkin')

    def test_appeal_response_does_not_leak_neighbours(self):
        body = {'name': 'Test User', 'phone': '+998901234567', 'email': 'a@b.uz', 'recipient': 'rector', 'message': 'Salom, bu sinov murojaati', 'consent': 'yes'}
        res = self.c.post('/api/appeals', data=body)
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(set(res.json()), {'number'})
        for url in ('/api/appeals/1', '/api/appeals/VQ-2026-00001', '/api/appeals?number=VQ-2026-00001'):
            self.assertIn(self.c.get(url).status_code, (404, 405), f'{url} murojaat ma’lumotini berdi')

