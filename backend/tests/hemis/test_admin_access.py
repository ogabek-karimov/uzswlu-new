"""HEMIS orqali kirish → admin bergan hisob: rolni faqat admin beradi (Foydalanuvchilar → rol + HEMIS ID).
HEMIS lavozimi (dekan, mudir, o'qituvchi) hech qanday rol yoki kirish bermaydi; hisob o'zi yaratilmaydi."""
from django.test import TestCase

from apps.accounts.models import Role, StaffSession, User
from apps.hemis import access
from tests.support import seed_preset_roles

DEAN, CHAIR, TEACHER = '8654', '7768', '7792'


def bearer(hemis_id):
    return {'HTTP_AUTHORIZATION': f'Bearer {StaffSession.issue(hemis_id)}'}


class AdminAccessTests(TestCase):
    def setUp(self):
        seed_preset_roles()  # dekan (doirali), oqituvchi — migratsiya ularni o'chiradi, sinov uchun qayta yaratiladi
        self.dekan = Role.objects.get(slug='dekan')

    def give(self, hemis_id=DEAN, role='dekan', username='dekan1'):
        return User.objects.create(username=username, name='Qo‘lda', role=role, hemis_id=hemis_id)

    def test_no_account_no_access_and_nothing_created(self):
        # HEMIS'da dekan bo'lsa ham: admin hisob bermagan — hech narsa yo'q, hisob o'zi yaratilmaydi
        self.assertFalse(access.eligible(DEAN))
        self.assertFalse(access.cabinet_allowed(DEAN))
        self.assertIsNone(access.provision(DEAN))
        self.assertFalse(User.objects.filter(hemis_id=DEAN).exists())
        self.assertFalse(hasattr(Role, 'hemis_role'))  # lavozim bo'yicha avtomatik rol maydoni olib tashlangan

    def test_admin_given_account_keeps_role_and_refreshes_profile(self):
        u = self.give(TEACHER, role='editor', username='qolda')
        got = access.provision(TEACHER)
        self.assertEqual((got.pk, got.role), (u.pk, 'editor'))  # roli o'zgarmaydi — faqat ism/lavozim HEMIS'dan
        self.assertTrue(access.cabinet_allowed(TEACHER))

    def test_closed_or_unlinked_account_loses_access_immediately(self):
        u = self.give()
        self.assertTrue(access.cabinet_allowed(DEAN))
        u.status = 'disabled'
        u.save()
        self.assertFalse(access.cabinet_allowed(DEAN))
        self.assertIsNone(access.provision(DEAN))
        u.status, u.hemis_id = 'active', ''
        u.save()
        self.assertFalse(access.cabinet_allowed(DEAN))

    def test_no_role_staff_only_views_dashboard(self):
        # HEMIS'dagi lavozim (dekan) saytda rol bermaydi: Dashboard'ni ko'radi, lekin hech narsani o'zgartira olmaydi
        me = self.client.get('/api/me', **bearer(DEAN))
        self.assertEqual(me.status_code, 200)
        self.assertFalse(me.json()['hasRole'])
        self.assertEqual(self.client.get('/api/me/admin-link?list=1', **bearer(DEAN)).json()['available'], False)
        res = self.client.patch('/api/me', {'about': {'uz': 'x'}}, content_type='application/json', **bearer(DEAN))
        self.assertEqual(res.status_code, 403)
        self.assertIn('rol berilmagan', res.content.decode())
        self.assertEqual(self.client.get('/api/me/documents/articles', **bearer(DEAN)).status_code, 403)
        self.assertEqual(self.client.get('/api/me/cms/posts', **bearer(DEAN)).status_code, 403)
        # superadmin rol bersa — ishlaydi
        self.give()
        self.assertTrue(self.client.get('/api/me', **bearer(DEAN)).json()['hasRole'])
        self.assertEqual(self.client.patch('/api/me', {'about': {'uz': 'x'}}, content_type='application/json', **bearer(DEAN)).status_code, 200)

    def test_cabinet_link_and_one_time_handoff(self):
        self.give()
        res = self.client.get('/api/me/admin-link', **bearer(DEAN)).json()
        self.assertTrue(res['available'])
        from django.conf import settings
        # havola admin panel domenida: sessiya o'sha domenda ochiladi (aks holda brauzerdagi eski — masalan superadmin — sessiya qolardi)
        self.assertTrue(res['url'].startswith(settings.ADMIN_PANEL_URL + '/api/auth/hemis/handoff?t='), res['url'])
        path = res['url'][res['url'].index('/api/auth/hemis/handoff'):]
        first = self.client.get(path)
        self.assertEqual(first.status_code, 302)
        self.assertNotIn('kirish?hemis=', first['Location'])
        self.assertEqual(self.client.get('/api/cms/users/me').json()['user']['role'], 'dekan')
        # ikkinchi marta ishlamaydi (bir martalik) va soxta token rad etiladi
        self.assertIn('kirish?hemis=xato', self.client.get(path)['Location'])
        self.assertIn('kirish?hemis=xato', self.client.get('/api/auth/hemis/handoff?t=soxta')['Location'])

    def test_profile_menu_lists_own_sections_and_deep_links(self):
        self.give()
        res = self.client.get('/api/me/admin-link?list=1', **bearer(DEAN)).json()
        self.assertEqual((res['available'], res['url'], res['role']), (True, None, 'Dekan'))  # ro'yxat — havolasiz
        keys = [s['key'] for s in res['sections']]
        self.assertIn('news', keys)
        self.assertNotIn('dashboard', keys)
        self.assertNotIn('leaders', keys)  # rolda yo'q bo'lim ko'rinmaydi
        self.assertEqual({s['level'] for s in res['sections']} - {'read', 'write'}, set())
        self.assertEqual(res['stats'], {'published': 0, 'drafts': 0, 'month': 0})  # kabinet bosh sahifasidagi rol paneli raqamlari
        link = self.client.get('/api/me/admin-link?next=news', **bearer(DEAN)).json()['url']
        res = self.client.get(link[link.index('/api/auth/hemis/handoff'):])
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res['Location'].endswith('/postlar/news'), res['Location'])
        self.assertEqual(self.client.get('/api/me/admin-link?next=leaders', **bearer(DEAN)).status_code, 404)

    def test_handoff_ignores_foreign_path(self):
        from django.core import signing
        from django.core.cache import cache
        self.give()
        cache.set('hemis-handoff:zz', 1, 30)
        token = signing.dumps({'h': DEAN, 'n': 'zz', 'p': 'https://evil.example/'}, salt='hemis-admin-handoff')
        res = self.client.get(f'/api/auth/hemis/handoff?t={token}')
        self.assertEqual(res.status_code, 302)
        self.assertNotIn('evil.example', res['Location'])
