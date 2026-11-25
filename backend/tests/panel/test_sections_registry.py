"""Yangi model qo'shilganda ruxsatlar jadvalidan tushib qolmasin.

Har kolleksiya/global yo ruxsatlar bo'limiga (`roles.SECTIONS` kaliti) bog'langan, yo ataylab «faqat superadmin» (`roles.SUPER_ONLY`).
Admin panel bo'limlarni serverdan oladi (`/users/me` → `sections`), shuning uchun SECTIONS ga qo'shilgan bo'lim jadvalda o'zi chiqadi.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

from apps.accounts import roles as rl
from apps.panel.collections import REGISTRY, Collection
from apps.panel.globals_ import GLOBALS

HINT = ("«{slug}» ruxsatlar jadvalida yo'q: unga `section = '<bo‘lim>'` bering (bo'lim backend/apps/accounts/roles.py SECTIONS "
        "va SECTION_PATHS da bo'lsin) yoki ataylab faqat superadmin uchun bo'lsa — roles.SUPER_ONLY ga qo'shing.")


class SectionsRegistryTests(SimpleTestCase):
    def test_every_collection_has_a_section_or_is_super_only(self):
        for slug, coll in REGISTRY.items():
            with self.subTest(collection=slug):
                dynamic = type(coll).section_for is not Collection.section_for  # masalan, Posts: tur bo'yicha bo'lim
                if slug in rl.SUPER_ONLY:
                    self.assertFalse(coll.section or dynamic, f'«{slug}» SUPER_ONLY da, lekin bo‘limi bor — birini olib tashlang')
                    continue
                self.assertTrue(dynamic or coll.section, HINT.format(slug=slug))
                if coll.section:
                    self.assertIn(coll.section, rl.SECTIONS, f'«{slug}».section = {coll.section!r} — SECTIONS da yo‘q')

    def test_every_global_has_a_section_or_is_super_only(self):
        for slug, g in GLOBALS.items():
            with self.subTest(global_=slug):
                if slug in rl.SUPER_ONLY:
                    self.assertFalse(g.section, f'«{slug}» SUPER_ONLY da, lekin bo‘limi bor')
                    continue
                self.assertIn(g.section, rl.SECTIONS, HINT.format(slug=slug))

    def test_super_only_names_exist(self):
        unknown = rl.SUPER_ONLY - set(REGISTRY) - set(GLOBALS)
        self.assertFalse(unknown, f'SUPER_ONLY da mavjud bo‘lmagan nomlar: {sorted(unknown)}')

    def test_every_section_is_used_and_has_admin_page(self):
        used = {c.section for c in REGISTRY.values()} | {g.section for g in GLOBALS.values()} | set(rl.POST_SECTIONS) | {'dashboard'}
        self.assertFalse(set(rl.SECTIONS) - used, 'Hech bir model ishlatmaydigan bo‘lim')
        self.assertEqual(set(rl.SECTION_PATHS), set(rl.SECTIONS), 'Har bo‘limga admin sahifasi (SECTION_PATHS) kerak')
        router = (Path(__file__).resolve().parents[3] / 'admin' / 'src' / 'router.ts')
        if router.exists():  # CI'da admin papkasi bor; alohida backend konteynerida bo'lmasligi mumkin
            paths = set(re.findall(r"path:\s*'([^']*)'", router.read_text(encoding='utf-8')))
            for key, path in rl.SECTION_PATHS.items():
                with self.subTest(section=key):
                    first = path.strip('/').split('/')[0]
                    self.assertTrue(path == '/' or any(p.split('/')[0].lstrip('/') == first for p in paths), f'{key}: {path} admin router.ts da yo‘q')

    def test_catalog_matches_sections(self):
        cat = rl.catalog()
        self.assertEqual([c['key'] for c in cat], list(rl.SECTIONS))
        self.assertTrue(all(c['label'] and c['group'] and c['path'] for c in cat))
