"""HEMIS'dan ma'lumotni olib bazaga yozish. Odatda o'zi `run_nightly` orqali KECHASI ishlaydi.

    python manage.py sync_hemis            # faqat tinch oynada (HEMIS_SYNC_WINDOW, sukut 01:00–05:00)
    python manage.py sync_hemis --force    # oynadan tashqarida ham (qo'lda, bilgan holda)
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.hemis.api import HemisApi, HemisError
from apps.hemis.models import HemisSnapshot
from apps.hemis.schedule import in_window, parse_window
from apps.hemis.sync import build_snapshot


class Command(BaseCommand):
    help = 'HEMIS’dan xodimlar, bo‘limlar va sonlarni olib bazaga yozadi (kechki oynada)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Tinch oynadan tashqarida ham ishga tushirish')

    def handle(self, *args, force=False, **opts):
        window = parse_window(settings.HEMIS_SYNC_WINDOW)
        now = timezone.localtime()
        if not force and not in_window(now, window):
            raise CommandError(f'Hozir ({now:%H:%M}) HEMIS’ga chiqilmaydi: tinch oyna {settings.HEMIS_SYNC_WINDOW}. '
                               'Zarur bo‘lsa --force bilan ishga tushiring.')
        if not HemisSnapshot.acquire():
            raise CommandError('Boshqa sinxronlash hozir ishlayapti (yoki yaqinda yiqilgan) — kuting.')
        try:
            snap = HemisSnapshot.load()
            api = HemisApi()
            try:
                data = build_snapshot(api)
            except HemisError as exc:
                HemisSnapshot.objects.filter(pk=1).update(error=str(exc))  # oldingi nusxa saqlanib qoladi
                raise CommandError(str(exc)) from exc
            snap.data, snap.synced_at, snap.error = data, timezone.now(), ''
            snap.save(update_fields=['data', 'synced_at', 'error'])
            self.stdout.write(self.style.SUCCESS(
                f"HEMIS: {len(data['staff'])} xodim, {len(data['faculties'])} fakultet, {len(data['staffDepartments'])} bo‘lim saqlandi "
                f"({api.requests} so‘rov)"))
        finally:
            HemisSnapshot.release()
