"""Swagger to'liqligi: kodda ishlaydigan har bir amal hujjatda bo'lishi shart (yangi endpoint/kolleksiya qo'shilganda
hujjatni unutib qoldirmaslik uchun), va hujjat tomoshabin roliga bog'liq emas."""
import re

from django.test import Client, TestCase
from django.urls import get_resolver

from apps.panel.collections import REGISTRY
from apps.panel.globals_ import GLOBALS

METHODS = ('get', 'post', 'put', 'patch', 'delete')
# Ataylab hujjatlanmaydiganlar: hujjatning o'zi va eski tashqi manzil (ichki yo'naltirish)
HIDDEN = {'/api/schema', '/api/docs', '/api/redoc', '/api/media/file/{}'}


def norm(path: str) -> str:
    return re.sub(r'\{[^}]+\}', '{}', path).rstrip('/')


def get_schema(client=None) -> dict:
    return (client or Client(HTTP_HOST='localhost')).get('/api/schema/?format=json').json()


def code_routes():
    """URLconf dagi har bir `/api/*` yo'l uchun View qabul qiladigan metodlar (parametr nomlari normallashtirilgan)."""
    def walk(resolver, prefix=''):
        for entry in resolver.url_patterns:
            pattern = prefix + str(entry.pattern)
            if hasattr(entry, 'url_patterns'):
                yield from walk(entry, pattern)
            else:
                yield pattern, entry.callback
    for pattern, callback in walk(get_resolver()):
        cls = getattr(callback, 'cls', None)
        if not pattern.startswith('api/') or cls is None:
            continue
        path = norm('/' + re.sub(r'<(?:\w+:)?(\w+)>', '{}', pattern))
        yield path, cls, {m for m in METHODS if hasattr(cls, m)}


class SwaggerCompletenessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema = get_schema()
        cls.paths = cls.schema['paths']

    def ops(self, path):
        return {m for m in self.paths.get(path, {}) if m in METHODS}

    def test_every_collection_action_is_documented(self):
        """Ruxsatlar jadvalidagi (`coll.access`) har bir amal uchun: ro'yxat, bitta yozuv, ommaviy amal, soni."""
        for slug, coll in REGISTRY.items():
            acc, base = coll.access, f'/api/cms/{slug}'
            expected = {
                base: {m for a, m in (('read', 'get'), ('create', 'post'), ('update', 'patch'), ('delete', 'delete')) if a in acc},
                f'{base}/{{id}}': {m for a, m in (('read', 'get'), ('update', 'patch'), ('delete', 'delete')) if a in acc},
                f'{base}/count': {'get'} if 'read' in acc else set(),
            }
            for path, methods in expected.items():
                with self.subTest(path=path):
                    self.assertTrue(methods <= self.ops(path), f'{path}: kutilgan {sorted(methods)}, hujjatda {sorted(self.ops(path))}')

    def test_bulk_operations_documented_for_every_writable_collection(self):
        for slug, coll in REGISTRY.items():
            for action, method in (('update', 'patch'), ('delete', 'delete')):
                if action in coll.access:
                    with self.subTest(collection=slug, bulk=method):
                        self.assertIn(method, self.ops(f'/api/cms/{slug}'))
                        self.assertEqual(self.paths[f'/api/cms/{slug}'][method]['operationId'], f'cms_{slug}_bulk_{action}')

    def test_versions_and_globals(self):
        for slug, coll in REGISTRY.items():
            if coll.versions:
                with self.subTest(collection=slug):
                    self.assertEqual(self.ops(f'/api/cms/{slug}/versions'), {'get'})
                    self.assertEqual(self.ops(f'/api/cms/{slug}/versions/{{vid}}'), {'post'})
        for slug, g in GLOBALS.items():
            with self.subTest(glob=slug):
                self.assertTrue({'get', 'post'} <= self.ops(f'/api/cms/globals/{slug}'))
                if g.versions:
                    self.assertEqual(self.ops(f'/api/cms/globals/{slug}/versions'), {'get'})

    def test_every_code_route_is_documented(self):
        documented = {}
        for path, item in self.paths.items():
            documented.setdefault(norm(path), set()).update(m for m in item if m in METHODS)
        missing = []
        for path, cls, methods in code_routes():
            # Umumiy `/api/cms/{slug}...` shablonlari har bir kolleksiya uchun alohida yo'llarga ochiladi (yuqoridagi testlar)
            if path in HIDDEN or path.startswith(('/api/cms/{}', '/api/cms/globals/{}')):
                continue
            gap = methods - documented.get(path, set())
            if gap:
                missing.append(f'{sorted(gap)} {path} [{cls.__name__}]')
        self.assertEqual(missing, [], 'Hujjatda yo‘q amallar — swagger.py/extend_schema ni yangilang')

    def test_admin_collection_operations_state_allowed_roles(self):
        for slug in REGISTRY:
            for path in (f'/api/cms/{slug}', f'/api/cms/{slug}/{{id}}'):
                for method in self.ops(path):
                    with self.subTest(path=path, method=method):
                        self.assertIn('Ruxsat', self.paths[path][method].get('description', ''), 'kim uchun ekani yozilmagan')

    def test_operation_ids_are_unique(self):
        ids = [op['operationId'] for item in self.paths.values() for m, op in item.items() if m in METHODS and 'operationId' in op]
        self.assertEqual(len(ids), len(set(ids)))


class SwaggerDoesNotDependOnViewerTests(TestCase):
    def test_same_schema_for_anonymous_and_every_role(self):
        from tests.support import PASSWORD, Base  # noqa: F401  (foydalanuvchilar yaratish uchun)
        from apps.accounts.models import User
        anon = get_schema()
        for role in ('superadmin', 'editor', 'faculty', 'pages', 'sdg'):
            user = User.objects.create_user(f'u_{role}', password=PASSWORD, role=role, name=role)
            client = Client(HTTP_HOST='localhost')
            client.force_login(user)
            with self.subTest(role=role):
                self.assertEqual(get_schema(client), anon, 'hujjat rolga qarab o‘zgarmasligi kerak')
