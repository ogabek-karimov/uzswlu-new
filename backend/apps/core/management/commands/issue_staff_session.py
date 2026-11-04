"""Xodim kabineti sessiyasi: HEMIS (my.gov) kirishidan keyin (yoki sinash uchun qo'lda) token beradi.

    python manage.py issue_staff_session 9300

Token `session` cookie'siga yoki `Authorization: Bearer <token>` sarlavhasiga qo'yiladi.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import StaffSession
from apps.hemis import get_client


class Command(BaseCommand):
    help = 'Xodim kabineti uchun sessiya tokenini yaratadi'

    def add_arguments(self, parser):
        parser.add_argument('hemis_id')
        parser.add_argument('--hours', type=int, default=None, help='Amal qilish muddati (soat)')

    def handle(self, *args, hemis_id, hours, **options):
        if not any(str(p['id']) == hemis_id for p in get_client().staff('uz')):
            raise CommandError(f'HEMIS’da {hemis_id} ID li xodim topilmadi')
        token = StaffSession.issue(hemis_id, hours)
        self.stdout.write(token)
        self.stderr.write(f'Cookie: {settings.STAFF_SESSION_COOKIE}={token}  yoki  Authorization: Bearer {token}')
