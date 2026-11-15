from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

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
