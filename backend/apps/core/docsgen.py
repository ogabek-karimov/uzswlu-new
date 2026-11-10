"""Loyiha qo'llanmasi (docs/) generatori — faqat Python.

  docs/*.md           — qo'lda yoziladigan qo'llanmalar (`01-boshlash.md`, …)
  docs/reference.md   — KODDAN AVTOMATIK yig'iladi: rollar jadvali, manzillar, buyruqlar, sozlamalar, testlar xaritasi, tekshiruvlar,
                        admin sahifalari, frontend marshrutlari. Qo'lda tahrirlamang — `python manage.py build_docs`.
  docs/index.html     — hamma .md dan yig'iladigan bitta fayl: qidiruv, chap menyu, qorong'i rejim; brauzerda ikki marta bosib ochiladi.

Hujjat kod bilan hamfikr bo'lishini `tests/core/test_docs.py` kafolatlaydi: reference/index eskirgan bo'lsa, havola yoki
`backend/...` yo'li, `manage.py <buyruq>` mavjud bo'lmasa test yiqiladi.
"""
import ast
import html
import re
from pathlib import Path

from django.conf import settings

REPO = Path(settings.BASE_DIR).parent
DOCS = REPO / 'docs'
GENERATED_NOTE = '> ⚙️ **Bu fayl koddan avtomatik yig‘iladi** — qo‘lda tahrirlamang: `cd backend && python manage.py build_docs`.\n'


# ════════════════════════════════════════════════════════════ reference.md
def _first_line(text: str | None) -> str:
    return (text or '').strip().split('\n')[0].strip()


def _esc(value) -> str:
    return str(value).replace('|', '\\|').replace('\n', ' ')


def table(head: list[str], rows: list[list]) -> str:
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join('---' for _ in head) + '|']
    out += ['| ' + ' | '.join(_esc(c) for c in row) + ' |' for row in rows]
    return '\n'.join(out) + '\n'


def roles_section() -> str:
    from apps.accounts.models import User
    from apps.panel.collections import REGISTRY
    from apps.panel.globals_ import GLOBALS
    roles = [r for r, _ in User.ROLES]
    letters = {'read': 'R', 'create': 'C', 'update': 'U', 'delete': 'D'}

    def cell(access: dict, role: str) -> str:
        out = ''.join(letters[a] for a in ('read', 'create', 'update', 'delete') if a in letters and role in (access.get(a) or ()))
        return out or '—'
    rows, notes = [], []
    for slug, c in sorted(REGISTRY.items()):
        rows.append([f'`{slug}`'] + [cell(c.access, r) for r in roles])
        for action, text in (c.rules or {}).items():
            notes.append(f'- `{slug}` · **{action}**: {text}')
    grows = []
    for slug, g in sorted(GLOBALS.items()):
        a = g.access
        grows.append([f'`{slug}` (global)'] + [''.join(x for x, k in (('R', 'read'), ('U', 'update')) if a.get(k) is None or r in (a.get(k) or ())) or '—' for r in roles])
    text = '### Rol × kolleksiya jadvali\n\n'
    text += '`R` o‘qish · `C` yaratish · `U` tahrirlash · `D` o‘chirish · `—` ruxsat yo‘q. Obyekt darajasidagi qo‘shimcha cheklovlar jadval ostida.\n\n'
    text += table(['Kolleksiya'] + [f'`{r}`' for r in roles], rows + grows)
    if notes:
        text += '\n**Obyekt darajasidagi qoidalar** (rol jadvalidan tashqari):\n\n' + '\n'.join(notes) + '\n'
    return text


