"""Zaxiradan tiklash (BAZA VA FAYLLAR ALMASHTIRILADI):

    docker compose stop backend nightly      # ochiq ulanishlar bazani bloklamasin
    docker compose run --rm backend python manage.py restore latest --yes
    docker compose up -d

Sanaga qarab: `restore 2026-08-15 --yes` — o'sha kungacha olingan eng yangi nusxa (`backup --find 2026-08-15` oldindan ko'rsatadi).

Tiklashdan oldin joriy holatdan `...-pre-restore.tar.gz` nusxasi olinadi (--no-safety bilan o'chiriladi).
Faqat baza: --db-only, faqat fayllar: --media-only. Tekshirib ko'rish uchun: `backup --verify FAYL`.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.core import backup as bk


class Command(BaseCommand):
    help = 'Zaxira nusxadan bazani va fayllarni tiklash'

    def add_arguments(self, parser):
        parser.add_argument('ref', help='latest, sana (2026-08-15 — shu kungacha bo‘lgan eng yangi nusxa), fayl nomi yoki to‘liq yo‘l')
        parser.add_argument('--yes', action='store_true', help='Tasdiqlash (usiz hech narsa o‘zgarmaydi)')
        parser.add_argument('--no-safety', action='store_true', help='Tiklashdan oldingi xavfsizlik nusxasi olinmasin')
        parser.add_argument('--db-only', action='store_true')
        parser.add_argument('--media-only', action='store_true')

    def handle(self, *args, ref, yes, no_safety, db_only, media_only, **o):
        if db_only and media_only:
            raise CommandError('--db-only va --media-only birga bo‘lmaydi')
        try:
            path = bk.resolve(ref)
            m = bk.verify(path)
            self.stdout.write(f"Nusxa: {path.name} — olingan {m['created']}, baza: {m['db']}, fayllar: {m['files']}")
            if not yes:
                raise CommandError('Joriy baza va fayllar shu nusxa bilan ALMASHTIRILADI. Davom etish uchun --yes qo‘shing.')
            res = bk.restore(path, safety=not no_safety, db=not media_only, media=not db_only)
        except bk.BackupError as exc:
            raise CommandError(str(exc)) from exc
        if res['safety']:
            self.stdout.write(f"Oldingi holat saqlandi: {res['safety']}")
        self.stdout.write(self.style.SUCCESS(f"Tiklandi. Fayl papkalari: {', '.join(res['media']) or '—'}"))
