"""HEMIS'ga va serverga bosim: tinch oyna, qulf, so'rov byudjeti, ketma-ket xatoda to'xtash, kechki jadval."""
import io
import json
import urllib.error
from datetime import date, datetime, time, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.hemis import guard
from apps.hemis.api import HemisApi, HemisError
from apps.hemis.models import HemisSnapshot
from apps.hemis.schedule import in_window, next_run, parse_time, parse_window, run_time, window_end

TZ = ZoneInfo('Asia/Tashkent')
WIN = parse_window('01:00-05:00')


def at(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=TZ)


class ScheduleTests(SimpleTestCase):
    def test_in_window(self):
        for hh, expected in ((0, False), (1, True), (3, True), (4, True), (5, False), (14, False), (23, False)):
            self.assertEqual(in_window(at(2026, 11, 9, hh, 30 if hh == 4 else 0), WIN), expected, hh)

    def test_window_crossing_midnight(self):
        w = parse_window('23:00-04:00')
        self.assertTrue(in_window(at(2026, 11, 9, 23, 30), w))
        self.assertTrue(in_window(at(2026, 11, 9, 2), w))
        self.assertFalse(in_window(at(2026, 11, 9, 12), w))

    def test_run_time_is_inside_window_deterministic_and_jittered(self):
        times = {run_time(date(2026, 11, d), parse_time('02:30'), 20, WIN, TZ) for d in range(1, 29)}
        for t in times:
            self.assertTrue(in_window(t, WIN))
            self.assertTrue(time(2, 30) <= t.time() <= time(2, 50))
        self.assertGreater(len({t.time() for t in times}), 10, 'har kuni har xil (HEMIS «soat»ga qarab zarba olmasin)')
        self.assertEqual(run_time(date(2026, 11, 9), parse_time('02:30'), 20, WIN, TZ), run_time(date(2026, 11, 9), parse_time('02:30'), 20, WIN, TZ))

    def test_jitter_never_pushes_out_of_window(self):
        t = run_time(date(2026, 11, 9), parse_time('04:50'), 60, WIN, TZ)
        self.assertTrue(in_window(t, WIN))

    def test_next_run_never_in_past_and_never_daytime(self):
        for hh in (0, 2, 3, 6, 12, 23):
            now = at(2026, 11, 9, hh, 15)
            n = next_run(now, parse_time('02:30'), 20, WIN)
            self.assertGreater(n, now)
            self.assertTrue(in_window(n, WIN), f'{hh}: {n}')
            self.assertLessEqual(n - now, timedelta(hours=26))

    def test_window_end(self):
        self.assertEqual(window_end(at(2026, 11, 9, 3), WIN), at(2026, 11, 9, 5))


def http_error(code, retry_after=None):
    headers = {'Retry-After': retry_after} if retry_after else {}
    return urllib.error.HTTPError('http://h/x', code, 'err', headers, io.BytesIO(b''))


def ok_response(payload):
    res = mock.MagicMock()
    res.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return res


@override_settings(HEMIS_REQUEST_DELAY=0.5, HEMIS_MAX_REQUESTS=10, HEMIS_MAX_CONSECUTIVE_FAILURES=3)
class PoliteClientTests(SimpleTestCase):
    def api(self):
        return HemisApi('http://hemis.test/rest/v1', 'tok', 5)

    def test_pauses_between_every_request_not_only_pages(self):
        clock = {'t': 100.0}
        sleeps = []
        api = self.api()
        with mock.patch('apps.hemis.api.time.monotonic', lambda: clock['t']), \
                mock.patch('apps.hemis.api.time.sleep', lambda s: (sleeps.append(s), clock.__setitem__('t', clock['t'] + s))), \
                mock.patch('urllib.request.urlopen', side_effect=lambda *a, **k: ok_response({'data': {'items': []}})):
            for _ in range(4):
                api.get('data/x')
        self.assertEqual(len(sleeps), 3)           # 1-so'rovdan oldin kutilmaydi, qolganlari orasida pauza
        self.assertTrue(all(s >= 0.49 for s in sleeps))

    def test_request_budget_stops_sync(self):
        api = self.api()
        with mock.patch('apps.hemis.api.time.sleep'), mock.patch('urllib.request.urlopen', side_effect=lambda *a, **k: ok_response({'data': {'items': []}})) as m:
            with self.assertRaisesRegex(HemisError, 'chegarasiga'):
                for _ in range(50):
                    api.get('data/x')
        self.assertEqual(m.call_count, 10)

    def test_consecutive_failures_abort_instead_of_hammering(self):
        api = self.api()
        with mock.patch('apps.hemis.api.time.sleep'), mock.patch('urllib.request.urlopen', side_effect=OSError('down')) as m:
            with self.assertRaises(HemisError):
                api.get('data/a')           # 3 urinish → 3 ta xato
            with self.assertRaisesRegex(HemisError, 'ketma-ket'):
                api.get('data/b')           # endi umuman so'rov yuborilmaydi
        self.assertEqual(m.call_count, 3)

    def test_success_resets_failure_counter(self):
        api = self.api()
        seq = [OSError('x'), OSError('x'), ok_response({'data': {'items': [1]}})]
        with mock.patch('apps.hemis.api.time.sleep'), mock.patch('urllib.request.urlopen', side_effect=seq):
            self.assertEqual(api.get('data/a')['items'], [1])
        self.assertEqual(api._failures, 0)

    def test_client_errors_are_not_retried(self):
        for code in (401, 403, 404):
            api = self.api()
            with mock.patch('apps.hemis.api.time.sleep'), mock.patch('urllib.request.urlopen', side_effect=http_error(code)) as m:
                with self.assertRaises(HemisError):
                    api.get('data/a')
            self.assertEqual(m.call_count, 1, code)

    def test_retry_after_is_honoured_and_capped(self):
        api = self.api()
        sleeps = []
        seq = [http_error(429, '7'), http_error(503, '9999'), ok_response({'data': {'items': []}})]
        with mock.patch('apps.hemis.api.time.sleep', side_effect=sleeps.append), mock.patch('urllib.request.urlopen', side_effect=seq):
            api.get('data/a')
        self.assertIn(7, sleeps)
        self.assertIn(120, sleeps)           # 9999 s so'ralsa ham 120 s dan oshmaydi