def endpoints_section() -> str:
    from django.urls import get_resolver

    def walk(patterns, prefix=''):
        for p in patterns:
            if hasattr(p, 'url_patterns'):
                yield from walk(p.url_patterns, prefix + str(p.pattern))
            else:
                yield prefix + str(p.pattern), p.callback
    groups: dict[str, list] = {'Ochiq sayt API (`/api/…`)': [], 'Payload bilan mos (`/api/site/…`)': [], 'Admin panel (`/api/cms/…`)': [],
                               'HEMIS kirish (`/api/auth/hemis/…`)': [], 'Boshqa': []}
    for url, cb in walk(get_resolver().url_patterns):
        cls = getattr(cb, 'cls', None) or getattr(cb, 'view_class', None)
        name = cls.__name__ if cls else getattr(cb, '__name__', '?')
        mod = (cls.__module__ if cls else cb.__module__).replace('.', '/') + '.py'
        scope = getattr(cls, 'throttle_scope', '') if cls else ''
        if url.startswith('api/cms/'):
            key = 'Admin panel (`/api/cms/…`)'
        elif url.startswith('api/site/'):
            key = 'Payload bilan mos (`/api/site/…`)'
        elif url.startswith('api/auth/hemis/'):
            key = 'HEMIS kirish (`/api/auth/hemis/…`)'
        elif url.startswith('api/') and not url.startswith(('api/docs', 'api/redoc', 'api/schema', 'api/media')):
            key = 'Ochiq sayt API (`/api/…`)'
        elif url.startswith(('media/', 'static/')) or url.startswith('^media'):
            continue
        else:
            key = 'Boshqa'
        groups[key].append([f'`/{url}`', f'`{name}`', f'`{mod}`', scope and f'`{scope}`'])
    text = '### Manzillar (URL xaritasi)\n\nBatafsil parametr va javoblar — Swagger: `http://localhost:8000/api/docs/`. Pastda: manzil → view → fayl → so‘rov cheklovi doirasi (`THROTTLE_*`).\n'
    for title, rows in groups.items():
        if rows:
            text += f'\n#### {title}\n\n' + table(['Manzil', 'View', 'Fayl', 'Cheklov'], sorted(rows))
    return text


def commands_section() -> str:
    from django.core.management import get_commands, load_command_class
    rows = []
    for name, app in sorted(get_commands().items()):
        if not str(app).startswith('apps.'):
            continue
        cmd = load_command_class(app, name)
        rows.append([f'`python manage.py {name}`', _first_line(cmd.help), f'`{app.replace(".", "/")}/management/commands/{name}.py`'])
    return '### `manage.py` buyruqlari (loyihaniki)\n\nDocker\'da: `docker compose exec backend python manage.py <buyruq>`. Parametrlar: `python manage.py <buyruq> --help`.\n\n' + \
        table(['Buyruq', 'Nima qiladi', 'Fayl'], rows)


