from django.test import TestCase

from apps.api.builders_site import site_out
from apps.core.models import SiteSettings


class GlossaryAppUrlTests(TestCase):
    def test_empty_by_default(self):
        self.assertIsNone(site_out('uz')['glossaryApp'])

    def test_exposed_when_set(self):
        s = SiteSettings.load()
        s.glossary_app_url = 'https://play.google.com/store/apps/details?id=uz.example.akt'
        s.save()
        self.assertEqual(site_out('uz')['glossaryApp'], 'https://play.google.com/store/apps/details?id=uz.example.akt')
