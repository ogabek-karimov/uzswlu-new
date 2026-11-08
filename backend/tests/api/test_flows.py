"""Ochiq API oqimlari (demo ma'lumot bilan): sanoqlar, eski /api/site/* manzillari, API token, xodim kabineti, murojaat, statistika."""
import io
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.accounts.models import StaffSession
from apps.core.models import Hit
from tests.support import SeededTestCase

PDF = b'%PDF-1.4 test\n%%EOF\n'


def uploaded(name: str, data: bytes, ctype: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, ctype)


class SeedDataTests(SeededTestCase):
    """Demo ma'lumot yuklangandan keyingi sanoqlar (seed_data/ o'zgarsa — shu sonlar ham yangilanadi)."""

    def get(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        return r.json()

    def test_home(self):
        h = self.get('/api/home?lang=uz')
        self.assertEqual((len(h['news']), len(h['announcements'])), (4, 4))
        self.assertEqual([s['key'] for s in h['stats']], ['faculties', 'staff', 'departments', 'students'])
        self.assertEqual((len(h['slides']), len(h['faculties']), len(h['partners'])), (7, 11, 10))
        self.assertTrue(h['slides'][0]['image'].startswith('http://localhost:8000/media/'))

    def test_site_menu_and_symbols(self):
        s = self.get('/api/site?lang=ru')
        self.assertEqual(len(s['menu']), 8)
        self.assertEqual(len(s['symbols'] or []), 3)

    def test_staff_search_and_summary(self):
        self.assertEqual(self.get("/api/staff?lang=uz&q=yo%27ldoshev")['total'], 1)
        st = self.get('/api/staff?lang=uz')
        self.assertEqual((st['summary']['staff'], st['groups']['all']), (55, 55))

    def test_posts_and_search(self):
        self.assertGreater(self.get('/api/posts?type=news&lang=ru')['total'], 0)
        self.assertGreater(self.get('/api/search?q=universitet&lang=uz')['total'], 0)

    def test_legacy_site_endpoints_still_served(self):
        for u in ['latest', 'slides', 'index', 'settings', 'symbols', 'menu', 'sdg-goals', 'staff-hidden', 'staff/9300',
                  'posts?type=news', 'events', 'leadership', 'documents', 'videos', 'faculties',
                  'faculties/english-philology', 'sdg/6', 'pages/universitet-haqida']:
            with self.subTest(url=u):
                self.assertEqual(self.client.get('/api/site/' + u).status_code, 200)

    def test_public_api_requires_token_when_configured(self):
        with override_settings(API_TOKEN='secret-token'):
            self.assertIn(self.client.get('/api/home').status_code, (401, 403))
            self.assertEqual(self.client.get('/api/home', HTTP_AUTHORIZATION='Bearer secret-token').status_code, 200)
            self.assertIn(self.client.get('/api/home', HTTP_AUTHORIZATION='Bearer wrong').status_code, (401, 403))
            self.assertEqual(self.client.get('/api/site/latest').status_code, 200)   # /api/site/* — tokensiz ochiq


class StaffCabinetFlowTests(SeededTestCase):
    """Xodim kabineti: HEMIS orqali kirgan xodim o'z profilini tahrirlaydi (ketma-ket oqim)."""

    def setUp(self):
        super().setUp()
        self.A = {'HTTP_AUTHORIZATION': f"Bearer {StaffSession.issue('9300')}"}

    def patch(self, body, **kw):
        return self.client.patch('/api/me', json.dumps(body), content_type='application/json', **self.A)

    def test_requires_login(self):
        self.assertEqual(self.client.get('/api/me').status_code, 401)

    def test_profile_roundtrip_and_validation(self):
        me = self.client.get('/api/me?lang=uz', **self.A).json()
        self.assertEqual((me['hemis']['lastName'], me['hemis']['firstName']), ('Tuxtasinov', 'Ilxomjon'))
        r = self.patch({'about': {'uz': 'Salom <b>dunyo</b>', 'en': 'Hello'},
                        'contacts': [{'type': 'email', 'value': 'a@b.uz'}, {'type': 'phone', 'value': ''}],
                        'socials': [{'network': 'instagram', 'url': 'https://instagram.com/x'}],
                        'science': [{'network': 'orcid', 'url': 'https://orcid.org/0000'}], 'visibility': {'cv': False}})
        self.assertEqual(r.status_code, 200, r.content)
        pub = self.client.get('/api/staff/9300?lang=en').json()
        self.assertEqual(pub['about'], 'Hello')
        self.assertEqual(pub['contacts'], [{'type': 'email', 'value': 'a@b.uz'}])   # bo'sh telefon tashlandi
        self.assertEqual(pub['socials'][0]['network'], 'instagram')
        self.assertEqual(self.client.get('/api/staff/9300?lang=uz').json()['about'], 'Salom dunyo')   # HTML tozalandi
        self.assertEqual(self.patch({'socials': [{'network': 'instagram', 'url': 'http://x'}]}).status_code, 422)   # http emas
        self.assertEqual(self.patch({'contacts': [{'type': 'email', 'value': 'nope'}]}).status_code, 422)

    def test_avatar(self):
        buf = io.BytesIO()
        Image.new('RGB', (900, 500), 'red').save(buf, 'PNG')
        r = self.client.post('/api/me/avatar', {'file': uploaded('a.png', buf.getvalue(), 'image/png')}, **self.A)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(self.client.get('/api/staff/9300').json()['photo'])
        self.assertIs(self.client.get('/api/me', **self.A).json()['hasOwnPhoto'], True)
        r = self.client.post('/api/me/avatar', {'file': uploaded('a.png', b'not an image', 'image/png')}, **self.A)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.delete('/api/me/avatar', **self.A).status_code, 200)
        self.assertFalse(self.client.get('/api/staff/9300').json()['photo'])

    def test_documents(self):
        c, A = self.client, self.A
        r = c.post('/api/me/documents/cv', {'title_uz': 'Mening CV', 'title_en': 'My CV', 'file': uploaded('cv.pdf', PDF, 'application/pdf')}, **A)
        self.assertEqual(r.status_code, 200, r.content)
        doc = r.json()
        self.assertEqual(c.post('/api/me/documents/cv', {'title_uz': 'x', 'file': uploaded('x.pdf', b'MZ not pdf', 'application/pdf')}, **A).status_code, 422)
        self.assertEqual(c.post('/api/me/documents/cv', {'file': uploaded('x.pdf', PDF, 'application/pdf')}, **A).status_code, 422)   # nomsiz
        self.assertEqual(c.post('/api/me/documents/videos', {'title_uz': 'Video', 'url': 'https://youtu.be/abcdefghijk'}, **A).status_code, 200)
        self.assertEqual(c.post('/api/me/documents/videos', {'title_uz': 'Video', 'url': 'http://youtu.be/x'}, **A).status_code, 422)
        self.assertEqual(len(c.get('/api/me/documents/cv', **A).json()), 1)
        # ko'rinish: cv yashirilgan → ommaviy profilda yo'q; yoqilsa — tilga qarab nom (zh → en ga qaytadi)
        self.patch({'visibility': {'cv': False}})
        self.assertFalse(any(d['section'] == 'cv' for d in c.get('/api/staff/9300').json()['documents']))
        self.patch({'visibility': {'cv': True}})
        pub = c.get('/api/staff/9300?lang=zh').json()
        self.assertTrue(any(d['section'] == 'cv' and d['items'][0]['title'] == 'My CV' for d in pub['documents']))
        self.assertEqual(c.delete(f"/api/me/documents/cv/{doc['id']}", **A).status_code, 200)
        self.assertEqual(c.delete(f"/api/me/documents/cv/{doc['id']}", **A).status_code, 404)
        self.assertEqual(c.get('/api/me/documents/xyz', **A).status_code, 404)


