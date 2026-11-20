"""Lokal sinov kirishi: faqat DEBUG + STAFF_DEV_LOGIN + HEMIS ulanmagan bo'lganda ishlaydi."""
from django.test import TestCase, override_settings

from apps.accounts.models import StaffSession

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
        res = self.client.get(URL)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Dekan', res.content.decode())
        res = self.client.get(URL + '&as=8654')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res['Location'], '/dashboard')
        self.assertEqual(StaffSession.objects.filter(hemis_id='8654').count(), 1)
        self.assertEqual(self.client.get(URL + '&as=0000').status_code, 404)
