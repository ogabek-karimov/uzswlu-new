"""Swagger'dagi `x-roles` haqiqatga mosligi: har rol × amal uchun server 403 qaytaradi ⇔ rol `x-roles` da yo'q.

Hujjat (Swagger) va kod (`Collection.access`, ko'rinishlardagi rol tekshiruvlari) ajralib ketsa — shu test yiqiladi.
Yozuvsiz (`where[id][equals]=0`) so'rovlar ishlatiladi, shuning uchun ma'lumot o'zgarmaydi.
"""
from apps.accounts.models import User
from apps.api.swagger import ALL_ROLES
from apps.panel.collections import REGISTRY
from apps.panel.globals_ import GLOBALS
from tests.api.test_swagger import get_schema
from tests.support import PASSWORD, Base, api, jwt_for, loose

NOTHING = 'where[id][equals]=0'


class RoleMatrixTests(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.paths = get_schema()['paths']

    def setUp(self):
        super().setUp()
        self.h = {}
        for role in ALL_ROLES:
            User.objects.filter(username=f'm_{role}').delete()
            User.objects.create_user(f'm_{role}', password=PASSWORD, role=role, name=role, scope='fa' if role == 'faculty' else '')
        with loose():
            for role in ALL_ROLES:
                self.h[role] = jwt_for(f'm_{role}')

    def roles_of(self, path, method):
        return set(self.paths[path][method]['x-roles'])

    def check(self, method, path, url, body=None):
        allowed = self.roles_of(path, method)
        for role in sorted(ALL_ROLES):
            with self.subTest(op=f'{method.upper()} {path}', role=role):
                res = api(method, url, self.h[role], body)
                if role in allowed:
                    # Rol darvozasi: «Ruxsat yo‘q». Boshqa 403 (masalan «bu fakultet doirangizda emas») — ob'ekt darajasidagi qoida, `x-rules` da yoziladi
                    gate = res.status_code == 401 or (res.status_code == 403 and b'Ruxsat yo\xe2\x80\x98q' in res.content.replace(b'\\u2018', '\u2018'.encode()))
                    self.assertFalse(gate, f'{role} ruxsat etilgan, lekin {res.status_code}: {res.content[:200]}')
                else:
                    self.assertEqual(res.status_code, 403, f'{role} ruxsatsiz bo‘lishi kerak, lekin {res.status_code}')

    def test_collection_operations(self):
        for slug, coll in REGISTRY.items():
            base = f'/api/cms/{slug}'
            acc = coll.access
            if 'read' in acc:
                self.check('get', base, f'{base}?limit=1')
                self.check('get', f'{base}/count', f'{base}/count')
                self.check('get', f'{base}/{{id}}', f'{base}/0')
            if 'create' in acc:
                self.check('post', base, base, {})
            if 'update' in acc:
                self.check('patch', base, f'{base}?{NOTHING}', {})
            if 'delete' in acc:
                self.check('delete', base, f'{base}?{NOTHING}')
                self.check('delete', f'{base}/{{id}}', f'{base}/0')

    def test_globals(self):
        for slug, g in GLOBALS.items():
            base = f'/api/cms/globals/{slug}'
            self.check('get', base, base)
            self.check('post', base, base, {})

    def test_panel_and_admin_only_endpoints(self):
        from apps.api.swagger import _panel_roles
        for path in _panel_roles():
            method = 'post' if path.endswith(('unlock', '2fa/reset')) else 'get'
            self.check(method, path, path.replace('{id}', '0').replace('{name}', 'x'), {} if method == 'post' else None)

    def test_anonymous_is_rejected_everywhere(self):
        from django.test import Client
        from tests.support import HOST
        for path, item in self.paths.items():
            if not path.startswith('/api/cms/') or '{' in path:
                continue
            for method, op in item.items():
                if method not in ('get', 'post', 'patch', 'delete') or 'x-roles' not in op or {} in op.get('security', []) or path.endswith('/logout'):
                    continue  # tokensiz ruxsat etilganlar (`security: [{}]`) va idempotent `logout` o'tkazib yuboriladi
                with self.subTest(op=f'{method.upper()} {path}'):
                    with loose('login'), loose('panel-read'), loose('panel-write'):
                        res = getattr(Client(**HOST), method)(path)
                    self.assertIn(res.status_code, (400, 401, 403), res.content[:120])  # hech qachon 2xx emas

    def test_bulk_without_where_is_rejected(self):
        for slug, coll in REGISTRY.items():
            for action, method in (('update', 'patch'), ('delete', 'delete')):
                if action in coll.access:
                    with self.subTest(collection=slug, method=method):
                        res = api(method, f'/api/cms/{slug}', self.h['superadmin'], {} if method == 'patch' else None)
                        self.assertEqual(res.status_code, 400)

    def test_role_filtered_schema_matches_x_roles(self):
        from django.test import Client
        for role in sorted(ALL_ROLES):
            doc = Client(HTTP_HOST='localhost').get(f'/api/schema/?format=json&role={role}').json()
            for path, item in doc['paths'].items():
                for method, op in item.items():
                    if isinstance(op, dict) and 'x-roles' in op:
                        with self.subTest(role=role, op=f'{method} {path}'):
                            self.assertIn(role, op['x-roles'])
            full = {(p, m) for p, i in self.paths.items() for m, o in i.items() if isinstance(o, dict) and role in o.get('x-roles', ())}
            kept = {(p, m) for p, i in doc['paths'].items() for m, o in i.items() if isinstance(o, dict) and 'x-roles' in o}
            self.assertEqual(full, kept, f'{role}: filtr bitta amalni ham yo‘qotmasligi kerak')
