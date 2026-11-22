"""Sahifadagi bo'lim xodimlari (masalan, «Axborot-resurs markazi»): HEMIS'dan avtomatik, admin zaxirasi, karta kontaktlari."""
from django.core.cache import cache
from django.test import TestCase

from apps.api.builders_staff import department_staff_out
from apps.hemis import get_client
from apps.pages.models import Page
from apps.structure.models import StaffProfile


class PageStaffTests(TestCase):
    def setUp(self):
        cache.clear()
        client = get_client()
        self.dept = next(d for d in client.staff_departments('uz') if d.get('group') == 'unit')
        staff = client.staff('uz')
        self.members = [p for p in staff if any(str(e['department']['id']) == str(self.dept['id']) for e in p['employments'])]
        self.outsider = next(p for p in staff if p not in self.members)

    def test_by_id_or_uzbek_name(self):
        by_id = [p['id'] for p in department_staff_out(str(self.dept['id']), 'uz')]
        self.assertEqual(len(by_id), len(self.members))
        self.assertEqual([p['id'] for p in department_staff_out(self.dept['name'], 'uz')], by_id)
        self.assertEqual(department_staff_out('mavjud emas', 'uz'), [])

    def test_admin_extra_after_department_no_duplicates(self):
        member = str(self.members[0]['id'])
        out = department_staff_out(str(self.dept['id']), 'uz', [str(self.outsider['id']), member, 'yoq-id'])
        self.assertEqual(out[-1]['id'], str(self.outsider['id']))
        self.assertEqual(len(out), len(self.members) + 1)

    def test_only_office_phone_never_mobile(self):
        hid = str(self.members[0]['id'])
        StaffProfile.objects.create(hemis_id=hid, contacts=[{'type': 'mobile', 'value': '+998 90 000 00 00'}])
        card = next(p for p in department_staff_out(str(self.dept['id']), 'uz') if p['id'] == hid)
        self.assertIsNone(card['phone'])  # mobil — ko'rinmaydi
        StaffProfile.objects.filter(hemis_id=hid).update(contacts=[{'type': 'mobile', 'value': '+998 90 000 00 00'}, {'type': 'phone', 'value': '71-230-13-56'}])
        card = next(p for p in department_staff_out(str(self.dept['id']), 'uz') if p['id'] == hid)
        self.assertEqual(card['phone'], '71-230-13-56')  # ichki telefon
        card = next(p for p in department_staff_out(str(self.dept['id']), 'uz', contacts={hid: {'phone': '1016'}}, hours='8:30–16:30') if p['id'] == hid)
        self.assertEqual((card['phone'], card['hours']), ('1016', '8:30–16:30'))  # admin kiritgani ustun

    def test_hidden_staff_not_shown(self):
        hid = str(self.members[0]['id'])
        StaffProfile.objects.create(hemis_id=hid, hidden=True)
        self.assertNotIn(hid, [p['id'] for p in department_staff_out(str(self.dept['id']), 'uz', [hid])])

    def test_page_api_has_staff(self):
        Page.objects.update_or_create(slug='axborot-resurs-markazi', defaults={'title': {'uz': 'ARM'}, 'template': 'text', 'staff_department': self.dept['name']})
        from apps.api.builders_site import page_out
        page = page_out(Page.objects.get(slug='axborot-resurs-markazi'), 'uz')
        self.assertEqual(len(page['staff']), len(self.members))
        self.assertIn('position', page['staff'][0])


class PageCtaTests(TestCase):
    def test_cta_only_with_url_and_label(self):
        from apps.api.builders_site import page_out
        p = Page.objects.create(slug='cta-test', title={'uz': 'T'}, template='text', cta_url='https://uzlib.uz/',
                                cta_title={'uz': 'Kutubxona'}, cta_label={'uz': 'Oçiş'})
        self.assertEqual(page_out(p, 'uz')['cta'], {'title': 'Kutubxona', 'text': None, 'label': 'Oçiş', 'url': 'https://uzlib.uz/'})
        p.cta_label = {}
        p.save()
        self.assertIsNone(page_out(p, 'uz')['cta'])
