"""Zaxira nusxa:

    python manage.py backup                 # hozir zaxira olish (+ tekshirish, eskilarini tozalash, BACKUP_COPY_TO ga nusxa)
    python manage.py backup --list          # mavjud nusxalar
    python manage.py backup --verify latest # butunligini tekshirish (yoki fayl nomi)
    python manage.py backup --status        # oxirgi zaxira yangimi? (eskirgan bo'lsa chiqish kodi 1 — monitoring uchun)
    python manage.py backup --no-media      # faqat baza
Tiklash: python manage.py restore <fayl|latest> --yes
"""
import re

from django.core.management.base import BaseCommand, CommandError

from apps.core import backup as bk
from apps.core.utils import size_label


class Command(BaseCommand):
    help = 'Baza va yuklangan fayllarning zaxira nusxasini olish / tekshirish / ro‘yxati'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--verify', metavar='FAYL', nargs='?', const='latest')
        parser.add_argument('--status', action='store_true')
        parser.add_argument('--prune', action='store_true', help='Faqat eskilarini tozalash')
        parser.add_argument('--no-media', action='store_true')
        parser.add_argument('--no-copy', action='store_true', help='BACKUP_COPY_TO ga nusxa olinmasin')
        parser.add_argument('--label', default='', help='Fayl nomiga qo‘shiladi (kichik lotin harflar va -)')

    def handle(self, *args, **o):
        try:
            if o['list']:
                return self.show_list()
            if o['status']:
                return self.show_status()
            if o['verify']:
                path = bk.resolve(o['verify'])
                m = bk.verify(path)
                return self.stdout.write(self.style.SUCCESS(f"OK: {path.name} — baza: {m['db']}, {m['files']} fayl, {m['created']}"))
            if o['prune']:
                removed = bk.prune()
                return self.stdout.write(f'{len(removed)} ta eski zaxira o‘chirildi' + (': ' + ', '.join(removed) if removed else ''))
            if o['label'] and not re.fullmatch(r'[a-z-]{1,20}', o['label']):
                raise CommandError('--label faqat kichik lotin harflar va "-" (≤20 belgi)')
            res = bk.create(o['label'], media=False if o['no_media'] else None, copy=not o['no_copy'])
            bk.verify(res['path'])
            removed = bk.prune()
            self.stdout.write(self.style.SUCCESS(f"Zaxira tayyor: {res['path']}"))
            self.stdout.write(f"  hajmi {size_label(res['size'])}, baza: {res['db']}, fayllar: {res['files']}, eskisi o‘chirildi: {len(removed)}")
            for p in res['copied']:
                self.stdout.write(f'  nusxa: {p}')
            if res['copy_error']:
                raise CommandError(f"Zaxira olindi, lekin ikkinchi joyga nusxa OLINMADI: {res['copy_error']}")
        except bk.BackupError as exc:
            raise CommandError(str(exc)) from exc

    def show_list(self):
        items = bk.list_backups()
        self.stdout.write(f'Papka: {bk.backup_dir()}')
        if not items:
            return self.stdout.write('  (bo‘sh)')
        for b in items:
            m = b['meta']
            self.stdout.write(f"  {b['name']}  {size_label(b['size']):>9}  {m.get('db', '?'):7} {m.get('files', '?')} fayl")

    def show_status(self):
        s = bk.status()
        if s['latest']:
            self.stdout.write(f"Oxirgi: {s['latest']['name']} ({s['age_hours']} soat oldin), jami {s['count']} ta")
        if not s['ok']:
            raise CommandError(s['reason'])
        self.stdout.write(self.style.SUCCESS('Zaxira yangi'))