def _env_calls(path: Path) -> dict[str, tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            fname = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ''
            if fname in ('env', 'env_bool', 'env_list') and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                default = ast.unparse(node.args[1]) if len(node.args) > 1 else "''"
                out.setdefault(node.args[0].value, (default, node.lineno))
    return out


def parse_env_example(path: Path) -> list[tuple[str, str, str, bool]]:
    """`.env.example` → [(bo'lim, NOM, qiymat, izoh)] — izoh: o'zidan oldingi `#` qatorlari."""
    rows, section, comment = [], '', []
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line:
            comment = []
            continue
        m = re.match(r'^#\s*---\s*(.+?)\s*---?\s*$', line)
        if m:
            section, comment = m.group(1), []
            continue
        var = re.match(r'^(#\s*)?([A-Z][A-Z0-9_]+)=(.*)$', line)
        if var:
            rows.append((section, var.group(2), var.group(3), ' '.join(comment), bool(var.group(1))))
            comment = []
        elif line.startswith('#'):
            comment.append(line.lstrip('# ').strip())
    return rows


def env_section() -> str:
    text = '### Sozlamalar (.env)\n\nFayllar: `backend/.env` (namuna: `backend/.env.example`), `.env.docker` (namuna: `.env.docker.example`, faqat PostgreSQL), `frontend/.env` (namuna: `frontend/.env.example`), ildiz `.env` (ixtiyoriy: portlar).\n'
    documented: set[str] = set()
    for title, path in (('Backend — `backend/.env.example`', REPO / 'backend/.env.example'), ('PostgreSQL — `.env.docker.example`', REPO / '.env.docker.example'),
                        ('Frontend — `frontend/.env.example`', REPO / 'frontend/.env.example')):
        if not path.exists():
            continue
        rows = parse_env_example(path)
        documented |= {r[1] for r in rows}
        text += f'\n#### {title}\n\n' + table(['O‘zgaruvchi', 'Namuna', 'Izoh', 'Holat'], [
            [f'`{n}`', f'`{v}`' if v else '*(bo‘sh)*', c, 'ixtiyoriy (izohda)' if opt else ''] for _, n, v, c, opt in rows])
    settings_py = REPO / 'backend/config/settings.py'
    extra = {k: v for k, v in _env_calls(settings_py).items() if k not in documented}
    text += '\n#### Namunada ko‘rsatilmagan, lekin `settings.py` o‘qiydigan o‘zgaruvchilar\n\nStandart qiymat bilan ishlaydi; kerak bo‘lsa `backend/.env` ga qo‘shing.\n\n'
    text += table(['O‘zgaruvchi', 'Standart', 'Qayerda'], [[f'`{k}`', f'`{v[0]}`', f'`backend/config/settings.py:{v[1]}`'] for k, v in sorted(extra.items())])
    return text


def checks_section() -> str:
    tree = ast.parse((REPO / 'backend/apps/core/checks.py').read_text(encoding='utf-8'))
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'Warning' and node.args:
            ident = next((kw.value.value for kw in node.keywords if kw.arg == 'id' and isinstance(kw.value, ast.Constant)), '')
            msg = node.args[0].value if isinstance(node.args[0], ast.Constant) else ast.unparse(node.args[0])
            hint = next((kw.value.value for kw in node.keywords if kw.arg == 'hint' and isinstance(kw.value, ast.Constant)), '')
            rows.append([f'`{ident}`', msg, hint])
    return ('### Production tekshiruvlari (`python manage.py check`)\n\nDEBUG o‘chiq bo‘lganda ishga tushishda chiqadi (Docker\'da `docker compose logs backend`). Hammasi yo‘qolishi kerak.\n\n'
            + table(['Kod', 'Nima noto‘g‘ri', 'Qanday tuzatiladi'], sorted(rows)))


def tests_section() -> str:
    root = REPO / 'backend/tests'
    rows, total = [], 0
    for path in sorted(root.rglob('test_*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        n = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith('test'))
        total += n
        slow = ' · `slow`' if "tag('slow')" in path.read_text(encoding='utf-8') else ''
        rows.append([f'`backend/tests/{path.relative_to(root).as_posix()}`', n, _first_line(ast.get_docstring(tree)) + slow])
    return (f'### Backend testlari xaritasi ({total} ta test)\n\nIshga tushirish: `cd backend && python manage.py test --parallel` · bitta fayl: `python manage.py test tests.security.test_files`.\n\n'
            + table(['Fayl', 'Testlar', 'Nimani tekshiradi'], rows))


def models_section() -> str:
    from django.apps import apps
    rows = []
    for cfg in apps.get_app_configs():
        if cfg.name.startswith('apps.'):
            for m in cfg.get_models():
                rows.append([f'`{cfg.name.split(".")[-1]}`', f'`{m.__name__}`', str(m._meta.verbose_name), f'`{cfg.name.replace(".", "/")}/models.py`'])
    return '### Ma\'lumotlar modellari\n\n' + table(['Ilova', 'Model', 'Nomi', 'Fayl'], rows)


def middleware_section() -> str:
    from django.conf import settings as s
    return '### Middleware tartibi (yuqoridan pastga)\n\n' + '\n'.join(f'{i}. `{m}`' for i, m in enumerate(s.MIDDLEWARE, 1)) + '\n'


def admin_routes_section() -> str:
    src = (REPO / 'admin/src/router.ts').read_text(encoding='utf-8')
    rows = []
    for m in re.finditer(r"\{ path: '([^']*)', name: '([^']+)', component: \(\) => import\('\./pages/(\w+\.vue)'\), meta: \{([^}]*)\}", src):
        path, name, comp, meta = m.groups()
        roles = re.search(r"roles: \[([^\]]*)\]", meta)
        who = 'faqat `superadmin`' if 'superOnly' in meta else (roles.group(1).replace("'", '`') if roles else 'hamma kirgan xodim')
        rows.append([f'`/{path}`', f'`admin/src/pages/{comp}`', who])
    return '### Admin panel sahifalari\n\nMarshrut → fayl → kim ko‘radi (`admin/src/router.ts`; server tomonidagi ruxsat alohida — yuqoridagi jadval).\n\n' + table(['Manzil', 'Fayl', 'Rollar'], rows)


def frontend_section() -> str:
    pages, api = [], []
    for p in sorted((REPO / 'frontend/app/pages').rglob('*.vue')):
        rel = p.relative_to(REPO / 'frontend/app/pages').with_suffix('').as_posix()
        route = '/' + re.sub(r'/?index$', '', re.sub(r'\[([^\]]+)\]', r':\1', rel))
        pages.append([f'`{route}`', f'`frontend/app/pages/{p.relative_to(REPO / "frontend/app/pages").as_posix()}`'])
    for p in sorted((REPO / 'frontend/server/api').rglob('*.ts')):
        rel = p.relative_to(REPO / 'frontend/server/api').as_posix()
        m = re.match(r'^(.*?)(?:\.(get|post|put|patch|delete))?\.ts$', rel)
        route = '/api/' + re.sub(r'/?index$', '', re.sub(r'\[([^\]]+)\]', r':\1', m.group(1)))
        api.append([f'`{(m.group(2) or "any").upper()} {route}`', f'`frontend/server/api/{rel}`'])
    return ('### Frontend (Nuxt)\n\n#### Sahifalar (til prefiksi: `/ru`, `/en`, `/zh`; o‘zbekcha — prefikssiz)\n\n' + table(['Marshrut', 'Fayl'], pages)
            + '\n#### Nuxt server qatlami (brauzer → shu yerga → backend)\n\n' + table(['Manzil', 'Fayl'], api))


def modules_section() -> str:
    rows = []
    for path in sorted(list((REPO / 'backend/apps').glob('*/*.py')) + list((REPO / 'backend/config').glob('*.py'))):
        if path.name in ('__init__.py', 'apps.py', 'asgi.py', 'wsgi.py') or '/migrations/' in path.as_posix():
            continue
        doc = _first_line(ast.get_docstring(ast.parse(path.read_text(encoding='utf-8'))))
        rows.append([f'`{path.relative_to(REPO).as_posix()}`', doc or '—'])
    return '### Backend fayllar xaritasi (qaysi fayl nima qiladi)\n\nHar faylning boshidagi izohdan olinadi.\n\n' + table(['Fayl', 'Vazifasi'], rows)


def build_reference() -> str:
    parts = ['# Avtomatik ma’lumotnoma\n', GENERATED_NOTE,
             'Bu sahifa **koddan** yig‘iladi, shuning uchun doim haqiqatga mos: rollar, manzillar, buyruqlar, sozlamalar, testlar.\n',
             roles_section(), commands_section(), env_section(), checks_section(), endpoints_section(), admin_routes_section(), frontend_section(),
             modules_section(), tests_section(), models_section(), middleware_section()]
    return '\n'.join(parts).rstrip() + '\n'


# ════════════════════════════════════════════════════════════ markdown → html
def slug(text: str) -> str:
    """GitHub bilan bir xil: kichik harf, tinish belgilari tashlanadi, bo'shliq → `-`."""
    text = re.sub(r'`|\*\*', '', text).strip().lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'\s', '-', text)


def inline(text: str, doc: str) -> str:
    codes: list[str] = []

    def stash(m):
        codes.append(f'<code>{html.escape(m.group(1))}</code>')
        return f'\0{len(codes) - 1}\0'
    text = re.sub(r'`([^`]+)`', stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        md = re.match(r'^(?:\./)?(\d\d-[\w-]+|README|reference)\.md(?:#(.+))?$', url)
        if md:
            target = 'doc-' + md.group(1).lower() + (f'--{md.group(2)}' if md.group(2) else '')
            return f'<a href="#{target}">{label}</a>'
        if url.startswith('#'):
            return f'<a href="#{doc}--{url[1:]}">{label}</a>'
        ext = ' target="_blank" rel="noopener"' if url.startswith('http') else ' class="repo"'
        return f'<a href="{html.escape(url)}"{ext}>{label}</a>'
    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, text)
    return re.sub(r'\0(\d+)\0', lambda m: codes[int(m.group(1))], text)


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|') and not line.endswith('\\|'):
        line = line[:-1]
    return [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', line)]


def md_to_html(text: str, doc: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Kichik, ishonchli Markdown (sarlavha, jadval, ro'yxat, kod bloki, iqtibos, havola, **qalin**, `kod`). → (html, [(daraja, id, sarlavha)])"""
    lines, out, heads, i = text.split('\n'), [], [], 0
    list_stack: list[tuple[int, str]] = []

    def close_lists(to: int = 0):
        while len(list_stack) > to:
            out.append(f'</li></{list_stack.pop()[1]}>')
    while i < len(lines):
        line = lines[i]
        fence = re.match(r'^```(\w*)\s*$', line)
        if fence:
            close_lists()
            j, buf = i + 1, []
            while j < len(lines) and not lines[j].startswith('```'):
                buf.append(lines[j])
                j += 1
            lang = fence.group(1)
            out.append(f'<div class="code"><button class="copy" type="button" aria-label="Nusxa olish">Nusxa</button><pre><code class="lang-{lang}">{html.escape(chr(10).join(buf))}</code></pre></div>')
            i = j + 1
            continue
        head = re.match(r'^(#{1,4})\s+(.*?)\s*#*\s*$', line)
        if head:
            close_lists()
            level, title = len(head.group(1)), head.group(2)
            hid = doc if level == 1 else f'{doc}--{slug(title)}'
            heads.append((level, hid, re.sub(r'`|\*\*', '', title)))
            out.append(f'<h{level} id="{hid}">{inline(title, doc)}<a class="anchor" href="#{hid}" aria-label="Havola">#</a></h{level}>')
            i += 1
            continue
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\|?\s*:?-{3,}', lines[i + 1]):
            close_lists()
            header = split_row(line)
            j, rows = i + 2, []
            while j < len(lines) and lines[j].startswith('|'):
                rows.append(split_row(lines[j]))
                j += 1
            th = ''.join(f'<th>{inline(c, doc)}</th>' for c in header)
            body = ''.join('<tr>' + ''.join(f'<td>{inline(c, doc)}</td>' for c in r) + '</tr>' for r in rows)
            out.append(f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')
            i = j
            continue
        li = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if li:
            indent, marker, content = len(li.group(1)), li.group(2), li.group(3)
            kind = 'ol' if marker[0].isdigit() else 'ul'
            while list_stack and list_stack[-1][0] > indent:
                out.append(f'</li></{list_stack.pop()[1]}>')
            if list_stack and list_stack[-1][0] == indent:
                out.append('</li><li>')
            else:
                out.append(f'<{kind}><li>')
                list_stack.append((indent, kind))
            out.append(inline(content, doc))
            i += 1
            continue
        if list_stack and line.startswith('  ') and line.strip():
            out.append(' ' + inline(line.strip(), doc))
            i += 1
            continue
        if line.startswith('>'):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].startswith('>'):
                buf.append(lines[i].lstrip('> ').rstrip())
                i += 1
            out.append(f'<blockquote>{inline(" ".join(buf), doc)}</blockquote>')
            continue
        if re.match(r'^-{3,}\s*$', line):
            close_lists()
            out.append('<hr>')
            i += 1
            continue
        if not line.strip():
            close_lists()
            i += 1
            continue
        close_lists()
        buf = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,4}\s|```|\||>|\s*([-*]|\d+\.)\s|-{3,}\s*$)', lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append(f'<p>{inline(" ".join(buf), doc)}</p>')
    close_lists()
    return '\n'.join(out), heads


# ════════════════════════════════════════════════════════════ index.html
def doc_files() -> list[Path]:
    """Tartib: README (bosh sahifa), keyin 01…12, oxirida avtomatik reference."""
    rank = lambda p: (0 if p.stem.lower() == 'readme' else 2 if p.stem == 'reference' else 1, p.name)
    return sorted(DOCS.glob('*.md'), key=rank)


def doc_id(path: Path) -> str:
    return 'doc-' + path.stem.lower()


def build_index() -> str:
    sections, nav = [], []
    for path in doc_files():
        text = path.read_text(encoding='utf-8')
        body, heads = md_to_html(text, doc_id(path))
        title = next((h[2] for h in heads if h[0] == 1), path.stem)
        sections.append(f'<section class="doc" id="sec-{doc_id(path)}" data-title="{html.escape(title)}">\n{body}\n</section>')
        subs = ''.join(f'<li><a href="#{h[1]}">{html.escape(h[2])}</a></li>' for h in heads if h[0] == 2)
        nav.append(f'<li><a class="top" href="#{doc_id(path)}">{html.escape(title)}</a><ul>{subs}</ul></li>')
    return (INDEX_TEMPLATE.replace('{{NAV}}', '\n'.join(nav)).replace('{{CONTENT}}', '\n'.join(sections)))


INDEX_TEMPLATE = (Path(__file__).parent / 'docs_template.html').read_text(encoding='utf-8')


def write_all(check: bool = False) -> list[str]:
    """Hamma generatsiya qilinadigan fayllarni yozadi (check=True — yozmaydi, eskirganlari ro'yxatini qaytaradi)."""
    DOCS.mkdir(exist_ok=True)
    stale = []
    ref = DOCS / 'reference.md'
    new_ref = build_reference()
    if not ref.exists() or ref.read_text(encoding='utf-8') != new_ref:
        stale.append('docs/reference.md')
        if not check:
            ref.write_text(new_ref, encoding='utf-8', newline='\n')
    idx = DOCS / 'index.html'
    new_idx = build_index()
    if not idx.exists() or idx.read_text(encoding='utf-8') != new_idx:
        stale.append('docs/index.html')
        if not check:
            idx.write_text(new_idx, encoding='utf-8', newline='\n')
    return stale
