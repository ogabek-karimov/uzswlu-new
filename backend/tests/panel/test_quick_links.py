import re
from pathlib import Path

from apps.api.builders_site import home_out, quick_links_out
from apps.content.models import QuickLink
from apps.content.quick_links import ICON_NAMES, valid_url
from tests.panel.test_collections import PanelBase

ROOT = Path(__file__).resolve().parents[3]


class QuickLinkValidationTests(PanelBase):
    def test_url_rules(self):
        for ok in ('/career', '/site/reception', 'https://play.google.com/store/apps/details?id=uz.x&pcampaignid=web_share', 'http://a.uz'):
            self.assertTrue(valid_url(ok), ok)
        for bad in ('', 'javascript:alert(1)', '//evil.example', 'ftp://a.uz', 'career', 'data:text/html,x', '/a b'):
            self.assertFalse(valid_url(bad), bad)

    def test_icon_lists_are_in_sync(self):
        """Admin sahifasi va sayt komponentidagi ikonkalar backend ro'yxati bilan bir xil (aks holda ikonka ko'rinmay qoladi)."""
        for rel in ('admin/src/pages/QuickLinksPage.vue', 'frontend/app/components/home/QuickLinks.vue'):
            src = (ROOT / rel).read_text(encoding='utf-8')
            self.assertEqual(set(re.findall(r"'((?:lucide|app):[\w-]+)'", src)) - {'lucide:arrow-up-right', 'lucide:arrow-right'}, set(ICON_NAMES), rel)


class QuickLinkPanelTests(PanelBase):
    def test_seeded_cards_exist(self):
        self.assertGreaterEqual(QuickLink.objects.count(), 6)
        self.assertTrue(any(q['url'] == '/career' for q in quick_links_out('uz')))

    def test_seeded_cards_point_to_own_pages(self):
        urls = {q['url'] for q in quick_links_out('uz')}
        self.assertTrue({'/virtual-qabulxona', '/korporativ-pochta'} <= urls, urls)
        self.assertFalse({'/site/reception', '/services/mail'} & urls)
        for page in ('virtual-qabulxona', 'korporativ-pochta'):
            self.assertTrue((ROOT / f'frontend/app/pages/{page}.vue').exists(), page)

    def test_create_and_expose(self):
        QuickLink.objects.all().delete()
        r = self.send('post', '/api/cms/quick-links', {'icon': 'lucide:book-a', 'url': 'https://play.google.com/store/apps/details?id=uz.soft.aktlugat23',
                                                         'title': {'uz': 'AKT izohli lug‘ati', 'en': 'ICT glossary'}, 'text': {'uz': 'Mobil ilova'}, 'order': 1})
        self.assertEqual(r.status_code, 201, r.content[:300])
        (uz,) = quick_links_out('uz')
        self.assertEqual((uz['title'], uz['external'], uz['text']), ('AKT izohli lug‘ati', True, 'Mobil ilova'))
        (en,) = quick_links_out('en')
        self.assertEqual((en['title'], en['text']), ('ICT glossary', 'Mobil ilova'))  # izoh tarjimasi yo‘q — o‘zbekcha
        self.assertEqual(home_out('uz')['quickLinks'][0]['icon'], 'lucide:book-a')

    def test_hidden_and_order(self):
        QuickLink.objects.all().delete()
        a = QuickLink.objects.create(url='/a', title={'uz': 'A'}, order=2)
        QuickLink.objects.create(url='/b', title={'uz': 'B'}, order=1)
        QuickLink.objects.create(url='/c', title={'uz': 'C'}, order=3, visible=False)
        self.assertEqual([q['title'] for q in quick_links_out('uz')], ['B', 'A'])
        self.assertFalse(quick_links_out('uz')[1]['external'])
        self.assertEqual(a.title['uz'], 'A')

    def test_rejects_bad_input(self):
        base = {'icon': 'lucide:globe', 'url': '/x', 'title': {'uz': 'X'}}
        for patch in ({'url': 'javascript:alert(1)'}, {'icon': 'lucide:nope'}, {'title': {'ru': 'Х'}}):
            with self.subTest(patch=patch):
                r = self.send('post', '/api/cms/quick-links', {**base, **patch})
                self.assertEqual(r.status_code, 400, r.content[:200])
