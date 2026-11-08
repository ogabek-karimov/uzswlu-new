"""API_TOKEN almashtirish va production sozlama ogohlantirishlari."""

from django.test import Client, override_settings
from tests.support import HOST, Base, api


class TokenRotationAndChecksTests(Base):
    def test_old_and_new_api_token_both_work_during_rotation(self):
        with override_settings(API_TOKEN='new-token-value,old-token-value'):
            for t in ('new-token-value', 'old-token-value'):
                self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION=f'Bearer {t}').status_code, 200)
            self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION='Bearer third').status_code, 403)
            self.assertEqual(Client(**HOST).get('/api/faculties', HTTP_AUTHORIZATION='Bearer new-token-value,old-token-value').status_code, 403)

    def test_production_checks_warn_about_weak_settings(self):
        from apps.core.checks import security_settings
        with override_settings(DEBUG=False, API_TOKEN='short', API_DOCS_PUBLIC=True, ALLOWED_HOSTS=['*']):
            ids = {w.id for w in security_settings(None)}
        self.assertTrue({'uzswlu.W002', 'uzswlu.W004', 'uzswlu.W005', 'uzswlu.W006'} <= ids)
        with override_settings(DEBUG=True):
            self.assertEqual(security_settings(None), [])
