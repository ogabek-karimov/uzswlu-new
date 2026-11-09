"""Zaxira va tiklash: yaratish, tekshirish, tiklash (SQLite va PostgreSQL — qaysi baza bilan ishlayotgan bo'lsa), ko'chma JSON,
buzilgan arxiv, tozalash, qulf, xavfsizlik (yo'l almashtirish), kechki vazifa, buyruqlar."""
import io
import json
import os
import tarfile
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase, override_settings

from apps.accounts.models import User
from apps.core import backup as bk
from apps.core import nightly
from apps.structure.models import Faculty


class BackupBase(TransactionTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.dir, self.media, self.private = root / 'backups', root / 'media', root / 'private'
        for p, name, text in ((self.media, 'a/photo.webp', 'rasm-1'), (self.private, 'appeals/1/ariza.pdf', 'yopiq-1')):
            (p / name).parent.mkdir(parents=True, exist_ok=True)
            (p / name).write_text(text)
        ov = override_settings(BACKUP_DIR=self.dir, MEDIA_ROOT=self.media, PRIVATE_ROOT=self.private, BACKUP_ENABLED=True,
                              BACKUP_COPY_TO='', BACKUP_DB_FORMAT='auto')
        ov.enable()
        self.addCleanup(ov.disable)
        User.objects.create_user('root', password='Pw-12345678!', role='superadmin', name='Root')
        Faculty.objects.create(slug='fa', name={'uz': 'Asl fakultet'})

    def names(self):
        return sorted(Faculty.objects.values_list('slug', flat=True))


class CreateAndRestoreTests(BackupBase):
    def test_create_has_db_media_manifest_sidecar_and_verifies(self):
        res = bk.create()
        self.assertTrue(res['path'].exists() and res['size'] > 0)
        with tarfile.open(res['path']) as tar:
            names = set(tar.getnames())
        self.assertTrue({'manifest.json', 'media/a/photo.webp', 'private/appeals/1/ariza.pdf'} <= names)
        self.assertTrue(any(n.startswith('db.') for n in names))
        side = res['path'].with_name(res['path'].name[:-7] + '.json')
        self.assertTrue(side.exists())
        self.assertEqual(bk.verify(res['path'])['files'], 2)
        self.assertEqual([p.name for p in self.dir.iterdir() if p.name.startswith(('.tmp', '..'))], [])  # vaqtinchalik fayl qolmaydi

    def _roundtrip(self):
        res = bk.create()
        Faculty.objects.create(slug='yangi', name={'uz': 'Zaxiradan keyin qo‘shildi'})
        Faculty.objects.filter(slug='fa').delete()
        User.objects.all().delete()
        (self.media / 'a/photo.webp').write_text('BUZILGAN')
        (self.media / 'ortiqcha.webp').write_text('keyin yuklangan')
        out = bk.restore(res['path'])
        self.assertEqual(self.names(), ['fa'])                                   # baza zaxiradagi holatda
        self.assertTrue(User.objects.filter(username='root').exists())
        self.assertEqual((self.media / 'a/photo.webp').read_text(), 'rasm-1')    # fayl asl holiga qaytdi
        self.assertFalse((self.media / 'ortiqcha.webp').exists())                # zaxiradan keyingi fayl olib tashlandi
        self.assertEqual((self.private / 'appeals/1/ariza.pdf').read_text(), 'yopiq-1')
        self.assertTrue(out['safety'] and out['safety'].exists())                # tiklashdan oldingi holat ham saqlangan
        self.assertIn('pre-restore', out['safety'].name)

    def test_restore_roundtrip_native(self):
        self._roundtrip()

    def test_restore_roundtrip_portable_json(self):
        with override_settings(BACKUP_DB_FORMAT='json'):
            self.assertEqual(bk.pick_db_format(), 'json')
            self._roundtrip()

    def test_db_only_and_media_only(self):
        res = bk.create()
        Faculty.objects.create(slug='yangi', name={'uz': 'x'})
        (self.media / 'a/photo.webp').write_text('o‘zgargan')
        bk.restore(res['path'], safety=False, media=False)
        self.assertEqual(self.names(), ['fa'])
        self.assertEqual((self.media / 'a/photo.webp').read_text(), 'o‘zgargan')
        bk.restore(res['path'], safety=False, db=False)
        self.assertEqual((self.media / 'a/photo.webp').read_text(), 'rasm-1')

    def test_no_media_backup_leaves_files_untouched_on_restore(self):
        res = bk.create(media=False)
        (self.media / 'a/photo.webp').write_text('hozirgi')
        bk.restore(res['path'], safety=False)
        self.assertEqual((self.media / 'a/photo.webp').read_text(), 'hozirgi')

    def test_vanishing_file_does_not_break_backup(self):
        real_add = tarfile.TarFile.add

        def flaky(self_, name, *a, **kw):
            if str(name).endswith('photo.webp'):
                raise FileNotFoundError(name)
            return real_add(self_, name, *a, **kw)
        with mock.patch.object(tarfile.TarFile, 'add', flaky):
            res = bk.create()
        bk.verify(res['path'])


class IntegrityTests(BackupBase):
    def test_truncated_archive_is_rejected(self):
        p = bk.create()['path']
        p.write_bytes(p.read_bytes()[:-200])
        with self.assertRaises(bk.BackupError):
            bk.verify(p)

    def test_modified_archive_fails_checksum(self):
        p = bk.create()['path']
        data = bytearray(p.read_bytes())
        data[len(data) // 2] ^= 0xFF
        p.write_bytes(bytes(data))
        with self.assertRaisesRegex(bk.BackupError, 'sha256'):
            bk.verify(p)

    def test_restore_refuses_broken_archive_and_changes_nothing(self):
        p = bk.create()['path']
        Faculty.objects.create(slug='yangi', name={'uz': 'x'})
        p.write_bytes(p.read_bytes()[:-200])
        with self.assertRaises(bk.BackupError):
            bk.restore(p)
        self.assertIn('yangi', self.names())

    def test_path_traversal_member_cannot_escape(self):
        good = bk.create()['path']
        evil = self.dir / 'uzswlu-20200101-000000.tar.gz'
        with tarfile.open(good) as src, tarfile.open(evil, 'w:gz') as dst:
            for m in src:
                dst.addfile(m, src.extractfile(m) if m.isfile() else None)
            info = tarfile.TarInfo('../../evil.txt')
            info.size = 4
            dst.addfile(info, io.BytesIO(b'evil'))
        with self.assertRaises(bk.BackupError):
            bk.restore(evil, safety=False)
        self.assertFalse((Path(self.tmp.name).parent / 'evil.txt').exists())
        self.assertFalse((self.dir.parent / 'evil.txt').exists())


class RetentionTests(BackupBase):
    """Status, ikkinchi joyga nusxa va qulf."""

    def test_status(self):
        self.assertFalse(bk.status()['ok'])
        bk.create()
        self.assertTrue(bk.status()['ok'])
        with override_settings(BACKUP_MAX_AGE_HOURS=0):
            self.assertFalse(bk.status()['ok'])

    def test_second_location_copy_and_failure_reporting(self):
        copy_dir = Path(self.tmp.name) / 'offsite'
        with override_settings(BACKUP_COPY_TO=str(copy_dir)):
            res = bk.create()
        self.assertEqual(res['copied'][0].parent, copy_dir)
        self.assertEqual(bk.verify(res['copied'][0])['db'], res['db'])
        blocker = Path(self.tmp.name) / 'file'
        blocker.write_text('x')
        with override_settings(BACKUP_COPY_TO=str(blocker / 'sub')):
            res = bk.create()
        self.assertTrue(res['path'].exists() and res['copy_error'])     # asosiy zaxira bor, ikkinchi nusxa xatosi aniq aytiladi

    def test_lock_blocks_parallel_and_stale_lock_is_ignored(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        lock = self.dir / '.lock'
        lock.write_text('1')
        with self.assertRaisesRegex(bk.BackupError, 'ishlayapti'):
            bk.create()
        old = time.time() - 7 * 3600
        os.utime(lock, (old, old))
        bk.create()
        self.assertFalse(lock.exists())

    def test_failed_backup_leaves_no_partial_and_releases_lock(self):
        with mock.patch.object(bk, '_dump_sqlite', side_effect=RuntimeError('disk to‘ldi')), \
                mock.patch.object(bk, '_dump_json', side_effect=RuntimeError('disk to‘ldi')), \
                mock.patch.object(bk, '_dump_pg', side_effect=RuntimeError('disk to‘ldi')):
            with self.assertRaises(RuntimeError):
                bk.create()
        self.assertEqual([p.name for p in self.dir.iterdir()], [])


class PostgresCommandTests(BackupBase):
    """pg_dump/pg_restore chaqiruvi: parol buyruq qatorida emas (ps'da ko'rinmasin), kerakli bayroqlar bor."""

    CFG = {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'uzswlu', 'USER': 'u', 'PASSWORD': 's3cret', 'HOST': 'db', 'PORT': '5432'}

    def test_pg_dump_and_restore_invocation(self):
        calls = []

        def fake_run(args, **kw):
            calls.append((args, kw['env']))
            return mock.Mock(returncode=0, stdout='', stderr='')
        with mock.patch.object(bk, '_db', return_value=self.CFG), mock.patch.object(bk.subprocess, 'run', fake_run):
            bk._dump_pg(Path('/tmp/x.pgdump'))
        dump_args, dump_env = calls[0]
        self.assertEqual(dump_args[0], 'pg_dump')
        self.assertTrue({'--format=custom', '--no-owner', '--no-privileges', '-h', 'db', '-U', 'u', 'uzswlu'} <= set(dump_args))
        self.assertNotIn('s3cret', ' '.join(dump_args))
        self.assertEqual(dump_env['PGPASSWORD'], 's3cret')

    def test_pg_failure_is_reported_without_secret(self):
        res = mock.Mock(returncode=1, stdout='', stderr='connection refused')
        with mock.patch.object(bk, '_db', return_value=self.CFG), mock.patch.object(bk.subprocess, 'run', return_value=res):
            with self.assertRaisesRegex(bk.BackupError, 'connection refused') as cm:
                bk._dump_pg(Path('/tmp/x.pgdump'))
        self.assertNotIn('s3cret', str(cm.exception))

    def test_auto_falls_back_to_json_without_pg_dump(self):
        with mock.patch.object(bk, '_engine', return_value='postgres'), mock.patch.object(bk.shutil, 'which', return_value=None):
            self.assertEqual(bk.pick_db_format(), 'json')
            with override_settings(BACKUP_DB_FORMAT='native'), self.assertRaisesRegex(bk.BackupError, 'pg_dump'):
                bk.pick_db_format()
        with mock.patch.object(bk, '_engine', return_value='postgres'), mock.patch.object(bk.shutil, 'which', return_value='/usr/bin/pg_dump'):
            self.assertEqual(bk.pick_db_format(), 'pgdump')

    def test_wrong_engine_restore_is_refused(self):
        with mock.patch.object(bk, '_engine', return_value='postgres'), self.assertRaisesRegex(bk.BackupError, 'SQLite'):
            bk._restore_db(Path('/x'), 'sqlite')


class ProductionCheckTests(BackupBase):
    def test_backup_warnings(self):
        from apps.core.checks import security_settings
        with override_settings(DEBUG=False, BACKUP_ENABLED=False):
            self.assertIn('uzswlu.W008', {w.id for w in security_settings(None)})
        with override_settings(DEBUG=False, BACKUP_ENABLED=True, BACKUP_COPY_TO=''):
            self.assertIn('uzswlu.W009', {w.id for w in security_settings(None)})
        with override_settings(DEBUG=False, BACKUP_ENABLED=True, BACKUP_COPY_TO='/mnt/offsite'):
            ids = {w.id for w in security_settings(None)}
        self.assertFalse({'uzswlu.W008', 'uzswlu.W009'} & ids)


class NightlyAndCommandTests(BackupBase):
    def test_nightly_task_disabled_and_enabled(self):
        with override_settings(BACKUP_ENABLED=False):
            self.assertIn('o‘chirilgan', nightly.backup())
        text = nightly.backup()
        self.assertIn('uzswlu-', text)
        self.assertEqual(len(bk.list_backups()), 1)

    def test_nightly_runs_backup_first_and_failure_does_not_stop_others(self):
        self.assertEqual(nightly.TASKS[0][0], 'backup')
        with mock.patch.object(bk, 'run_scheduled', side_effect=bk.BackupError('disk to‘la')):
            res = nightly.run_all()
        self.assertTrue(res['backup'].startswith('XATO'))
        self.assertIn('sessions', res)

    def test_commands(self):
        out = io.StringIO()
        call_command('backup', stdout=out)
        call_command('backup', '--list', stdout=out)
        call_command('backup', '--status', stdout=out)
        call_command('backup', '--verify', stdout=out)
        self.assertIn('Zaxira tayyor', out.getvalue())
        Faculty.objects.create(slug='yangi', name={'uz': 'x'})
        with self.assertRaisesRegex(CommandError, '--yes'):
            call_command('restore', 'latest', stdout=out)
        self.assertIn('yangi', self.names())                      # --yes siz hech narsa o'zgarmaydi
        call_command('restore', 'latest', '--yes', stdout=out)
        self.assertEqual(self.names(), ['fa'])

    def test_backup_command_status_fails_when_stale_or_missing(self):
        with self.assertRaises(CommandError):
            call_command('backup', '--status', stdout=io.StringIO())
        with self.assertRaisesRegex(CommandError, 'topilmadi'):
            call_command('backup', '--verify', 'yoq.tar.gz', stdout=io.StringIO())


NOW = datetime(2026, 11, 10, 12, 0)   # seshanba


class PolicyBase(BackupBase):

    def make(self, when: datetime, pinned: bool = False, label: str = ''):
        self.dir.mkdir(parents=True, exist_ok=True)
        name = f"uzswlu-{when:%Y%m%d-%H%M%S}{('-' + label) if label else ''}.tar.gz"
        p = self.dir / name
        p.write_bytes(b'x')
        p.with_name(name[:-7] + '.json').write_text('{"pinned": true}' if pinned else '{}')
        return p

    def daily(self, count: int, now=NOW):
        return [self.make(now - timedelta(days=d, hours=10)) for d in range(count)]   # har kuni 02:00

    def left(self):
        return [b['when'] for b in bk.list_backups()]


class PolicyTests(PolicyBase):
    """Saqlash siyosati: oxirgi 14 kun hammasi → haftalik (8 hafta) → oylik (12 oy) → yillik (abadiy)."""

    def test_tiers_on_400_days_of_daily_backups(self):
        self.daily(400)
        with override_settings(BACKUP_KEEP_MIN=1):
            removed = bk.prune(now=NOW)
        kept = sorted(self.left(), reverse=True)
        self.assertGreater(len(removed), 300)
        recent = [w for w in kept if NOW - w < timedelta(days=14)]
        self.assertEqual(len(recent), 14)                                           # kunlik: hammasi
        weeks = [w for w in kept if timedelta(days=14) <= NOW - w < timedelta(weeks=8)]
        self.assertEqual(len({w.isocalendar()[:2] for w in weeks}), len(weeks))     # haftalik: har haftadan bittadan
        self.assertGreaterEqual(len(weeks), 6)
        months = [w for w in kept if timedelta(weeks=8) <= NOW - w < timedelta(days=365)]
        self.assertEqual(len({(w.year, w.month) for w in months}), len(months))     # oylik: har oydan bittadan
        self.assertGreaterEqual(len(months), 9)
        old = [w for w in kept if NOW - w >= timedelta(days=365)]
        self.assertEqual(len({w.year for w in old}), len(old))                      # yillik: har yildan bittadan
        self.assertLess(len(kept), 45)                                              # 400 → ~40
        self.assertEqual(kept[0], NOW - timedelta(hours=10))                        # eng yangisi saqlangan

    def test_week_winner_is_the_latest_of_that_week(self):
        for d in (30, 29, 28, 27, 26, 25, 24):       # 7 kun ketma-ket → ikki ISO-haftaga bo'linadi
            self.make(NOW - timedelta(days=d, hours=10))
        self.make(NOW - timedelta(days=1))
        with override_settings(BACKUP_KEEP_MIN=1):
            bk.prune(now=NOW)
        kept = [w for w in self.left() if NOW - w > timedelta(days=14)]
        for w in kept:
            same_week = [x for x in (NOW - timedelta(days=d, hours=10) for d in range(24, 31)) if x.isocalendar()[:2] == w.isocalendar()[:2]]
            self.assertEqual(w, max(same_week))      # haftaning ENG OXIRGI nusxasi qoladi

    def test_three_year_nightly_simulation_stays_bounded_and_covers_history(self):
        """Har kuni zaxira + har kuni tozalash, 3 yil: joy cheklangan, tarix uzilmaydi, tozalash barqaror (qayta ishlatsa o'zgarmaydi)."""
        start = datetime(2023, 11, 10, 2, 0)
        for d in range(3 * 365 + 5):
            now = start + timedelta(days=d)
            self.make(now)
            bk.prune(now=now + timedelta(minutes=30))
        end = start + timedelta(days=3 * 365 + 4, minutes=30)
        kept = sorted(self.left(), reverse=True)
        self.assertLessEqual(len(kept), 14 + 8 + 12 + 4 + 2)                       # ≈ 40 ta, 1100 ta emas
        self.assertEqual(bk.prune(now=end), [])                                     # idempotent
        for k in range(1, 12):                                                      # oxirgi 12 oyning har biridan nusxa bor
            probe = end - timedelta(days=30 * k)
            self.assertTrue(any((w.year, w.month) == (probe.year, probe.month) for w in kept), probe)
        self.assertGreaterEqual({w.year for w in kept} & {2023, 2024, 2025, 2026}, {2023, 2024, 2025, 2026})  # har yildan bor
        self.assertEqual(len([w for w in kept if end - w < timedelta(days=14)]), 14)

    def test_manual_backups_inside_daily_window_are_all_kept(self):
        self.daily(3)
        extra = [self.make(NOW - timedelta(days=2, hours=h), label='qolda') for h in (1, 2, 3)]
        with override_settings(BACKUP_KEEP_MIN=1):
            self.assertEqual(bk.prune(now=NOW), [])
        self.assertTrue(all(p.exists() for p in extra))

    def test_pinned_is_never_deleted_and_marked(self):
        pinned = self.make(NOW - timedelta(days=900), pinned=True)
        plain = self.make(NOW - timedelta(days=901))
        self.daily(5)
        with override_settings(BACKUP_KEEP_MIN=1, BACKUP_KEEP_YEARS=1):
            removed = bk.prune(now=NOW)
        self.assertTrue(pinned.exists())
        self.assertIn(plain.name, removed)
        self.assertEqual(dict((b['name'], r) for b, r in bk.retention(now=NOW))[pinned.name], 'qadalgan')

    def test_keep_min_protects_newest_even_when_all_are_ancient(self):
        files = [self.make(NOW - timedelta(days=2000 + d)) for d in range(5)]
        with override_settings(BACKUP_KEEP_MIN=3, BACKUP_KEEP_YEARS=1):
            bk.prune(now=NOW)
        self.assertEqual([p.exists() for p in files], [True, True, True, False, False])

    def test_keep_days_zero_disables_pruning(self):
        self.daily(60)
        with override_settings(BACKUP_KEEP_DAYS=0):
            self.assertEqual(bk.prune(now=NOW), [])
        self.assertEqual(len(self.left()), 60)

    def test_years_limit_drops_older_than_n_years(self):
        old = self.make(NOW - timedelta(days=3 * 365 + 20))
        recent_year = self.make(NOW - timedelta(days=400))
        self.make(NOW - timedelta(days=1))
        with override_settings(BACKUP_KEEP_MIN=1, BACKUP_KEEP_YEARS=2):
            removed = bk.prune(now=NOW)
        self.assertEqual(removed, [old.name])
        self.assertTrue(recent_year.exists())

    def test_zero_weeks_or_months_collapse_tiers(self):
        self.daily(120)
        with override_settings(BACKUP_KEEP_MIN=1, BACKUP_KEEP_WEEKS=0, BACKUP_KEEP_MONTHS=12):
            bk.prune(now=NOW)
        mid = [w for w in self.left() if timedelta(days=14) <= NOW - w]
        self.assertEqual(len({(w.year, w.month) for w in mid}), len(mid))   # haftalik oyna yo'q — to'g'ridan-to'g'ri oylik

    def test_dry_run_deletes_nothing_and_foreign_files_are_ignored(self):
        self.daily(60)
        other = self.dir / 'notes.txt'
        other.write_text('mening faylim')
        with override_settings(BACKUP_KEEP_MIN=1):
            would = bk.prune(dry_run=True, now=NOW)
            self.assertEqual(len(self.left()), 60)
            self.assertEqual(sorted(bk.prune(now=NOW)), sorted(would))
        self.assertTrue(other.exists())
        self.assertFalse(any(self.dir.glob(f'{would[0][:-7]}*')))          # sidecar ham o'chadi

    def test_future_dated_backup_is_treated_as_recent(self):
        future = self.make(NOW + timedelta(days=2))
        with override_settings(BACKUP_KEEP_MIN=0):
            self.assertEqual(bk.prune(now=NOW), [])
        self.assertTrue(future.exists())


class DateLookupAndPinTests(PolicyBase):
    def setUp(self):
        super().setUp()
        for d in (5, 40, 100):
            self.make(NOW - timedelta(days=d, hours=10))

    def test_resolve_by_date_picks_latest_on_or_before(self):
        target = (NOW - timedelta(days=40)).strftime('%Y-%m-%d')            # shu kunning o'zida zaxira bor
        self.assertEqual(bk.parse_name(bk.resolve(target).name), NOW - timedelta(days=40, hours=10))
        between = (NOW - timedelta(days=60)).strftime('%Y-%m-%d')            # oraliqda — undan oldingisi
        self.assertEqual(bk.parse_name(bk.resolve(between).name), NOW - timedelta(days=100, hours=10))
        with self.assertRaisesRegex(bk.BackupError, 'eng eskisi'):
            bk.resolve('2000-01-01')
        with self.assertRaisesRegex(bk.BackupError, 'Sana noto‘g‘ri'):
            bk.find('2026-13-45')

    def test_resolve_by_exact_minute(self):
        when = NOW - timedelta(days=40, hours=10)
        self.assertEqual(bk.parse_name(bk.resolve(when.strftime('%Y-%m-%d %H:%M')).name), when)
        earlier = (when - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')
        self.assertEqual(bk.parse_name(bk.resolve(earlier).name), NOW - timedelta(days=100, hours=10))

    def test_find_returns_neighbours(self):
        before, after = bk.find((NOW - timedelta(days=60)).strftime('%Y-%m-%d'))
        self.assertEqual((before['when'], after['when']), (NOW - timedelta(days=100, hours=10), NOW - timedelta(days=40, hours=10)))

    def test_pin_updates_sidecar_and_offsite_copy(self):
        off = Path(self.tmp.name) / 'offsite'
        res = None
        with override_settings(BACKUP_COPY_TO=str(off)):
            res = bk.create()
            bk.pin(res['path'].name)
            for d in (self.dir, off):
                self.assertTrue(json.loads((d / (res['path'].name[:-7] + '.json')).read_text())['pinned'])
            self.assertTrue(json.loads((d / (res['path'].name[:-7] + '.json')).read_text())['sha256'])    # boshqa ma'lumot yo'qolmagan
            bk.pin(res['path'].name, False)
            self.assertFalse(json.loads((self.dir / (res['path'].name[:-7] + '.json')).read_text())['pinned'])

    def test_commands_plan_pin_find_and_restore_by_date(self):
        out = io.StringIO()
        newest = bk.create()['path']
        call_command('backup', '--plan', stdout=out)
        self.assertIn('kunlik', out.getvalue())
        self.assertIn('oylik', out.getvalue())
        call_command('backup', '--pin', newest.name, stdout=out)
        call_command('backup', '--list', stdout=out)
        self.assertIn('📌', out.getvalue())
        call_command('backup', '--find', (NOW - timedelta(days=60)).strftime('%Y-%m-%d'), stdout=out)
        self.assertIn('shu sanagacha eng yangisi', out.getvalue())
        Faculty.objects.create(slug='yangi', name={'uz': 'x'})
        today = datetime.now().strftime('%Y-%m-%d')
        call_command('restore', today, '--yes', '--no-safety', '--db-only', stdout=out)     # bugungi sana → shu paytda olingan nusxa
        self.assertEqual(self.names(), ['fa'])
