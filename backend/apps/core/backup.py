"""Zaxira nusxa (backup) va tiklash — faqat Python, cron/tashqi dastur shart emas (PostgreSQL uchun `pg_dump` bo'lsa u ishlatiladi).

Bitta nusxa = bitta arxiv `uzswlu-YYYYMMDD-HHMMSS.tar.gz` (+ yoniga `.json` ma'lumot fayli: hajm, sha256, baza turi):
    manifest.json            — nima va qachon olingani
    db.sqlite3 | db.pgdump | db.jsonl   — baza (turi muhitga qarab)
    media/, private/         — yuklangan rasm/PDF va yopiq fayllar (murojaat ilovalari)

Baza usullari:
    SQLite      → sqlite3 ichki zaxira API'si (ishlayotgan bazadan ham izchil nusxa oladi)
    PostgreSQL  → pg_dump (custom format; izchil snapshot, serverni to'xtatmaydi). pg_dump bo'lmasa → db.jsonl (Django serializer)
    JSON        → har qanday baza uchun ko'chma format (sekinroq, lekin dasturga bog'liq emas)

Boshqaruv: `python manage.py backup` / `restore`. Kechasi `run_nightly` ichida avtomatik (apps.core.nightly).
"""
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.db import connection, connections, transaction
from django.utils import timezone

NAME_RE = re.compile(r'^uzswlu-(\d{8})-(\d{6})(?:-([a-z-]+))?\.tar\.gz$')
LOCK_STALE_SECONDS = 6 * 3600
JSON_SKIP = {'contenttypes.contenttype', 'auth.permission', 'sessions.session', 'admin.logentry'}


class BackupError(Exception):
    pass


