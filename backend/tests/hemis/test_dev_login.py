"""Lokal sinov kirishi: faqat DEBUG + STAFF_DEV_LOGIN + HEMIS ulanmagan bo'lganda ishlaydi."""
from django.conf import settings
from django.test import TestCase, override_settings

from apps.accounts.models import Role, StaffSession
from tests.support import give_cabinet_role

URL = '/api/auth/hemis/login?next=cabinet'


class DevLoginTests(TestCase):
    @override_settings(DEBUG=False, STAFF_DEV_LOGIN=True)
    def test_off_without_debug(self):
        self.assertEqual(self.client.get(URL).status_code, 503)

    @override_settings(DEBUG=True, STAFF_DEV_LOGIN=False)
    def test_off_without_flag(self):
        self.assertEqual(self.client.get(URL).status_code, 503)

    @override_settings(DEBUG=True, STAFF_DEV_LOGIN=True)
    def test_picker_and_login(self):
        # Ro'yxat — admin HEMIS ID biriktirgan hisoblar, rol bo'yicha (HEMIS lavozimi o'zi kirish bermaydi)
        page = self.client.get(URL).content.decode()
        self.assertIn('Hali hech kimga rol berilmagan', page)
        self.assertIn('Rolsiz xodim', page)  # rolsiz xodim ham kiradi — faqat Dashboard va KPI
        Role.objects.create(slug='matbuot', name='Matbuot xizmati', permissions={'news': 'write'})
        give_cabinet_role('8654', role='matbuot')
        res = self.client.get(URL)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Matbuot xizmati', res.content.decode())
        self.assertNotIn('<b>Dekan</b>', res.content.decode())
        res = self.client.get(URL + '&as=8654')
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res['Location'].startswith(settings.SITE_URL + '/api/dev-login?token='))
        self.assertEqual(StaffSession.objects.filter(hemis_id='8654').count(), 1)
        self.assertEqual(self.client.get(URL + '&as=0000').status_code, 404)  # bunday xodim yo'q