class SyncCommandTests(TestCase):
    def run_sync(self, now, **kw):
        out = io.StringIO()
        with mock.patch('apps.hemis.management.commands.sync_hemis.timezone.localtime', return_value=now):
            call_command('sync_hemis', stdout=out, **kw)
        return out.getvalue()

    def test_refuses_during_the_day(self):
        with override_settings(HEMIS_API_URL='http://h/rest', HEMIS_API_TOKEN='t'), mock.patch('apps.hemis.management.commands.sync_hemis.HemisApi') as api:
            with self.assertRaisesRegex(CommandError, 'tinch oyna'):
                self.run_sync(at(2026, 11, 9, 14))
            api.assert_not_called()           # HEMIS'ga umuman chiqilmadi

    def test_runs_in_window_force_overrides_and_lock_is_released(self):
        fake = {'staff': [], 'faculties': [], 'staffDepartments': []}
        with override_settings(HEMIS_API_URL='http://h/rest', HEMIS_API_TOKEN='t'), \
                mock.patch('apps.hemis.management.commands.sync_hemis.HemisApi'), \
                mock.patch('apps.hemis.management.commands.sync_hemis.build_snapshot', return_value=fake):
            self.assertIn('saqlandi', self.run_sync(at(2026, 11, 9, 2)))
            self.assertIn('saqlandi', self.run_sync(at(2026, 11, 9, 14), force=True))
        snap = HemisSnapshot.load()
        self.assertIsNone(snap.running_since)
        self.assertIsNotNone(snap.synced_at)

    def test_second_process_cannot_start_while_first_runs(self):
        self.assertTrue(HemisSnapshot.acquire())
        self.assertFalse(HemisSnapshot.acquire())
        with self.assertRaisesRegex(CommandError, 'ishlayapti'):
            self.run_sync(at(2026, 11, 9, 2))
        HemisSnapshot.release()
        self.assertTrue(HemisSnapshot.acquire())
        HemisSnapshot.release()

    def test_stale_lock_after_crash_is_taken_over(self):
        HemisSnapshot.load()
        HemisSnapshot.objects.filter(pk=1).update(running_since=timezone.now() - timedelta(hours=HemisSnapshot.LOCK_HOURS + 1))
        self.assertTrue(HemisSnapshot.acquire())
        HemisSnapshot.release()

    def test_failure_keeps_previous_snapshot_and_releases_lock(self):
        snap = HemisSnapshot.load()
        snap.data, snap.synced_at = {'staff': [{'id': '1'}]}, timezone.now()
        snap.save()
        with override_settings(HEMIS_API_URL='http://h/rest', HEMIS_API_TOKEN='t'), \
                mock.patch('apps.hemis.management.commands.sync_hemis.HemisApi'), \
                mock.patch('apps.hemis.management.commands.sync_hemis.build_snapshot', side_effect=HemisError('HEMIS javob bermadi')):
            with self.assertRaises(CommandError):
                self.run_sync(at(2026, 11, 9, 2))
        snap = HemisSnapshot.load()
        self.assertEqual(snap.data, {'staff': [{'id': '1'}]})      # eski ma'lumot butun
        self.assertIn('javob bermadi', snap.error)
        self.assertIsNone(snap.running_since)


class OAuthGlobalLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(HEMIS_OAUTH_GLOBAL_PER_MIN=3)
    def test_global_per_minute_cap(self):
        calls = []
        for _ in range(3):
            self.assertEqual(guard.call(lambda: calls.append(1) or 'ok'), 'ok')
        with self.assertRaises(guard.HemisUnavailable):
            guard.call(lambda: calls.append(1))
        self.assertEqual(len(calls), 3)    # to'rtinchi so'rov HEMIS'ga yetib bormadi


