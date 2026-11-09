"""Zaxira nusxa:

    python manage.py backup                 # hozir zaxira olish (+ tekshirish, eskilarini tozalash, BACKUP_COPY_TO ga nusxa)
    python manage.py backup --list          # mavjud nusxalar
    python manage.py backup --verify latest # butunligini tekshirish (yoki fayl nomi)
    python manage.py backup --status        # oxirgi zaxira yangimi? (eskirgan bo'lsa chiqish kodi 1 — monitoring uchun)
    python manage.py backup --no-media      # faqat baza
    python manage.py backup --plan          # qaysi nusxa nima uchun saqlanadi / qaysi biri o'chadi (hech narsa o'chirmaydi)
    python manage.py backup --pin FAYL      # nusxani qadash: hech qachon avtomatik o'chmaydi (--unpin — bekor qilish)
    python manage.py backup --find 2026-08-15   # shu sanaga eng yaqin nusxalar
Saqlash siyosati: oxirgi 14 kun — hammasi; keyin har haftadan, oydan, yildan bittadan (BACKUP_KEEP_* sozlamalari).
Tiklash: python manage.py restore <fayl|latest|2026-08-15> --yes
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
        parser.add_argument('--prune', action='store_true', help='Faqat siyosatga ko‘ra ortiqchalarini tozalash')
        parser.add_argument('--plan', action='store_true', help='Saqlash rejasini ko‘rsatish (--prune --dry-run bilan bir xil)')
        parser.add_argument('--pin', metavar='FAYL')
        parser.add_argument('--unpin', metavar='FAYL')
        parser.add_argument('--find', metavar='SANA', help='YYYY-MM-DD yoki "YYYY-MM-DD HH:MM"')
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
            if o['plan']:
                return self.show_plan()
            if o['pin'] or o['unpin']:
                path = bk.pin(o['pin'] or o['unpin'], value=bool(o['pin']))
                return self.stdout.write(self.style.SUCCESS(f"{path.name}: " + ('qadaldi — avtomatik o‘chirilmaydi' if o['pin'] else 'qadash bekor qilindi')))
            if o['find']:
                return self.show_find(o['find'])
            if o['prune']:
                removed = bk.prune()
                shown = ', '.join(removed[:5]) + (f' … (+{len(removed) - 5})' if len(removed) > 5 else '')
                return self.stdout.write(f'{len(removed)} ta ortiqcha zaxira o‘chirildi' + (f': {shown}' if removed else ''))
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
        self.show_plan(header=f'Papka: {bk.backup_dir()}')

    def show_plan(self, header=''):
        items = bk.retention()
        self.stdout.write(header or f'Papka: {bk.backup_dir()}  (kun {bk.settings.BACKUP_KEEP_DAYS} · hafta {bk.settings.BACKUP_KEEP_WEEKS} · oy {bk.settings.BACKUP_KEEP_MONTHS} · yil {bk.settings.BACKUP_KEEP_YEARS or "abadiy"})')
        if not items:
            return self.stdout.write('  (bo‘sh)')
        for b, reason in items:
            m = b['meta']
            mark = self.style.WARNING('o‘chadi') if reason is None else reason
            self.stdout.write(f"  {b['name']}  {size_label(b['size']):>9}  {m.get('db', '?'):7} {str(m.get('files', '?')):>4} fayl  {'📌 ' if m.get('pinned') else ''}{mark}")
        gone = sum(1 for _, r in items if r is None)
        self.stdout.write(f'  jami {len(items)} ta, tozalashda o‘chadi: {gone}')

    def show_find(self, ref):
        before, after = bk.find(ref)
        for title, b in (('shu sanagacha eng yangisi', before), ('shundan keyingi eng eskisi', after)):
            self.stdout.write(f"  {title}: " + (f"{b['name']} ({size_label(b['size'])})" if b else '—'))
        if before:
            self.stdout.write(f'  tiklash: manage.py restore {ref} --yes')

    def show_status(self):
        s = bk.status()
        if s['latest']:
            self.stdout.write(f"Oxirgi: {s['latest']['name']} ({s['age_hours']} soat oldin), jami {s['count']} ta")
        if not s['ok']:
            raise CommandError(s['reason'])
        self.stdout.write(self.style.SUCCESS('Zaxira yangi'))
