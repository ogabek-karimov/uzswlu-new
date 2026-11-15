from tests.support import SeededTestCase


class PostNeighborsTests(SeededTestCase):
    """Post sahifasidagi «Oldingi / Keyingi»: shu turdagi qo'shni postlar, vaqt bo'yicha zanjir."""

    def test_prev_next_chain_is_consistent(self):
        rows = self.client.get('/api/posts?type=news&lang=uz&limit=50').json()
        items = rows['items'] if isinstance(rows, dict) else rows
        self.assertGreaterEqual(len(items), 3)
        slugs = [x['slug'] for x in items]  # yangilari birinchi
        mid = self.client.get(f'/api/posts/news/{slugs[1]}?lang=uz').json()
        self.assertEqual(mid['next']['slug'], slugs[0])    # keyingi = yangiroq
        self.assertEqual(mid['prev']['slug'], slugs[2])    # oldingi = eskiroq
        self.assertEqual(mid['next']['type'], 'news')
        newest = self.client.get(f'/api/posts/news/{slugs[0]}?lang=uz').json()
        self.assertIsNone(newest['next'])
        self.assertIsNotNone(newest['prev'])
