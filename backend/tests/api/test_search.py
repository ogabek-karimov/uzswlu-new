"""Sayt qidiruvi (GET /search): nima qidiriladi va yozuv farqlari (tutuq, yangi alifbo, kirill, qo'shimchalar)."""
from django.test import SimpleTestCase
from django.utils import timezone

from apps.api.search import norm, search_out, variants
from apps.content.models import Post
from apps.hemis import get_client
from apps.pages.models import Page
from apps.structure.models import Faculty
from tests.support import SeededTestCase


class NormalizeTests(SimpleTestCase):
    def test_apostrophes_and_alphabets_fold_to_one_form(self):
        same = {norm(x) for x in ("O‘quv binolari", "o'quv binolari", 'oʻquv binolari', 'oquv binolari', 'Öquv binolari', 'Ўқув бинолари')}
        self.assertEqual(len(same), 1, same)
        self.assertEqual(norm('Şahar çiroqlari'), norm('Shahar chiroqlari'))
        self.assertEqual(norm('ЕР'), norm('yer'))  # o'zbek kirillida so'z boshidagi "е" = "ye"

    def test_suffixes_are_trimmed(self):
        self.assertIn('kafedra', variants('kafedralari'))
        self.assertIn('fakultet', variants('fakultetlari'))
        self.assertIn('kafedr', variants(norm('кафедры').strip()))
        self.assertEqual(variants('60230100'), ['60230100'])  # raqamlar qisqartirilmaydi


class SearchCoverageTests(SeededTestCase):
    def find(self, q, lang='uz', kind=None):
        return search_out(lang, q, kind, 1, 50)

    def titles(self, q, **kw):
        return [i['title'] for i in self.find(q, **kw)['items']]

    def test_page_body_text_is_searched(self):
        page = Page.objects.filter(template='text', published=True, in_menu=True).first()
        page.body = {'uz': '<p>Bu yerda noyobsöz-qidiruv uchun maxsus matn bor.</p>'}
        page.save()
        self.assertIn(page.title['uz'], self.titles('noyobsoz'))

    def test_pdf_menu_links_are_documents(self):
        page = Page.objects.filter(template='text', published=True, in_menu=True).first()
        Page.objects.create(template='link', title={'uz': 'Sinov nizomi PDF'}, url='https://example.com/sinov-nizomi.pdf', parent=page.parent, order=99)
        r = self.find('sinov nizomi')
        self.assertEqual(r['counts']['documents'], 1)
        self.assertEqual(r['items'][0]['kind'], 'documents')

    def test_faculties_programs_and_staff(self):
        faculty = Faculty.objects.first()
        self.assertIn(faculty.name['uz'], self.titles(faculty.name['uz']))
        person = get_client().staff('uz')[0]
        surname = person['name'].split()[0]
        r = self.find(surname.lower())
        self.assertGreater(r['counts']['people'], 0)
        self.assertTrue(any(i['url'] == f"/teacher/{person['id']}" for i in r['items']))

    def test_cyrillic_query_finds_latin_text(self):
        self.assertTrue(self.titles('кафедра'), 'kirillcha so‘rov lotin matnni topishi kerak')

    def test_post_body_and_hidden_posts(self):
        post = Post.objects.create(type='news', slug='qidiruv-sinov', title={'uz': 'Oddiy sarlavha'}, body={'uz': '<p>Ichida yashirinsoz bor</p>'},
                                   status='published', published_at=timezone.now())
        self.assertEqual(self.titles('yashirinsoz', kind='news'), ['Oddiy sarlavha'])
        post.hidden = True
        post.save()
        self.assertEqual(self.find('yashirinsoz')['total'], 0)

    def test_view_accepts_people_type(self):
        res = self.client.get('/api/search', {'q': 'kafedra', 'type': 'people', 'lang': 'uz'})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(set(data['counts']), {'pages', 'news', 'documents', 'people'})
        self.assertTrue(all(i['kind'] == 'people' for i in data['items']))

    def test_quick_links_are_searched(self):
        # «Korporativ poçta» — menyuda emas, bosh sahifadagi «Tezkor xizmatlar»da
        self.assertIn('/korporativ-pochta', [i['url'] for i in self.find('korporativ')['items']])
