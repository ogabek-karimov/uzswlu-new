"""Shartnoma testi: ochiq API javoblari `frontend/docs/openapi.yaml` sxemalariga mos bo'lishi shart (4 til × barcha endpoint).

Backend javobi sxemadan chetga chiqsa — sayt (Nuxt) buziladi; bu test shuni darhol ushlaydi.
"""
import json
import unittest

from django.test import tag

from tests.support import SeededTestCase

from .openapi_check import SPEC_PATH, Validator, load_spec

try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except ImportError:  # pragma: no cover
    HAVE_YAML = False

LANGS = ('uz', 'ru', 'en', 'zh')


@tag('slow', 'contract')
@unittest.skipUnless(HAVE_YAML, 'PyYAML kerak: pip install -r requirements-dev.txt')
@unittest.skipUnless(SPEC_PATH.exists(), f'{SPEC_PATH} topilmadi')
class ContractTests(SeededTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.validator = Validator(load_spec())

    def call(self, url: str, openapi_path: str | None, expect: int = 200):
        r = self.client.get(url)
        self.assertEqual(r.status_code, expect, f'{url}: {r.content[:200]!r}')
        data = json.loads(r.content) if r.content else None
        if expect == 200 and openapi_path:
            errors = self.validator.validate(data, openapi_path, url)
            self.assertEqual(errors, [], f'{url} sxemaga mos emas')
        return data

    def check_language(self, lang: str):
        q = f'lang={lang}'
        for url, path in (
            (f'/api/home?{q}', '/home'), (f'/api/site?{q}', '/site'),
            (f'/api/staff?{q}', '/staff'), (f'/api/staff?{q}&q=yoldoshev', '/staff'),
            (f'/api/staff?{q}&group=chair&perPage=5&page=2', '/staff'), (f'/api/staff/9300?{q}', '/staff/{id}'),
            (f'/api/pages/universitet-haqida?{q}', '/pages/{slug}'),
            (f'/api/posts?{q}&type=news&sdg=11&month=2026-10&q=talaba', '/posts'),
            (f'/api/events?{q}', '/events'), (f'/api/events?{q}&month=2026-11', '/events'),
            (f'/api/leadership?{q}', '/leadership'), (f'/api/documents?{q}', '/documents'),
            (f'/api/programs?{q}&level=bachelor', '/programs'), (f'/api/programs?{q}&level=master', '/programs'),
            (f'/api/faculties?{q}', '/faculties'), (f'/api/faculties/english-philology?{q}', '/faculties/{slug}'),
            (f'/api/admission?{q}', '/admission'), (f'/api/sdg?{q}', '/sdg'),
            (f'/api/sdg/6?{q}', '/sdg/{n}'), (f'/api/sdg/1?{q}', '/sdg/{n}'),
            (f'/api/videos?{q}', '/videos'), (f'/api/contact?{q}', '/contact'),
            (f'/api/search?{q}&q=universitet', '/search'), (f'/api/search?{q}&q=rektor&type=pages', '/search'),
        ):
            with self.subTest(url=url):
                self.call(url, path)
        for kind in ('news', 'announcements', 'events'):
            with self.subTest(posts=kind):
                data = self.call(f'/api/posts?{q}&type={kind}', '/posts')
                if data['items']:
                    self.call(f'/api/posts/{kind}/{data["items"][0]["slug"]}?{q}', '/posts/{type}/{slug}')

    def test_uz(self):
        self.check_language('uz')

    def test_ru(self):
        self.check_language('ru')

    def test_en(self):
        self.check_language('en')

    def test_zh(self):
        self.check_language('zh')

    def test_not_found_responses(self):
        for url in ('/api/staff/99999999', '/api/pages/yoq-sahifa', '/api/posts/news/yoq', '/api/sdg/18', '/api/faculties/yoq'):
            with self.subTest(url=url):
                self.call(url, None, 404)

    def test_validator_catches_real_mismatches(self):
        """Tekshiruvchining o'zi ishlayotganini isbotlaydi (aks holda «hammasi mos» ma'nosiz)."""
        data = self.call('/api/contact?lang=uz', '/contact')
        broken = dict(data)
        broken.pop(next(iter(broken)))
        self.assertTrue(self.validator.validate(broken, '/contact', 'broken'), 'majburiy maydon yo‘qolishi sezilmadi')
        broken = {**data, 'recipients': 'matn'}
        self.assertTrue(self.validator.validate(broken, '/contact', 'broken'), 'tur xatosi sezilmadi')
