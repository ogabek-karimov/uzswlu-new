"""Zaxira va tiklash: yaratish, tekshirish, tiklash (SQLite va PostgreSQL — qaysi baza bilan ishlayotgan bo'lsa), ko'chma JSON,
buzilgan arxiv, tozalash, qulf, xavfsizlik (yo'l almashtirish), kechki vazifa, buyruqlar."""
import io
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
    def _fake(self, days_ago: int):
        when = datetime.now() - timedelta(days=days_ago, minutes=1)
        self.dir.mkdir(parents=True, exist_ok=True)
        p = self.dir / f"uzswlu-{when:%Y%m%d-%H%M%S}.tar.gz"
        p.write_bytes(b'x')
        return p

    def test_prune_removes_old_but_keeps_minimum(self):
        files = [self._fake(d) for d in (1, 2, 20, 30, 40)]
        with override_settings(BACKUP_KEEP_DAYS=14, BACKUP_KEEP_MIN=3):
            removed = bk.prune()
        self.assertEqual(len(removed), 2)                       # 30 va 40 kunlik; 3 ta eng yangisi (1, 2, 20) qoladi
        self.assertTrue(all(f.exists() for f in files[:3]))

    def test_prune_never_deletes_newest_even_if_all_old(self):
        files = [self._fake(d) for d in (50, 60)]
        with override_settings(BACKUP_KEEP_DAYS=14, BACKUP_KEEP_MIN=0):
            bk.prune()
        self.assertTrue(files[0].exists())

    def test_prune_ignores_foreign_files(self):
        self._fake(1)
        other = self.dir / 'notes.txt'
        other.write_text('mening faylim')
        with override_settings(BACKUP_KEEP_DAYS=1, BACKUP_KEEP_MIN=0):
            bk.prune()
        self.assertTrue(other.exists())

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
