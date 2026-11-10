"""Loyiha qo'llanmasini yig'ish: docs/reference.md (koddan) va docs/index.html (hamma .md dan, qidiruv bilan).

    cd backend && python manage.py build_docs            # yangilash
    cd backend && python manage.py build_docs --check    # eskirgan bo'lsa xato (CI/test)
Docker'da docs/ papkasi yo'q — buyruqni lokal (repo ildizi ko'rinadigan joyda) ishga tushiring.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.core import docsgen


class Command(BaseCommand):
    help = 'Qo‘llanmani yig‘ish: docs/reference.md (koddan avtomatik) va docs/index.html (qidiriladigan bitta fayl)'

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Hech narsa yozmaydi; eskirgan bo‘lsa xato bilan tugaydi')

    def handle(self, *args, check, **o):
        if not docsgen.REPO.joinpath('docs').exists() and check:
            raise CommandError('docs/ papkasi topilmadi (Docker ichidamisiz? Repo ildizidan ishga tushiring)')
        stale = docsgen.write_all(check=check)
        if check and stale:
            raise CommandError('Eskirgan: ' + ', '.join(stale) + ' — `cd backend && python manage.py build_docs` ni ishga tushiring va natijani commit qiling.')
        self.stdout.write(self.style.SUCCESS('Qo‘llanma yangilandi: ' + (', '.join(stale) if stale else 'o‘zgarish yo‘q')))