class NightlyTests(TestCase):
    def test_tasks_are_independent_and_clean_up(self):
        from apps.accounts.models import StaffSession
        from apps.core import nightly
        from apps.panel.models import LoginEvent, RevokedToken
        now = timezone.now()
        StaffSession.objects.create(hemis_id='1', token_hash='a' * 64, expires_at=now - timedelta(hours=1))
        StaffSession.objects.create(hemis_id='2', token_hash='b' * 64, expires_at=now + timedelta(hours=1))
        RevokedToken.objects.create(jti='old', expires_at=now - timedelta(hours=1))
        RevokedToken.objects.create(jti='live', expires_at=now + timedelta(hours=1))
        with override_settings(HEMIS_API_URL=''):
            res = nightly.run_all()
        self.assertTrue(res['hemis'].startswith('o‘tkazib'))
        self.assertEqual(list(RevokedToken.objects.values_list('jti', flat=True)), ['live'])
        self.assertEqual(list(StaffSession.objects.values_list('hemis_id', flat=True)), ['2'])
        self.assertNotIn('XATO', ' '.join(res.values()))

    def test_one_failing_task_does_not_stop_others(self):
        from apps.core import nightly
        with mock.patch.object(nightly, 'TASKS', [('a', mock.Mock(side_effect=RuntimeError('boom'))), ('b', lambda force=False: 'ok')]):
            res = nightly.run_all()
        self.assertEqual(res['b'], 'ok')
        self.assertTrue(res['a'].startswith('XATO'))

    def test_login_event_retention(self):
        from apps.core import nightly
        from apps.panel.models import LoginEvent
        old = LoginEvent.objects.create(username='x', result='success')
        LoginEvent.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=400))
        fresh = LoginEvent.objects.create(username='y', result='success')
        with override_settings(LOGIN_EVENT_RETENTION_DAYS=365):
            nightly.prune_login_events()
        self.assertFalse(LoginEvent.objects.filter(pk=old.pk).exists())
        self.assertTrue(LoginEvent.objects.filter(pk=fresh.pk).exists())
        LoginEvent.objects.filter(pk=fresh.pk).update(created_at=timezone.now() - timedelta(days=999))
        with override_settings(LOGIN_EVENT_RETENTION_DAYS=0):       # 0 — hech narsa o'chirilmaydi
            nightly.prune_login_events()
        self.assertTrue(LoginEvent.objects.filter(pk=fresh.pk).exists())

    def test_run_nightly_once_reports(self):
        out = io.StringIO()
        with override_settings(HEMIS_API_URL=''):
            call_command('run_nightly', '--once', stdout=out)
        self.assertIn('hemis:', out.getvalue())


class PanelHemisStatusTests(TestCase):
    """Admin panel HEMIS sahifasi: sinxronlash eskirganini/xatosini ko'rsatadi, xato matni faqat superadmin'ga."""

    def setUp(self):
        from apps.accounts.models import User
        from tests.support import PASSWORD, jwt_for, loose
        for role in ('superadmin', 'editor'):
            User.objects.create_user(f'h_{role}', password=PASSWORD, role=role, name=role)
        with loose():
            self.h = {r: jwt_for(f'h_{r}') for r in ('superadmin', 'editor')}
        self.old = (timezone.now() - timedelta(hours=40)).isoformat()
        snap = HemisSnapshot.load()
        snap.data = {'syncedAt': self.old, 'faculties': [], 'staff': [], 'staffDepartments': [], 'summary': {}}
        snap.synced_at, snap.error = timezone.now() - timedelta(hours=40), 'HEMIS javob bermadi: http://ichki-host/x'
        snap.save()

    def get(self, role):
        from tests.support import api
        with override_settings(HEMIS_API_URL='http://h/rest', HEMIS_API_TOKEN='t', HEMIS_CLIENT='apps.hemis.snapshot.SnapshotHemis'), \
                mock.patch('apps.hemis.snapshot.SnapshotHemis._data', new_callable=mock.PropertyMock, return_value=HemisSnapshot.load().data):
            return api('get', '/api/cms/panel/hemis', self.h[role]).json()

    def test_superadmin_sees_error_and_stale(self):
        body = self.get('superadmin')
        self.assertTrue(body['stale'])
        self.assertIn('javob bermadi', body['lastError'])

    def test_other_roles_never_see_internal_error(self):
        body = self.get('editor')
        self.assertTrue(body['stale'])
        self.assertIsNone(body['lastError'])

    def test_demo_data_is_not_reported_stale(self):
        from tests.support import api
        with override_settings(HEMIS_API_URL=''), \
                mock.patch('apps.hemis.snapshot.SnapshotHemis._data', new_callable=mock.PropertyMock, return_value=HemisSnapshot.load().data):
            body = api('get', '/api/cms/panel/hemis', self.h['superadmin']).json()
        self.assertFalse(body['stale'])
