"""HEMIS lavozimi → admin hisobi: avtomatik yaratish, doira, yopish va kabinetdan o'tish havolasi."""
from django.test import TestCase

from apps.accounts.models import Role, StaffSession, User
from apps.hemis import access

DEAN, CHAIR, TEACHER = '8654', '7768', '7792'


def bearer(hemis_id):
    return {'HTTP_AUTHORIZATION': f'Bearer {StaffSession.issue(hemis_id)}'}


class AdminAccessTests(TestCase):
    def setUp(self):
        # Migratsiyadagi tayyor rollar: dekan (doirali), oqituvchi
        self.dekan = Role.objects.get(slug='dekan')
        self.oqituvchi = Role.objects.get(slug='oqituvchi')

    def test_off_by_default(self):
        self.assertFalse(access.eligible(DEAN))
        self.assertIsNone(access.provision(DEAN))
        self.assertFalse(User.objects.filter(hemis_id=DEAN).exists())

    def test_dean_gets_scoped_account_when_mapped(self):
        self.dekan.hemis_role = 'dean'
        self.dekan.save()
        self.assertTrue(access.eligible(DEAN))
        u = access.provision(DEAN)
        self.assertEqual((u.role, u.hemis_auto, u.status), ('dekan', True, 'active'))
        self.assertFalse(u.has_usable_password())
        self.assertEqual(u.scope, 'international-journalism')  # dekan fakulteti HEMIS'dan
        self.assertEqual(User.objects.filter(hemis_id=DEAN).count(), 1)
        self.assertEqual(access.provision(DEAN).pk, u.pk)  # qayta kirish — yangi hisob yaratilmaydi

    def test_unmapped_position_is_denied_and_closed(self):
        self.dekan.hemis_role = 'dean'
        self.dekan.save()
        u = access.provision(DEAN)
        self.dekan.hemis_role = ''
        self.dekan.save()
        self.assertIsNone(access.provision(DEAN))
        u.refresh_from_db()
        self.assertEqual(u.status, 'disabled')
        self.dekan.hemis_role = 'dean'
        self.dekan.save()
        self.assertIsNone(access.provision(DEAN))  # yopilgan hisob o'zi qayta yoqilmaydi

    def test_manual_user_keeps_role(self):
        User.objects.create(username='qolda', name='Qo‘lda', role='editor', hemis_id=TEACHER)
        self.oqituvchi.hemis_role = 'teacher'
        self.oqituvchi.save()
        self.assertEqual(access.provision(TEACHER).role, 'editor')  # qo'lda tayinlangan rolga tegilmaydi

    def test_cabinet_link_and_one_time_handoff(self):
        self.assertEqual(self.client.get('/api/me/admin-link', **bearer(DEAN)).json(), {'available': False, 'url': None})
        self.dekan.hemis_role = 'dean'
        self.dekan.save()
        res = self.client.get('/api/me/admin-link', **bearer(DEAN)).json()
        self.assertTrue(res['available'])
        path = res['url'][res['url'].index('/api/auth/hemis/handoff'):]
        first = self.client.get(path)
        self.assertEqual(first.status_code, 302)
        self.assertNotIn('kirish?hemis=', first['Location'])
        self.assertEqual(self.client.get('/api/cms/users/me').json()['user']['role'], 'dekan')
        # ikkinchi marta ishlamaydi (bir martalik) va soxta token rad etiladi
        self.assertIn('kirish?hemis=xato', self.client.get(path)['Location'])
        self.assertIn('kirish?hemis=xato', self.client.get('/api/auth/hemis/handoff?t=soxta')['Location'])
