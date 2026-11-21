"""Namunaviy vazifalar (lokal sinov): demo xodimlar (dekan, kafedra mudiri, o'qituvchi, xodim) o'rtasida."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.accounts.models import StaffTask
from apps.api.builders_staff import find_person

DEAN, CHAIR, TEACHER, STAFF = '8654', '7768', '7792', '7909'

# (kim beradi, kimga, nomi, izoh, necha kundan keyin, bajarilganmi)
DEMO = [
    (DEAN, CHAIR, 'Kafedra yillik hisobotini topshirish', 'Ilmiy ish va nashrlar bo‘yicha jadval bilan.', 5, False),
    (DEAN, CHAIR, 'Yangi o‘quv yili dars jadvalini tasdiqlash', '', -2, False),
    (DEAN, CHAIR, 'Bitiruv ishlari mavzulari ro‘yxati', 'Hamma o‘qituvchi bo‘yicha.', -6, True),
    (CHAIR, TEACHER, 'Ish dasturini yangilash', 'Yangi standart bo‘yicha, PDF ko‘rinishida.', 3, False),
    (CHAIR, TEACHER, 'Ochiq dars o‘tkazish', 'Mavzu va vaqtni kelishib oling.', 10, False),
    (CHAIR, STAFF, 'Kafedra yig‘ilishi bayonnomasi', '', 1, False),
    (TEACHER, TEACHER, 'Maqolani jurnalga yuborish', '', 14, False),
    (STAFF, STAFF, 'Hujjatlarni arxivga topshirish', '', 7, False),
]


class Command(BaseCommand):
    help = 'Namunaviy kabinet vazifalarini yaratadi (faqat sinov uchun; mavjudlarini o‘chirmaydi)'

    def handle(self, *args, **opts):
        made = 0
        for author, assignee, title, note, days, done in DEMO:
            if StaffTask.objects.filter(author_id=author, assignee_id=assignee, title=title).exists():
                continue
            a, b = find_person(author, 'uz'), find_person(assignee, 'uz')
            if not a or not b:
                self.stderr.write(f'HEMIS namunasida topilmadi: {author} yoki {assignee}')
                continue
            StaffTask.objects.create(title=title, note=note, due=date.today() + timedelta(days=days), status='done' if done else 'open',
                                     assignee_id=assignee, assignee_name=b['name'], author_id=author, author_name=a['name'])
            made += 1
        self.stdout.write(f'{made} ta vazifa yaratildi')