class AppealAndHitTests(SeededTestCase):
    def good(self):
        rec = self.client.get('/api/contact').json()['recipients'][0]['id']
        return {'name': 'Test Foydalanuvchi', 'phone': '+998 90 123 45 67', 'email': 't@example.com',
                'recipient': rec, 'message': 'Bu test murojaati matni.', 'consent': 'yes'}

    def test_appeal(self):
        good = self.good()
        r = self.client.post('/api/appeals', good)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()['number'].startswith('VQ-'))
        self.assertEqual(self.client.post('/api/appeals', {**good, 'consent': 'no'}).status_code, 422)
        self.assertEqual(self.client.post('/api/appeals', {**good, 'phone': 'abc'}).status_code, 422)
        r = self.client.post('/api/appeals', {**good, 'file': uploaded('a.pdf', PDF, 'application/pdf')})
        self.assertEqual(r.status_code, 200, r.content)

    def test_hit_statistics_never_fail(self):
        r = self.client.post('/api/hit', json.dumps({'kind': 'pageview', 'path': '/', 'lang': 'uz'}),
                             content_type='text/plain', HTTP_USER_AGENT='Mozilla/5.0 (iPhone)')
        self.assertEqual(r.status_code, 204)
        self.assertEqual(Hit.objects.filter(kind='pageview', device='mobile').count(), 1)
        self.assertEqual(self.client.post('/api/hit', 'garbage', content_type='text/plain').status_code, 204)
        r = self.client.post('/api/site/hit', json.dumps({'kind': 'event', 'name': 'x'}), content_type='text/plain', HTTP_USER_AGENT='Mozilla/5.0')
        self.assertEqual(r.status_code, 204)
