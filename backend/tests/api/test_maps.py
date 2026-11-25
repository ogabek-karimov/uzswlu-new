from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from apps.structure.maps import map_embed, map_link, parse_coords


class MapsTests(SimpleTestCase):
    def test_embed_is_yandex_with_marker_lng_first(self):
        url = map_embed('41.285765, 69.203892', 'Toshkent', 'uz')
        self.assertTrue(url.startswith('https://yandex.com/map-widget/v1/?'))
        self.assertIn('ll=69.203892,41.285765', url)
        self.assertIn('pt=69.203892,41.285765,pm2rdl', url)

    def test_embed_and_link_fall_back_to_address(self):
        self.assertIn('text=Toshkent%20sh.', map_embed('', 'Toshkent sh.', 'ru'))
        self.assertEqual(map_link('', 'Toshkent sh.'), 'https://yandex.com/maps/?text=Toshkent%20sh.')

    def test_link_is_yandex(self):
        self.assertTrue(map_link('41.2, 69.2', 'x').startswith('https://yandex.com/maps/?ll=69.2,41.2'))

    def test_parse_yandex_link(self):
        self.assertEqual(parse_coords('https://yandex.com/maps/?ll=69.203892%2C41.285765&z=17'), '41.285765, 69.203892')
        self.assertEqual(parse_coords('https://yandex.uz/maps/?pt=69.203892,41.285765&z=17'), '41.285765, 69.203892')

    def test_parse_google_and_plain_still_work(self):
        self.assertEqual(parse_coords('https://www.google.com/maps/@41.286038,69.194908,17z'), '41.286038, 69.194908')
        self.assertEqual(parse_coords('41.286038, 69.194908'), '41.286038, 69.194908')
        self.assertEqual(parse_coords(''), '')
        with self.assertRaises(ValidationError):
            parse_coords('xarita')


class SiteCampusMapTests(TestCase):
    """Footer QR kodi `/api/site` dagi bosh binoning `mapUrl` ini kodlaydi — u binoning aniq nuqtasiga olib borishi kerak."""

    def test_site_campuses_have_exact_map_link(self):
        from apps.api.builders_site import site_out
        from apps.structure.models import Campus
        Campus.objects.create(key='main', name={'uz': 'Bosh bino'}, address={'uz': 'Toshkent'}, coords='41.286035, 69.193875',
                              map_url='https://www.google.com/maps/search/?api=1&query=Toshkent', order=1)
        Campus.objects.create(key='nopoint', name={'uz': 'Boshqa'}, address={'uz': 'Lutfiy 8'}, order=2)
        out = {c['id']: c for c in site_out('uz')['campuses']}
        self.assertEqual(out['main']['mapUrl'], 'https://yandex.com/maps/?ll=69.193875,41.286035&z=17&pt=69.193875,41.286035,pm2rdl')
        self.assertEqual(out['nopoint']['mapUrl'], 'https://yandex.com/maps/?text=Lutfiy%208')   # nuqta yo'q — manzil bo'yicha

    def test_migration_points_are_the_seed_points(self):
        """Yangi bazaga (seed) va mavjud bazaga (migratsiya) bir xil aniq nuqtalar tushadi."""
        import importlib
        import json
        from pathlib import Path
        from django.conf import settings
        fix = importlib.import_module('apps.structure.migrations.0012_campus_exact_coords').FIX
        seed = json.loads((Path(settings.BASE_DIR) / 'seed_data' / 'mock-data.json').read_text(encoding='utf-8'))
        points = {c['id']: c['coords'] for c in seed['contact']['campuses'] if c.get('coords')}
        self.assertEqual(points, {k: new for k, (old, new) in fix.items()})