# ---------------------------------------------------------------- yordamchilar
def backup_dir() -> Path:
    path = Path(settings.BACKUP_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _db() -> dict:
    return connection.settings_dict  # testda NAME test bazasiga almashtiriladi — shu lug'atdan o'qiymiz


def _engine() -> str:
    return 'sqlite' if 'sqlite' in _db()['ENGINE'] else 'postgres'


def _media_roots() -> dict[str, Path]:
    return {'media': Path(settings.MEDIA_ROOT), 'private': Path(settings.PRIVATE_ROOT)}


@contextlib.contextmanager
def _lock(directory: Path):
    """Ikkita zaxira bir vaqtda ishlamasin (kechki vazifa + qo'lda). Qotib qolgan qulf 6 soatdan keyin e'tiborsiz."""
    path = directory / '.lock'
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - path.stat().st_mtime > LOCK_STALE_SECONDS:
                path.unlink(missing_ok=True)
                continue
            raise BackupError('Boshqa zaxira/tiklash jarayoni ishlayapti (.lock). Tugashini kuting.') from None
    else:
        raise BackupError('Qulfni olib bo‘lmadi')
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def parse_name(name: str):
    m = NAME_RE.match(name)
    if not m:
        return None
    return datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')


def list_backups(directory: Path | None = None) -> list[dict]:
    """Eng yangisi birinchi."""
    directory = directory or backup_dir()
    out = []
    for p in directory.glob('uzswlu-*.tar.gz'):
        when = parse_name(p.name)
        if not when:
            continue
        meta = {}
        side = p.with_name(p.name[:-7] + '.json')
        if side.exists():
            with contextlib.suppress(ValueError, OSError):
                meta = json.loads(side.read_text(encoding='utf-8'))
        out.append({'path': p, 'name': p.name, 'when': when, 'size': p.stat().st_size, 'meta': meta})
    return sorted(out, key=lambda b: b['when'], reverse=True)


DATE_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?$')


def _parse_date(ref: str) -> datetime | None:
    """`2026-08-15` → o'sha kun oxirigacha; `2026-08-15 14:30` → aynan shu daqiqagacha."""
    m = DATE_RE.match(ref.strip())
    if not m:
        return None
    try:
        if m.group(2):
            return datetime.strptime(f'{m.group(1)} {m.group(2)}', '%Y-%m-%d %H:%M') + timedelta(minutes=1)
        return datetime.strptime(m.group(1), '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        return None


def find(ref: str) -> tuple[dict | None, dict | None]:
    """Sanaga eng yaqin zaxiralar: (shu sanagacha bo'lgan eng yangisi, undan keyingi eng eskisi)."""
    limit = _parse_date(ref)
    if not limit:
        raise BackupError(f'Sana noto‘g‘ri: {ref} (YYYY-MM-DD yoki "YYYY-MM-DD HH:MM")')
    items = list_backups()
    before = next((b for b in items if b['when'] < limit), None)
    after = next((b for b in reversed(items) if b['when'] >= limit), None)
    return before, after


def resolve(ref: str | None) -> Path:
    """`latest`, sana (`2026-08-15` — shu kungacha bo'lgan eng yangi nusxa), fayl nomi yoki to'liq yo'l → arxiv yo'li."""
    if not ref or ref == 'latest':
        items = list_backups()
        if not items:
            raise BackupError(f'Zaxira topilmadi: {backup_dir()}')
        return items[0]['path']
    if _parse_date(ref):
        before, after = find(ref)
        if before:
            return before['path']
        raise BackupError(f'{ref} yoki undan oldin zaxira yo‘q' + (f'; eng eskisi: {after["name"]}' if after else ''))
    p = Path(ref)
    if not p.exists():
        p = backup_dir() / ref
    if not p.exists():
        raise BackupError(f'Fayl topilmadi: {ref}')
    return p


# ---------------------------------------------------------------- bazani dump qilish
def _dump_sqlite(dest: Path) -> None:
    connection.ensure_connection()
    target = sqlite3.connect(dest)
    try:
        connection.connection.backup(target)
    finally:
        target.close()


def _pg_env_args(binary: str) -> tuple[list[str], dict]:
    cfg = _db()
    args = [binary]
    if cfg.get('HOST'):
        args += ['-h', str(cfg['HOST'])]
    if cfg.get('PORT'):
        args += ['-p', str(cfg['PORT'])]
    if cfg.get('USER'):
        args += ['-U', str(cfg['USER'])]
    env = {**os.environ, 'PGCONNECT_TIMEOUT': '15'}
    if cfg.get('PASSWORD'):
        env['PGPASSWORD'] = str(cfg['PASSWORD'])  # buyruq qatorida emas — `ps` da ko'rinmasin
    return args, env


def _run(args: list[str], env: dict, what: str) -> None:
    try:
        res = subprocess.run(args, env=env, capture_output=True, text=True, timeout=6 * 3600)
    except FileNotFoundError:
        raise BackupError(f'{args[0]} topilmadi') from None
    except subprocess.TimeoutExpired:
        raise BackupError(f'{what}: vaqt tugadi') from None
    if res.returncode != 0:
        raise BackupError(f'{what} xato bilan tugadi: {(res.stderr or res.stdout).strip()[:600]}')


def _dump_pg(dest: Path) -> None:
    args, env = _pg_env_args('pg_dump')
    _run(args + ['--format=custom', '--no-owner', '--no-privileges', '--file', str(dest), _db()['NAME']], env, 'pg_dump')


def _dump_json(dest: Path) -> int:
    from django.apps import apps
    from django.core import serializers
    total = 0
    with open(dest, 'w', encoding='utf-8') as f, transaction.atomic():
        for model in apps.get_models():
            label = model._meta.label_lower
            if label in JSON_SKIP or model._meta.proxy or not model._meta.managed:
                continue
            qs = model._base_manager.order_by('pk').iterator(chunk_size=2000)
            serializers.serialize('jsonl', qs, stream=f)
            total += 1
    return total


def pick_db_format() -> str:
    fmt = (settings.BACKUP_DB_FORMAT or 'auto').lower()
    if fmt not in ('auto', 'native', 'json'):
        raise BackupError(f'BACKUP_DB_FORMAT noto‘g‘ri: {fmt} (auto | native | json)')
    if fmt == 'json':
        return 'json'
    if _engine() == 'sqlite':
        return 'sqlite'
    if shutil.which('pg_dump'):
        return 'pgdump'
    if fmt == 'native':
        raise BackupError('BACKUP_DB_FORMAT=native, lekin pg_dump o‘rnatilmagan (postgresql-client)')
    return 'json'  # auto: pg_dump yo'q — ko'chma formatga tushamiz


DB_FILES = {'sqlite': 'db.sqlite3', 'pgdump': 'db.pgdump', 'json': 'db.jsonl'}


def _add_tree(tar: tarfile.TarFile, root: Path, arc: str) -> int:
    """Papkani arxivga qo'shadi. Zaxira vaqtida o'chirilgan/yozilayotgan fayl butun zaxirani buzmaydi."""
    count = 0
    if not root.is_dir():
        return 0
    tar.add(str(root), arcname=arc, recursive=False)
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(dirs) + sorted(files):
            full = Path(base, name)
            rel = full.relative_to(root).as_posix()
            if full.is_symlink():
                continue
            try:
                tar.add(str(full), arcname=f'{arc}/{rel}', recursive=False)
                count += full.is_file()
            except (FileNotFoundError, PermissionError):
                continue
    return count


# ---------------------------------------------------------------- yaratish
def create(label: str = '', *, media: bool | None = None, copy: bool = True) -> dict:
    """Yangi zaxira. Natija: {'path', 'size', 'db', 'files', 'copied': [...]}"""
    media = settings.BACKUP_MEDIA if media is None else media
    directory = backup_dir()
    with _lock(directory):
        _sweep_partials(directory)
        stamp = timezone.localtime().strftime('%Y%m%d-%H%M%S')
        name = f"uzswlu-{stamp}{('-' + label) if label else ''}.tar.gz"
        final, partial = directory / name, directory / f'.{name}.partial'
        work = Path(tempfile.mkdtemp(prefix='.tmp-', dir=directory))
        try:
            kind = pick_db_format()
            dbfile = work / DB_FILES[kind]
            {'sqlite': _dump_sqlite, 'pgdump': _dump_pg, 'json': _dump_json}[kind](dbfile)
            files = 0
            with tarfile.open(partial, 'w:gz', compresslevel=4) as tar:
                tar.add(str(dbfile), arcname=dbfile.name)
                included = []
                if media:
                    for arc, root in _media_roots().items():
                        n = _add_tree(tar, root, arc)
                        if root.is_dir():
                            included.append(arc)
                            files += n
                manifest = {
                    'version': 1, 'created': timezone.now().isoformat(), 'label': label, 'db': kind, 'dbFile': dbfile.name,
                    'engine': _db()['ENGINE'], 'dbSize': dbfile.stat().st_size, 'files': files, 'included': included,
                    'host': os.uname().nodename if hasattr(os, 'uname') else '',
                }
                raw = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
                info = tarfile.TarInfo('manifest.json')
                info.size, info.mtime = len(raw), time.time()
                tar.addfile(info, io.BytesIO(raw))
            digest = _sha256(partial)
            os.replace(partial, final)
            meta = {**manifest, 'sha256': digest, 'size': final.stat().st_size}
            final.with_name(name[:-7] + '.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        finally:
            shutil.rmtree(work, ignore_errors=True)
            partial.unlink(missing_ok=True)
    result = {'path': final, 'size': final.stat().st_size, 'db': kind, 'files': files, 'copied': [], 'copy_error': ''}
    if copy and settings.BACKUP_COPY_TO:
        try:
            result['copied'].append(copy_to(final, Path(settings.BACKUP_COPY_TO)))
        except (OSError, BackupError) as exc:
            result['copy_error'] = f'{settings.BACKUP_COPY_TO}: {exc}'
    return result


def _sweep_partials(directory: Path) -> None:
    """Oldingi yiqilgan urinishlardan qolgan yarim fayllar."""
    for p in list(directory.glob('.*.partial')) + list(directory.glob('.tmp-*')):
        if time.time() - p.stat().st_mtime > 3600:
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)


def copy_to(archive: Path, target: Path) -> Path:
    """Ikkinchi joyga (boshqa disk, ulangan tarmoq papkasi) nusxa: avval vaqtinchalik nom, keyin nomini almashtirish va sha256 solishtirish."""
    target.mkdir(parents=True, exist_ok=True)
    side = _sidecar(archive)
    tmp = target / f'.{archive.name}.partial'
    try:
        shutil.copyfile(archive, tmp)
        if _sha256(tmp) != _sha256(archive):
            raise BackupError('nusxa sha256 mos kelmadi')
        os.replace(tmp, target / archive.name)
        if side.exists():
            shutil.copyfile(side, target / side.name)
    finally:
        tmp.unlink(missing_ok=True)
    prune(target)
    return target / archive.name


# ---------------------------------------------------------------- saqlash siyosati (kun → hafta → oy → yil)
def _sidecar(path: Path) -> Path:
    return path.with_name(path.name[:-7] + '.json')


def retention(items: list[dict] | None = None, now: datetime | None = None, *, keep_days: int | None = None,
              keep_weeks: int | None = None, keep_months: int | None = None, keep_years: int | None = None,
              keep_min: int | None = None) -> list[tuple[dict, str | None]]:
    """Qaysi zaxira nima uchun saqlanadi (sabab matni) yoki o'chiriladi (None). Toza funksiya: faylga tegmaydi.

    Zaxira yoshiga qarab «vaqt oynasi»ga tushadi (oynalar hozirdan boshlab hisoblanadi, bir-birini to'ldiradi):
        kunlik   (< keep_days kun)        — HAMMASI saqlanadi (qo'lda olinganlari ham)
        haftalik (< keep_weeks hafta)     — har ISO-haftadan eng oxirgisi
        oylik    (< keep_months oy)       — har oydan eng oxirgisi
        yillik   (< keep_years yil; 0 — abadiy) — har yildan eng oxirgisi
    Doim saqlanadi: qadalgan (`pin`) nusxalar va eng yangi keep_min tasi. keep_days=0 — hech narsa o'chirilmaydi."""
    cfg = settings
    keep_days = cfg.BACKUP_KEEP_DAYS if keep_days is None else keep_days
    keep_weeks = cfg.BACKUP_KEEP_WEEKS if keep_weeks is None else keep_weeks
    keep_months = cfg.BACKUP_KEEP_MONTHS if keep_months is None else keep_months
    keep_years = cfg.BACKUP_KEEP_YEARS if keep_years is None else keep_years
    keep_min = cfg.BACKUP_KEEP_MIN if keep_min is None else keep_min
    items = sorted(items if items is not None else list_backups(), key=lambda b: b['when'], reverse=True)
    now = now or datetime.now()
    if keep_days <= 0:
        return [(b, 'o‘chirish yoqilmagan') for b in items]
    day_end = timedelta(days=keep_days)
    week_end = max(timedelta(weeks=max(keep_weeks, 0)), day_end)
    month_end = max(timedelta(days=round(max(keep_months, 0) * 30.44)), week_end)
    year_end = None if keep_years <= 0 else max(timedelta(days=round(keep_years * 365.25)), month_end)
    out, seen = [], set()
    for i, b in enumerate(items):
        age, w = now - b['when'], b['when'].isocalendar()
        if age < day_end:
            slot, label = None, 'kunlik'
        elif age < week_end:
            slot, label = ('w', w.year, w.week), f'haftalik {w.year}-H{w.week:02d}'
        elif age < month_end:
            slot, label = ('m', b['when'].year, b['when'].month), f'oylik {b["when"]:%Y-%m}'
        elif year_end is None or age < year_end:
            slot, label = ('y', b['when'].year), f'yillik {b["when"].year}'
        else:
            slot = label = None  # barcha oynalardan eski
        winner = bool(label) and (slot is None or slot not in seen)  # eng yangisi birinchi keladi → u slot g'olibi
        if winner and slot is not None:
            seen.add(slot)
        if b['meta'].get('pinned'):
            reason = 'qadalgan'
        elif winner:
            reason = label
        elif i < keep_min:
            reason = 'eng yangi'
        else:
            reason = None
        out.append((b, reason))
    return out


def prune(directory: Path | None = None, *, dry_run: bool = False, now: datetime | None = None, **policy) -> list[str]:
    """Siyosatga ko'ra ortiqcha zaxiralarni o'chiradi (dry_run — faqat nomlarini qaytaradi)."""
    removed = []
    for item, reason in retention(list_backups(directory), now, **policy):
        if reason is None:
            if not dry_run:
                item['path'].unlink(missing_ok=True)
                _sidecar(item['path']).unlink(missing_ok=True)
            removed.append(item['name'])
    return removed


def pin(ref: str, value: bool = True) -> Path:
    """Qadash: nusxa hech qachon avtomatik o'chirilmaydi (masalan, katta yangilanish oldidan). BACKUP_COPY_TO dagi nusxasi ham."""
    path = resolve(ref)
    for directory in filter(None, (path.parent, Path(settings.BACKUP_COPY_TO) if settings.BACKUP_COPY_TO else None)):
        archive = directory / path.name
        if not archive.exists():
            continue
        side = _sidecar(archive)
        meta = json.loads(side.read_text(encoding='utf-8')) if side.exists() else {}
        meta['pinned'] = value
        side.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


# ---------------------------------------------------------------- tekshirish
def verify(path: Path, deep: bool = True) -> dict:
    """Arxiv butunligi: sha256, tar/gzip to'liq o'qiladi, baza fayli haqiqatan ochiladi. Muammo bo'lsa BackupError."""
    path = Path(path)
    side = path.with_name(path.name[:-7] + '.json') if path.name.endswith('.tar.gz') else None
    meta = json.loads(side.read_text(encoding='utf-8')) if side and side.exists() else {}
    if meta.get('sha256') and _sha256(path) != meta['sha256']:
        raise BackupError(f'{path.name}: sha256 mos kelmadi — fayl buzilgan')
    try:
        names, manifest = set(), None
        with tarfile.open(path, 'r:gz') as tar:
            for member in tar:
                names.add(member.name)
                if member.name == 'manifest.json':
                    manifest = json.loads(tar.extractfile(member).read())
                elif member.isfile():
                    f = tar.extractfile(member)
                    while f.read(1024 * 1024):
                        pass  # gzip CRC va kesilgan arxivni aniqlash uchun oxirigacha o'qiymiz
    except (tarfile.TarError, EOFError, OSError, ValueError) as exc:
        raise BackupError(f'{path.name}: arxiv buzilgan ({exc})') from None
    if not manifest:
        raise BackupError(f'{path.name}: manifest.json yo‘q')
    dbfile = manifest.get('dbFile')
    if dbfile not in names:
        raise BackupError(f'{path.name}: {dbfile} arxivda yo‘q')
    if deep:
        with tempfile.TemporaryDirectory(dir=path.parent, prefix='.tmp-') as tmp:
            with tarfile.open(path, 'r:gz') as tar:
                tar.extract(dbfile, tmp, filter='data')
            _check_db_file(Path(tmp, dbfile), manifest['db'])
    return manifest


def _check_db_file(path: Path, kind: str) -> None:
    if kind == 'sqlite':
        con = sqlite3.connect(path)
        try:
            res = con.execute('PRAGMA integrity_check').fetchone()[0]
        finally:
            con.close()
        if res != 'ok':
            raise BackupError(f'SQLite butunlik tekshiruvi: {res}')
    elif kind == 'pgdump':
        if shutil.which('pg_restore'):
            res = subprocess.run(['pg_restore', '--list', str(path)], capture_output=True, text=True)
            if res.returncode != 0:
                raise BackupError(f'pg_dump fayli o‘qilmadi: {res.stderr.strip()[:300]}')
    else:
        with open(path, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                try:
                    json.loads(line)
                except ValueError:
                    raise BackupError(f'db.jsonl {n}-qator buzilgan') from None


# ---------------------------------------------------------------- tiklash
def restore(path: Path, *, safety: bool = True, db: bool = True, media: bool = True) -> dict:
    """Tiklash. Oldin arxiv tekshiriladi; keyin (safety=True) joriy holatdan `pre-restore` zaxirasi olinadi.
    Backend va nightly to'xtatilgan bo'lishi kerak (ochiq ulanishlar bazani bloklaydi)."""
    from django.core.cache import cache
    from django.core.management import call_command
    path = Path(path)
    manifest = verify(path)
    safety_path = None
    if safety:
        try:
            safety_path = create('pre-restore', copy=False)['path']
        except BackupError as exc:
            raise BackupError(f'Tiklashdan oldingi xavfsizlik nusxasi olinmadi: {exc}. Davom etish uchun --no-safety.') from None
    directory = backup_dir()
    with _lock(directory):
        tmp = Path(tempfile.mkdtemp(prefix='.tmp-', dir=directory))
        try:
            try:
                with tarfile.open(path, 'r:gz') as tar:
                    tar.extractall(tmp, filter='data')  # '../' va mutlaq yo'llar, xavfli havolalar rad etiladi
            except (tarfile.TarError, OSError) as exc:
                raise BackupError(f'Arxivni ochib bo‘lmadi: {exc}') from None
            if db:
                _restore_db(tmp / manifest['dbFile'], manifest['db'])
            restored = []
            if media:
                for arc, root in _media_roots().items():
                    src = tmp / arc
                    if arc in manifest.get('included', []) and src.is_dir():
                        _replace_contents(src, root)
                        restored.append(arc)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if db:
        connections.close_all()
        call_command('migrate', interactive=False, verbosity=0)  # zaxira eski bo'lsa — yangi migratsiyalar qo'llanadi
    cache.clear()
    return {'manifest': manifest, 'safety': safety_path, 'media': restored}


def _replace_contents(src: Path, dst: Path) -> None:
    """dst papkasining o'zini emas, ichini almashtiradi (u Docker volume ulangan joy bo'lishi mumkin)."""
    dst.mkdir(parents=True, exist_ok=True)
    for child in dst.iterdir():
        shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _restore_db(dbfile: Path, kind: str) -> None:
    from django.core.management import call_command
    if kind == 'sqlite':
        if _engine() != 'sqlite':
            raise BackupError('Bu SQLite nusxasi, joriy baza esa PostgreSQL. Ko‘chma format (BACKUP_DB_FORMAT=json) bilan olingan nusxa kerak.')
        connection.ensure_connection()
        source = sqlite3.connect(dbfile)
        try:
            source.backup(connection.connection)
        finally:
            source.close()
    elif kind == 'pgdump':
        if _engine() != 'postgres':
            raise BackupError('Bu PostgreSQL nusxasi, joriy baza esa SQLite.')
        connections.close_all()
        args, env = _pg_env_args('pg_restore')
        # --single-transaction: yarim tiklanib qolmaydi (xato bo'lsa hammasi orqaga qaytadi)
        _run(args + ['--clean', '--if-exists', '--no-owner', '--no-privileges', '--single-transaction', '--exit-on-error',
                     '--dbname', _db()['NAME'], str(dbfile)], env, 'pg_restore')
    else:
        call_command('migrate', interactive=False, verbosity=0)
        call_command('flush', interactive=False, verbosity=0)
        # loaddata kengaytma bo'yicha formatni aniqlaydi
        call_command('loaddata', str(dbfile), verbosity=0)


# ---------------------------------------------------------------- holat va kechki vazifa
def status() -> dict:
    items = list_backups()
    if not items:
        return {'ok': False, 'latest': None, 'age_hours': None, 'count': 0, 'reason': 'Hali birorta zaxira olinmagan'}
    latest = items[0]
    age = (datetime.now() - latest['when']).total_seconds() / 3600
    ok = age <= settings.BACKUP_MAX_AGE_HOURS
    return {'ok': ok, 'latest': latest, 'age_hours': round(age, 1), 'count': len(items),
            'reason': '' if ok else f'Oxirgi zaxira {age:.0f} soat oldin (chegara: {settings.BACKUP_MAX_AGE_HOURS} soat)'}


def run_scheduled() -> str:
    """Kechki vazifa: zaxira → tekshirish → eskilarini tozalash."""
    from apps.core.utils import size_label
    res = create()
    verify(res['path'], deep=True)  # olingan nusxa haqiqatan o'qiladimi — «zaxira bor, lekin ochilmaydi» bo'lmasin
    removed = prune()
    text = f"{res['path'].name} ({size_label(res['size'])}, baza: {res['db']}, {res['files']} fayl); {len(removed)} eskisi o‘chirildi"
    if res['copy_error']:
        raise BackupError(f"{text}. Ikkinchi joyga nusxa OLINMADI — {res['copy_error']}")
    if res['copied']:
        text += f"; nusxa: {res['copied'][0].parent}"
    return text
