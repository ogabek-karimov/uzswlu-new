"""Kontent o'zgarganda Nuxt/nginx keshini yangilash (apps/api/edge.py)."""
from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from apps.api import edge
from apps.api.common import bump_content_version


class _Resp:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self, n=-1): return b''


ON = dict(EDGE_PURGE_URL='http://frontend:3000/api/_purge', EDGE_REFRESH_URLS=['http://nginx/', 'http://nginx/ru'],
          EDGE_REFRESH_TOKEN='r-secret', API_TOKEN='tok-new,tok-old')


class EdgeRefreshTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    @override_settings(EDGE_PURGE_URL='', EDGE_REFRESH_URLS=[], EDGE_REFRESH_TOKEN='')
    def test_disabled_does_nothing(self):
        with mock.patch.object(edge.threading, 'Thread') as th:
            self.assertFalse(edge.schedule_edge_refresh())
            bump_content_version()
        th.assert_not_called()

    @override_settings(**ON)
    def test_refresh_calls_nuxt_then_nginx_with_secrets(self):
        calls = []
        def fake(req, timeout=0):
            calls.append((req.get_method(), req.full_url, dict(req.header_items())))
            return _Resp()
        with mock.patch('urllib.request.urlopen', fake):
            out = edge.refresh_edge()
        self.assertEqual(out, {'purge': True, 'refreshed': 2})
        self.assertEqual([c[0] for c in calls], ['POST', 'GET', 'GET'])
        self.assertEqual(calls[0][2]['Authorization'], 'Bearer tok-new')      # API_TOKEN ning birinchisi
        self.assertEqual(calls[1][2]['X-cache-refresh'], 'r-secret')

    @override_settings(**ON)
    def test_failure_does_not_raise(self):
        with mock.patch('urllib.request.urlopen', side_effect=OSError('down')):
            out = edge.refresh_edge()
        self.assertEqual(out, {'purge': False, 'refreshed': 0})

    @override_settings(**ON)
    def test_burst_of_saves_is_one_refresh(self):
        with mock.patch.object(edge.threading, 'Thread') as th:
            results = [edge.schedule_edge_refresh() for _ in range(5)]
        self.assertEqual(results, [True, False, False, False, False])
        self.assertEqual(th.call_count, 1)

    @override_settings(**ON)
    def test_bump_schedules_refresh(self):
        with mock.patch.object(edge, 'schedule_edge_refresh') as sch:
            bump_content_version()
        sch.assert_called_once()
