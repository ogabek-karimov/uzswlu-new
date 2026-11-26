from django.test import TestCase


class ShowcaseIntroPlainTests(TestCase):
    """«Kirish gapi» — oddiy matn: ichiga HTML tushib qolsa saytda teglar ko'rinmasin (Kelajakka qadam markazi)."""

    def test_intro_html_is_stripped(self):
        from apps.api.builders_site import showcase_out
        data = {'blocks': [{'intro': {'uz': '<h2>Kelajakka qadam</h2><p><strong>Maqsad:</strong> A &amp; B</p>'}, 'outro': {'uz': 'Oddiy gap'}}]}
        block = showcase_out(data, 'uz')[0]
        self.assertEqual(block['intro'], 'Kelajakka qadam Maqsad: A & B')
        self.assertEqual(block['outro'], 'Oddiy gap')
