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


class PageChildrenTests(TestCase):
    def test_children_cards_only_when_enabled(self):
        from apps.api.builders_site import page_out
        parent = Page.objects.create(slug='ota-test', title={'uz': 'Ota'}, template='text')
        Page.objects.create(slug='bola-1', title={'uz': 'Futbol'}, template='text', parent=parent, icon='goal', in_menu=False, order=2)
        Page.objects.create(slug='bola-0', title={'uz': 'Zakovat'}, template='text', parent=parent, icon='lightbulb', in_menu=False, order=1)
        Page.objects.create(slug='bola-yopiq', title={'uz': 'Yopiq'}, template='text', parent=parent, published=False)
        self.assertEqual(page_out(parent, 'uz')['children'], [])
        parent.show_children = True
        parent.save()
        kids = page_out(Page.objects.get(pk=parent.pk), 'uz')['children']
        self.assertEqual([(c['slug'], c['icon'], c['url']) for c in kids], [('bola-0', 'lightbulb', '/bola-0'), ('bola-1', 'goal', '/bola-1')])
        self.assertEqual(kids[0]['attachments'], [])

    def test_youth_club_seed_files_exist(self):
        import json
        from pathlib import Path
        from django.conf import settings
        data = Path(settings.BASE_DIR) / 'seed_data'
        seed = json.loads((data / 'youth_clubs.json').read_text(encoding='utf-8'))
        self.assertEqual(len(seed['clubs']), 8)
        for name in [d['file'] for c in seed['clubs'] for d in c['docs']] + [seed['yi']['file']]:
            self.assertTrue((data / 'files' / 'youth' / name).exists(), name)


class PageShowcaseTests(TestCase):
    def test_blocks_markers_and_parsing(self):
        from apps.api.builders_site import page_out
        from apps.core.html import restore_timeline
        self.assertEqual(restore_timeline('<p>[[kartalar]]</p><p>[[kartalar-3]]</p>'), '<!-- showcase:1 --><!-- showcase:3 -->')
        p = Page.objects.create(slug='sc-test', title={'uz': 'S'}, template='text', body={'uz': '<p>a</p><p>[[kartalar-2]]</p>'}, showcase={'blocks': [
            {'intro': {'uz': 'Tarkib'}, 'stats': {'uz': '7 | Koordinator\nnoto‘g‘ri qator'}, 'columns': [], 'outro': {}},
            {'intro': {}, 'stats': {}, 'columns': [{'title': {'uz': 'Klublar'}, 'icon': 'users-round', 'style': 'checks',
                                                   'items': {'uz': 'Zakovat — intellektual klub\n\nShaxmat'}}], 'outro': {'uz': 'Xulosa'}},
        ]})
        out = page_out(p, 'uz')
        self.assertIn('<!-- showcase:2 -->', out['body'])
        b1, b2 = out['showcase']
        self.assertEqual((b1['n'], b1['stats']), (1, [{'value': '7', 'label': 'Koordinator'}]))
        self.assertEqual(b2['columns'][0]['style'], 'checks')
        self.assertEqual(b2['columns'][0]['items'], [{'name': 'Zakovat', 'note': 'intellektual klub'}, {'name': 'Shaxmat', 'note': None}])
        self.assertEqual(b2['outro'], 'Xulosa')

    def test_old_single_shape_is_block_one(self):
        from apps.api.builders_site import showcase_out
        old = {'intro': {'uz': 'X'}, 'columns': [{'title': {'uz': 'K'}, 'icon': '', 'items': {'uz': 'a'}}]}
        self.assertEqual(showcase_out(old, 'uz')[0]['n'], 1)


class ShowcasePhotosTests(TestCase):
    def test_photos_only_block_and_admin_ids(self):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        from apps.api.builders_site import showcase_out
        from apps.core.models import Media
        from apps.panel.collections import showcase as clean_showcase
        buf = BytesIO()
        Image.new('RGB', (40, 30), 'red').save(buf, 'JPEG')
        m = Media(folder='posts', alt={'uz': 'Xona'}, file=SimpleUploadedFile('x.jpg', buf.getvalue(), content_type='image/jpeg'))
        m.save()
        data = clean_showcase({'blocks': [{'photos': [{'id': m.pk}, m.pk]}]})
        self.assertEqual(data['blocks'][0]['photos'], [m.pk])  # takror olib tashlandi
        out = showcase_out({'blocks': [{'photos': [m.pk, 99999]}]}, 'uz')
        self.assertEqual(len(out), 1)
        self.assertEqual([p['alt'] for p in out[0]['photos']], ['Xona'])  # yo'q fayl tashlab yuboriladi

    def test_many_columns_kept(self):
        from apps.panel.collections import showcase as clean_showcase
        cols = [{'title': {'uz': f'Davlat {i}'}, 'icon': 'globe', 'items': {'uz': 'X University'}} for i in range(17)]
        self.assertEqual(len(clean_showcase({'blocks': [{'columns': cols}]})['blocks'][0]['columns']), 17)
