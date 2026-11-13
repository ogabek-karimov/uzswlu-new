"""Ochiq javoblar keshi: to'dan himoya — bir xil so'rovlar bazaga bir vaqtda urilmaydi (CachedGetMixin._cached_or_build)."""
import threading
import time

from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.response import Response

from apps.api import common
from apps.api.common import CACHE_FORMAT, CachedGetMixin


class Slow(CachedGetMixin):
    """Bazaga boradigan view o'rnida: qancha marta yig'ilganini sanaydi."""

    def __init__(self, delay=0.15, status=200, fail=False):
        self.calls, self.delay, self.status, self.fail = 0, delay, status, fail
        self.lock = threading.Lock()

    def get(self, request, *args, **kwargs):
        with self.lock:
            self.calls += 1
            n = self.calls
        time.sleep(self.delay)
        if self.fail:
            raise RuntimeError('baza yiqildi')
        return Response({'n': n}, status=self.status)

    def fetch(self, key='pub:test'):
        return self._cached_or_build(key, 60, None, (), {})


class StampedeTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_cold_cache_one_build_for_many_requests(self):
        view, results = Slow(), []
        threads = [threading.Thread(target=lambda: results.append(view.fetch().data)) for _ in range(30)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(view.calls, 1)
        self.assertEqual(len(results), 30)
        self.assertTrue(all(r == {'n': 1} for r in results))

    def test_fresh_entry_served_without_building(self):
        view = Slow()
        view.fetch()
        view.fetch()
        view.fetch()
        self.assertEqual(view.calls, 1)

    def test_stale_entry_served_while_another_request_rebuilds(self):
        view = Slow()
        cache.set('pub:test', (CACHE_FORMAT, {'n': 'eski'}, time.time() - 1), 300)
        cache.add('pub:test:lock', 1, 15)           # boshqa so'rov hozir yangilayapti
        self.assertEqual(view.fetch().data, {'n': 'eski'})
        self.assertEqual(view.calls, 0)

    def test_stale_entry_rebuilt_by_exactly_one_request(self):
        view, results = Slow(), []
        cache.set('pub:test', (CACHE_FORMAT, {'n': 'eski'}, time.time() - 1), 300)
        threads = [threading.Thread(target=lambda: results.append(view.fetch().data)) for _ in range(20)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(view.calls, 1)
        self.assertEqual(view.fetch().data, {'n': 1})   # keyingi so'rov yangi nusxani oladi

    def test_failed_build_releases_lock_and_is_not_cached(self):
        view = Slow(delay=0, fail=True)
        with self.assertRaises(RuntimeError):
            view.fetch()
        self.assertIsNone(cache.get('pub:test'))
        self.assertTrue(cache.add('pub:test:lock', 1, 15))   # qulf bo'sh

    def test_non_200_not_cached(self):
        view = Slow(delay=0, status=404)
        view.fetch()
        view.fetch()
        self.assertEqual(view.calls, 2)

    def test_waiter_gives_up_and_builds_itself_if_lock_owner_vanishes(self):
        view = Slow(delay=0)
        cache.add('pub:test:lock', 1, 60)           # egasi yo'qolgan qulf
        old = common.CACHE_LOCK_WAIT
        common.CACHE_LOCK_WAIT = 0.2
        self.addCleanup(setattr, common, 'CACHE_LOCK_WAIT', old)
        self.assertEqual(view.fetch().data, {'n': 1})
        self.assertEqual(view.calls, 1)

    def test_old_cache_format_is_ignored(self):
        view = Slow(delay=0)
        cache.set('pub:test', {'eski': 'format'}, 300)   # joriy formatdan oldingi yozuv
        self.assertEqual(view.fetch().data, {'n': 1})
