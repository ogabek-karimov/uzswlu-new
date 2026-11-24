"""ID almashtirib boshqa ma'lumotni olishga urinish (IDOR): so'rovdagi ID/`where` ni o'zgartirib ruxsatsiz yozuvni o'qib bo'lmaydi.
Versiyalar tarixi, yashirilgan xodim profili va HEMIS ID biriktirish."""
from django.conf import settings

from apps.accounts.models import Role, User
from apps.content.models import Post
from apps.panel.models import Version
from apps.structure.models import StaffProfile
from tests.panel.test_collections import PanelBase


class IdSwapTests(PanelBase):
    def test_versions_of_other_post_types_are_not_readable(self):
        secret = Post.objects.create(type='announcements', title={'uz': 'Maxfiy qoralama'}, status='draft')
        Version.objects.create(entity='posts', entity_id=str(secret.pk), data={'title': {'uz': 'Maxfiy qoralama'}})
        Role.objects.create(slug='faqat-yangilik', name='Faqat yangilik', permissions={'news': 'write'})
        u = User(username='yangilikchi', name='Y', role='faqat-yangilik', status='active')
        u.set_password('Parol-12345!')
        u.save()
        self.client.logout()
        self.client.force_login(u)
        res = self.client.get(f'/api/cms/posts/versions?where[parent][equals]={secret.pk}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.j(res)['docs'], [])  # e'lonlar bo'limiga ruxsati yo'q — versiya ko'rinmaydi
        self.assertNotIn('Maxfiy', res.content.decode())
        self.assertEqual(self.client.get(f'/api/cms/posts/{secret.pk}').status_code, 404)

    def test_hidden_staff_overlay_reveals_nothing(self):
        StaffProfile.objects.update_or_create(hemis_id='9300', defaults={'hidden': True, 'about': {'uz': 'Shaxsiy matn'}, 'science': [{'network': 'orcid', 'url': 'https://orcid.org/x'}]})
        self.client.logout()
        auth = {'HTTP_AUTHORIZATION': f'Bearer {settings.API_TOKEN}'} if settings.API_TOKEN else {}
        res = self.client.get('/api/site/staff/9300', **auth)
        self.assertEqual(res.status_code, 200, res.content[:200])
        self.assertEqual(res.json(), {'hidden': True, 'about': None, 'science': []})
        self.assertEqual(self.client.get('/api/staff/9300').status_code, 404)

    def test_hemis_id_must_exist_and_be_unique(self):
        a = User.objects.create(username='a1', name='A', role='editor')
        b = User.objects.create(username='b1', name='B', role='editor')
        self.assertEqual(self.send('patch', f'/api/cms/users/{a.pk}', {'hemisId': '1133'}).status_code, 400)  # HEMIS'da yo'q
        self.assertEqual(self.send('patch', f'/api/cms/users/{a.pk}', {'hemisId': '9300'}).status_code, 200)
        res = self.send('patch', f'/api/cms/users/{b.pk}', {'hemisId': '9300'})  # boshqa hisobda band
        self.assertEqual(res.status_code, 400)
        self.assertIn('boshqa hisobga', res.content.decode())
        self.assertEqual(self.send('patch', f'/api/cms/users/{a.pk}', {'hemisId': ''}).status_code, 200)  # olib tashlash mumkin
