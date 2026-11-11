"""Qo'llanma (docs/) eskirmasligi: avtomatik fayllar kodga mos, havolalar/anchorlar/yo'llar/buyruqlar mavjud.

Hujjatni yangilash: `cd backend && python manage.py build_docs`. Ildiz papkada docs/ bo'lmasa (masalan, faqat backend/ nusxasi
konteynerga olingan bo'lsa) testlar o'tkazib yuboriladi."""
import re
import unittest
from pathlib import Path

from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from apps.core import docsgen

DOCS = docsgen.DOCS
REPO = docsgen.REPO
MD_FILES = sorted(DOCS.glob('*.md')) if DOCS.is_dir() else []

LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)\)')
TICKS = re.compile(r'`([^`\n]+)`')
ROOTS = ('backend/', 'frontend/', 'admin/', 'scripts/', 'docs/', '.github/')
# foydalanuvchi o'zi yaratadigan / ish vaqtida paydo bo'ladigan / namuna sifatida keltirilgan yo'llar
RUNTIME = re.compile(r'(\.env|backend/backups/.*|frontend/i18n/locales/kk\.json|docs/NN-nom\.md)$')
MANAGE = re.compile(r'manage\.py\s+([a-z_]+)')


def anchors(path: Path) -> set[str]:
    """Fayldagi sarlavhalarning GitHub-uslubidagi anchorlari (kod bloklaridan tashqari)."""
    out, fenced = set(), False
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('```'):
            fenced = not fenced
        elif not fenced and (m := re.match(r'#{1,4}\s+(.*)', line)):
            out.add(docsgen.slug(m.group(1)))
    return out


def prose(path: Path):
    """Kod bloklarisiz matn qatorlari (kod bloklarida namunaviy/yaroqsiz yo'llar bo'lishi mumkin)."""
    fenced = False
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('```'):
            fenced = not fenced
        elif not fenced:
            yield n, line


@unittest.skipUnless(MD_FILES, 'docs/ papkasi yo‘q')
class DocsFreshnessTests(SimpleTestCase):
    def test_generated_files_match_code(self):
        stale = docsgen.write_all(check=True)
        self.assertEqual(stale, [], f'Eskirgan: {stale}. Yangilang: cd backend && python manage.py build_docs')

    def test_build_docs_check_command(self):
        try:
            call_command('build_docs', '--check')
        except CommandError as e:
            self.fail(str(e))

    def test_every_guide_is_listed_in_readme_map(self):
        readme = (DOCS / 'README.md').read_text(encoding='utf-8')
        for p in MD_FILES:
            if p.name != 'README.md':
                self.assertIn(f'({p.name})', readme, f'{p.name} docs/README.md «Hujjatlar xaritasi»da yo‘q')


@unittest.skipUnless(MD_FILES, 'docs/ papkasi yo‘q')
class DocsLinksTests(SimpleTestCase):
    def test_relative_links_and_anchors_resolve(self):
        bad = []
        for p in MD_FILES:
            own = anchors(p)
            for n, line in prose(p):
                for href in LINK.findall(line):
                    if re.match(r'(https?:|mailto:)', href):
                        continue
                    target, _, frag = href.partition('#')
                    dest = p if not target else (p.parent / target).resolve()
                    if not dest.exists():
                        bad.append(f'{p.name}:{n} → {href} (fayl yo‘q)')
                    elif frag and dest.suffix == '.md' and frag not in (own if dest == p else anchors(dest)):
                        bad.append(f'{p.name}:{n} → {href} (anchor yo‘q)')
        self.assertEqual(bad, [])

    def test_backticked_repo_paths_exist(self):
        bad = []
        for p in MD_FILES:
            for n, line in prose(p):
                for tok in TICKS.findall(line):
                    tok = re.sub(r':\d+$', '', tok.strip().split(' ')[0].rstrip(',.;:'))   # `settings.py:283` — qator raqami
                    if not tok.startswith(ROOTS) or any(c in tok for c in '*<>{}$…|') or '...' in tok or RUNTIME.search(tok):
                        continue
                    if not (REPO / tok.split('::')[0].split('#')[0]).exists():
                        bad.append(f'{p.name}:{n} → {tok}')
        self.assertEqual(bad, [], 'Hujjatda tilga olingan yo‘llar topilmadi')

    def test_manage_py_commands_exist(self):
        known, bad = set(get_commands()), []
        for p in MD_FILES:
            for n, line in prose(p):
                for tok in TICKS.findall(line):
                    for cmd in MANAGE.findall(tok):
                        if cmd not in known:
                            bad.append(f'{p.name}:{n} → manage.py {cmd}')
        self.assertEqual(bad, [], 'Hujjatda yo‘q buyruq tilga olingan')

    def test_manage_py_commands_in_code_blocks_exist(self):
        known, bad = set(get_commands()), []
        for p in MD_FILES:
            fenced = False
            for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
                if line.startswith('```'):
                    fenced = not fenced
                elif fenced:
                    bad += [f'{p.name}:{n} → manage.py {c}' for c in MANAGE.findall(line) if c not in known]
        self.assertEqual(bad, [])


@unittest.skipUnless(MD_FILES, 'docs/ papkasi yo‘q')
class ChangelogTests(SimpleTestCase):
    """docs/13-yangiliklar.md: sanalar tartibli (yangisi tepada), har kunda kamida bitta punkt, eng so'nggi yozuv eskirmagan."""

    def setUp(self):
        path = DOCS / '13-yangiliklar.md'
        self.assertTrue(path.exists(), 'docs/13-yangiliklar.md yo‘q')
        self.text = path.read_text(encoding='utf-8')
        self.days = re.findall(r'^## (\d{4}-\d{2}-\d{2})\s*$', self.text, re.M)

    def test_dates_descending_and_unique(self):
        self.assertTrue(self.days, 'Hech bir «## YYYY-MM-DD» sarlavhasi yo‘q')
        self.assertEqual(self.days, sorted(set(self.days), reverse=True), 'Sanalar kamayish tartibida va takrorsiz bo‘lsin')

    def test_every_day_has_entries(self):
        for block in re.split(r'^## \d{4}-\d{2}-\d{2}\s*$', self.text, flags=re.M)[1:]:
            self.assertRegex(block, r'(?m)^- \*\*', 'Har kunda kamida bitta «- **Toifa:** …» punkt bo‘lsin')

    def test_readme_links_changelog(self):
        self.assertIn('(13-yangiliklar.md)', (DOCS / 'README.md').read_text(encoding='utf-8'))
