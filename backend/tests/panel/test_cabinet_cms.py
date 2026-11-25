"""Kabinet → panel ko'prigi: sayt ichidagi kabinetdan yangilik/e'lon/tadbir yozish (rol ruxsatlari admin paneldagi bilan bir xil)."""
from django.test import TestCase

from apps.accounts.models import Role, StaffSession, User
from apps.content.models import Post
from tests.support import give_cabinet_role, seed_preset_roles

DEAN, TEACHER = '8654', '7792'
POSTS = '/api/me/cms/posts'


def bearer(hemis_id):
    return {'HTTP_AUTHORIZATION': f'Bearer {StaffSession.issue(hemis_id)}'}


def new(title='Sinov', type_='news', **extra):
    return {'type': type_, 'title': {'uz': title}, 'status': 'published', **extra}


class CabinetCmsTests(TestCase):
    def setUp(self):
        seed_preset_roles()
        # Rolni admin beradi: hisob + rol + HEMIS ID (lavozim bo'yicha avtomatik rol yo'q)
        self.dean_acc = give_cabinet_role(DEAN, role='dekan')
        give_cabinet_role(TEACHER, role='oqituvchi')

    def post(self, path, body, who=DEAN):
        return self.client.post(path, body, content_type='application/json', **bearer(who))

    def test_requires_login_and_role(self):
        self.assertEqual(self.client.get(POSTS).status_code, 401)
        self.dean_acc.hemis_id = ''
        self.dean_acc.save()
        self.assertEqual(self.client.get(POSTS, **bearer(DEAN)).status_code, 403)  # admin HEMIS ID ni olib tashladi — kirish yo'q

    def test_dean_creates_edits_and_deletes_own_post(self):
        res = self.post(POSTS, new())
        self.assertEqual(res.status_code, 201, res.content)
        doc = res.json()['doc']
        author = User.objects.get(hemis_id=DEAN)
        self.assertEqual(Post.objects.get(pk=doc['id']).author_id, author.pk)  # muallif — xodimning admin hisobi
        res = self.client.patch(f'{POSTS}/{doc["id"]}', {'title': {'uz': 'Yangi'}}, content_type='application/json', **bearer(DEAN))
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(Post.objects.get(pk=doc['id']).title['uz'], 'Yangi')
        listed = self.client.get(f'{POSTS}?where[type][equals]=news', **bearer(DEAN)).json()
        self.assertIn(doc['id'], [d['id'] for d in listed['docs']])
        self.assertTrue(next(d for d in listed['docs'] if d['id'] == doc['id'])['own'])
        other = User.objects.create(username='boshqa0', name='Boshqa', role='editor')
        foreign = Post.objects.create(type='news', title={'uz': 'Begona'}, status='published', author=other)
        listed = self.client.get(f'{POSTS}?where[type][equals]=news', **bearer(DEAN)).json()
        self.assertFalse(next(d for d in listed['docs'] if d['id'] == foreign.pk)['own'])
        self.assertEqual(self.client.delete(f'{POSTS}/{doc["id"]}', **bearer(DEAN)).status_code, 200)
        self.assertIsNotNone(Post.objects.get(pk=doc['id']).deleted_at)  # savatga tushadi

    def test_cannot_touch_someone_elses_post(self):
        other = User.objects.create(username='boshqa', name='Boshqa', role='editor')
        p = Post.objects.create(type='news', title={'uz': 'Begona'}, status='published', author=other)
        self.assertEqual(self.client.patch(f'{POSTS}/{p.pk}', {'title': {'uz': 'X'}}, content_type='application/json', **bearer(DEAN)).status_code, 403)
        self.assertEqual(self.client.delete(f'{POSTS}/{p.pk}', **bearer(DEAN)).status_code, 403)

    def test_role_sections_are_enforced(self):
        # o'qituvchi: yangilik — faqat o'qish, tadbir — yozish
        self.assertEqual(self.post(POSTS, new(), TEACHER).status_code, 403)
        self.assertEqual(self.post(POSTS, new(type_='events'), TEACHER).status_code, 201)

    def test_only_whitelisted_collections_and_no_bulk(self):
        self.assertEqual(self.client.get('/api/me/cms/users', **bearer(DEAN)).status_code, 404)
        self.assertEqual(self.client.get('/api/me/cms/media', **bearer(DEAN)).status_code, 404)  # kutubxonani ko'rish yo'q
        self.assertEqual(self.client.patch(POSTS + '?where[id][in]=1', {}, content_type='application/json', **bearer(DEAN)).status_code, 405)
        self.assertEqual(self.client.delete(POSTS + '?where[id][in]=1', **bearer(DEAN)).status_code, 405)

    def test_post_writer_can_upload_cover_without_media_section(self):
        # Rolda faqat «Yangiliklar» (media yo'q): post uchun rasm yuklay oladi, kutubxonani ko'ra/o'chira olmaydi
        import io

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        Role.objects.filter(slug='dekan').update(permissions={'news': 'write'})
        buf = io.BytesIO()
        Image.new('RGB', (40, 40), 'red').save(buf, 'PNG')
        res = self.client.post('/api/me/cms/media', {'file': SimpleUploadedFile('a.png', buf.getvalue(), 'image/png')}, **bearer(DEAN))
        self.assertIn(res.status_code, (200, 201), res.content[:200])
        self.assertEqual(self.client.get('/api/me/cms/media', **bearer(DEAN)).status_code, 404)  # kutubxona ro'yxati yo'q
