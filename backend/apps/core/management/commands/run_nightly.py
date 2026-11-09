"""Kechki jadval ishga tushiruvchisi (cron/Celery o'rniga, faqat Python):

    python manage.py run_nightly            # doimiy: har kuni HEMIS_SYNC_AT (+ tasodifiy kechikish) da ishga tushadi
    python manage.py run_nightly --once     # hozir bir marta ishga tushirib chiqadi
    python manage.py run_nightly --once --only hemis --force

Qoidalar: jarayon qayta ishga tushsa darhol sinxronlamaydi (faqat jadvaldagi vaqtda); ish tinch oynadan tashqarida
boshlanmaydi; HEMIS yiqilsa oyna tugamaguncha 20 daqiqada bir marta, ko'pi bilan 3 marta qayta uriniladi.
"""
import signal
import time
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core import nightly
from apps.hemis.models import HemisSnapshot
from apps.hemis.schedule import in_window, next_run, parse_time, parse_window, window_end

RETRY_MINUTES, MAX_RETRIES = 20, 3


class Command(BaseCommand):
    help = 'Kechki vazifalar: HEMIS sinxronlash, eski sessiya va yozuvlarni tozalash'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')
        parser.add_argument('--only', choices=[n for n, _ in nightly.TASKS])
        parser.add_argument('--force', action='store_true', help='Oynadan tashqarida ham')

    def handle(self, *args, once=False, only=None, force=False, **opts):
        if once:
            return self.report(nightly.run_all(only, force))
        self.stop = False
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: setattr(self, 'stop', True))
        window = parse_window(settings.HEMIS_SYNC_WINDOW)
        at, jitter = parse_time(settings.HEMIS_SYNC_AT), settings.HEMIS_SYNC_JITTER_MINUTES
        self.stdout.write(f'Kechki jadval: {settings.HEMIS_SYNC_AT} (+≤{jitter} daqiqa), oyna {settings.HEMIS_SYNC_WINDOW}')
        snap = HemisSnapshot.objects.filter(pk=1).first()
        stale = not (snap and snap.synced_at) or timezone.now() - snap.synced_at > timedelta(hours=30)
        if settings.HEMIS_API_URL and stale and in_window(timezone.localtime(), window):
            self.stdout.write('Kechagi sinxronlash o‘tkazib yuborilgan — oyna ichida ekan, hozir bajariladi')
            self.run_with_retries(window)  # faqat tinch oyna ichida; kunduzi qayta ishga tushsa — kutadi
        while not self.stop:
            when = next_run(timezone.localtime(), at, jitter, window)
            self.stdout.write(f'Keyingi ishga tushish: {when:%Y-%m-%d %H:%M}')
            if not self.sleep_until(when):
                break
            self.run_with_retries(window)

    def sleep_until(self, when) -> bool:
        while not self.stop and timezone.localtime() < when:
            time.sleep(min(30, max(1, (when - timezone.localtime()).total_seconds())))  # SIGTERM tez ishlashi uchun qisqa uxlaymiz
        return not self.stop

    def run_with_retries(self, window):
        results = nightly.run_all()
        self.report(results)
        for _ in range(MAX_RETRIES):
            if not results['hemis'].startswith('XATO') or self.stop:
                return
            retry_at = timezone.localtime() + timedelta(minutes=RETRY_MINUTES)
            if not in_window(retry_at, window) or retry_at >= window_end(timezone.localtime(), window):
                self.stdout.write('Oyna tugayapti — HEMIS qayta urinilmaydi, ertaga')
                return
            if not self.sleep_until(retry_at):
                return
            results = nightly.run_all('hemis')
            self.report(results)

    def report(self, results):
        for name, text in results.items():
            self.stdout.write(f'  {name}: {text}')
        snap = HemisSnapshot.objects.filter(pk=1).first()
        if snap and snap.synced_at:
            self.stdout.write(f'  oxirgi muvaffaqiyatli HEMIS nusxasi: {timezone.localtime(snap.synced_at):%Y-%m-%d %H:%M}')
