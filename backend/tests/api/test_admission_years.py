"""Qabul yillari: faol yil saytda, yangi yil nusxa bilan (qoralama), faol qilish → oldingisi arxiv (narxlar saqlanadi),
arxivni saytda ko'rsatish/yashirish, faol yilni o'chirib bo'lmaydi, menyu va sayt ma'lumotida yil avtomatik."""
from django.test import TestCase

from apps.accounts.models import User
from apps.api.builders_site import admission_out, menu_out, site_out
from apps.structure.models import AdmissionYear, Program
from tests.support import PASSWORD, api, jwt_for, loose


class AdmissionYearsTests(TestCase):
    def setUp(self):
        User.objects.create_user('ay_root', password=PASSWORD, role='superadmin', name='AY')
        with loose():
            self.h = jwt_for('ay_root')
        self.active = AdmissionYear.active()

    def test_full_cycle(self):
        old_year = self.active.year
        Program.objects.create(code='60230100', title={'uz': 'Ingliz filologiyasi'}, level='bachelor', in_admission=True, price={'uz': '20 mln'})

        # Yangi yil — qoralama, saytda faol yil o'zgarmaydi
        r = api('post', '/api/cms/admission-years', self.h, {'year': '2030/2031', 'copyFrom': self.active.pk})
        self.assertIn(r.status_code, (200, 201), r.content)
        new = AdmissionYear.objects.get(year='2030/2031')
        self.assertEqual(new.status, 'draft')
        self.assertEqual(admission_out('uz')['year'], old_year)
        self.assertEqual(site_out('uz')['admissionYear'], old_year)

        # Noto'g'ri yil formati
        self.assertEqual(api('post', '/api/cms/admission-years', self.h, {'year': '2030/2035'}).status_code // 100, 4)

        # Faol qilish → oldingisi arxiv, yo'nalish narxi saqlanadi
        self.assertEqual(api('patch', f'/api/cms/admission-years/{new.pk}', self.h, {'status': 'active'}).status_code, 200)
        self.active.refresh_from_db()
        self.assertEqual(self.active.status, 'archive')
        self.assertEqual(self.active.programs_snapshot[0]['price']['uz'], '20 mln')
        self.assertEqual(admission_out('uz')['year'], '2030/2031')
        self.assertEqual(site_out('uz')['admissionYear'], '2030/2031')

        # Narx keyin o'zgarsa ham arxiv eski narxni ko'rsatadi
        Program.objects.filter(code='60230100').update(price={'uz': '25 mln'})
        arch = admission_out('uz', self.active.slug)
        self.assertTrue(arch['archived'])
        self.assertEqual(arch['programs'][0]['price'], '20 mln')
        self.assertIn({'year': old_year, 'slug': self.active.slug}, admission_out('uz')['archive'])

        # Arxivni saytda yashirish
        api('patch', f'/api/cms/admission-years/{self.active.pk}', self.h, {'public': False})
        self.assertIsNone(admission_out('uz', self.active.slug))
        self.assertEqual(self.client.get(f'/api/admission?year={self.active.slug}').status_code, 404)

        # Faol yilni o'chirib bo'lmaydi
        self.assertEqual(api('delete', f'/api/cms/admission-years/{new.pk}', self.h).status_code // 100, 4)

    def test_menu_title_follows_active_year(self):
        from apps.pages.models import Page
        group = Page.objects.create(title={'uz': 'Abituriyentlar'}, template='group', in_menu=True, published=True)
        Page.objects.create(title={'uz': 'Qabul – 2026/2027'}, url='/qabul', template='link', parent=group, in_menu=True, published=True)
        AdmissionYear.objects.update(status='archive')
        AdmissionYear.objects.create(year='2031/2032', status='active')
        titles = [link['title'] for g in menu_out('uz') for link in g['links'] if link['url'] == '/qabul']
        self.assertEqual(titles, ['Qabul – 2031/2032'])


class PageRectorCardTests(TestCase):
    """Matnli sahifadagi rektor kartasi: Rahbariyat'dan (surat bo'lmasa ham), rektor almashsa o'zi yangilanadi; o'chirilsa — yo'q."""

    def test_rector_card_follows_leadership(self):
        from apps.api.builders_site import page_out
        from apps.content.models import Leader
        from apps.pages.models import Page
        p = Page.objects.create(title={'uz': 'Tarix'}, slug='tarix-test', template='text', body={'uz': '<p>Matn</p>'}, show_rector=True)
        Leader.objects.filter(kind='rector').delete()
        self.assertIsNone(page_out(p, 'uz')['rector'])
        Leader.objects.create(kind='rector', name='Birinchi Rektor', role={'uz': 'Rektor'})
        card = page_out(p, 'uz')['rector']
        self.assertEqual((card['name'], card['photo']), ('Birinchi Rektor', None))
        Leader.objects.filter(kind='rector').update(name='Yangi Rektor')
        self.assertEqual(page_out(p, 'uz')['rector']['name'], 'Yangi Rektor')
        p.show_rector = False
        self.assertIsNone(page_out(p, 'uz')['rector'])


class UnitHeadsTests(TestCase):
    """Bo'limlar kartalari: HEMIS'dan avtomatik + admin qo'shimchalari; sahifada yoqilgan bo'lsa, yashirilgani — yo'q."""

    def test_units_on_page(self):
        from apps.api.builders_site import page_out
        from apps.content.models import UnitHead
        from apps.pages.models import Page
        UnitHead.objects.all().delete()
        UnitHead.objects.create(name='A', position={'uz': 'Bo‘lim boshlig‘i'}, order=2)
        UnitHead.objects.create(name='B', position={'uz': 'Direktor'}, order=1, url='/x')
        UnitHead.objects.create(name='C', position={'uz': 'Yashirin'}, order=3, visible=False)
        p = Page.objects.create(title={'uz': 'Bo‘limlar'}, slug='bolimlar-test', template='text', body={'uz': '<p>.</p>'}, show_units=True)
        units = page_out(p, 'uz')['units']
        # HEMIS bo'limlari (avtomatik) + HEMIS'da topilmagan admin yozuvlari (tartib bo'yicha, yashirinlarsiz)
        self.assertTrue(all(u['url'].startswith('/staff?department=') for u in units if u['source'] == 'hemis' and u['url'] not in ('/x',)))
        self.assertEqual([(u['name'], u['url']) for u in units if u['source'] == 'admin'], [('B', '/x'), ('A', None)])
        p.show_units = False
        self.assertEqual(page_out(p, 'uz')['units'], [])
