"""HEMIS'dan ma'lumotni olib bazaga yozish (har kuni, masalan cron'da 06:00):
    python manage.py sync_hemis
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.hemis.api import HemisApi, HemisError
from apps.hemis.models import HemisSnapshot
from apps.hemis.sync import build_snapshot


class Command(BaseCommand):
    help = 'HEMIS’dan xodimlar, bo‘limlar va sonlarni olib bazaga yozadi'

    def handle(self, *args, **opts):
        snap = HemisSnapshot.load()
        try:
            data = build_snapshot(HemisApi())
        except HemisError as exc:
            snap.error = str(exc)
            snap.save(update_fields=['error'])
            raise CommandError(str(exc)) from exc
        snap.data, snap.synced_at, snap.error = data, timezone.now(), ''
        snap.save()
        self.stdout.write(self.style.SUCCESS(
            f"HEMIS: {len(data['staff'])} xodim, {len(data['faculties'])} fakultet, {len(data['staffDepartments'])} bo‘lim saqlandi"))
