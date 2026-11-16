from apps.content.video_tour import parse_video
from apps.api.builders_site import video_tour_out
from tests.panel.test_collections import PanelBase


class ParseVideoTests(PanelBase):
    def test_supported_links(self):
        self.assertEqual(parse_video('https://www.youtube.com/watch?v=dQw4w9WgXcQ')[0], 'youtube')
        self.assertEqual(parse_video('https://youtu.be/dQw4w9WgXcQ')[1], 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0&autoplay=1')
        self.assertEqual(parse_video('https://vimeo.com/123456789')[0], 'vimeo')
        self.assertEqual(parse_video('https://cdn.example.uz/tur.mp4'), ('file', 'https://cdn.example.uz/tur.mp4'))

    def test_rejects_unsafe_links(self):
        for bad in ('', 'javascript:alert(1)', 'http://cdn.example.uz/tur.mp4', 'https://evil.example/page', 'https://youtube.com.evil.uz/watch?v=dQw4w9WgXcQ'):
            with self.subTest(url=bad):
                self.assertIsNone(parse_video(bad))


class VideoTourPanelTests(PanelBase):
    def test_empty_means_no_tour(self):
        self.assertIsNone(video_tour_out('uz'))

    def test_save_and_expose(self):
        r = self.send('post', '/api/cms/globals/video-tour', {'url': 'https://youtu.be/dQw4w9WgXcQ', 'title': {'uz': 'Universitet bo‘ylab sayohat'}, 'text': {'uz': '3 daqiqa'}})
        self.assertEqual(r.status_code, 200, r.content[:200])
        out = video_tour_out('uz')
        self.assertEqual((out['kind'], out['title'], out['text']), ('youtube', 'Universitet bo‘ylab sayohat', '3 daqiqa'))

    def test_hidden_tour_is_null(self):
        self.send('post', '/api/cms/globals/video-tour', {'url': 'https://youtu.be/dQw4w9WgXcQ', 'visible': False})
        self.assertIsNone(video_tour_out('uz'))

    def test_bad_url_rejected(self):
        r = self.send('post', '/api/cms/globals/video-tour', {'url': 'https://evil.example/x'})
        self.assertEqual(r.status_code, 400, r.content[:200])
