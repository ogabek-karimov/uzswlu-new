"""«Toshkent haqida» / «Kontingent» sahifalarini o'chiruvchi migratsiya (0002_remove_toshkent_kontingent)."""
import importlib

from django.apps import apps
from django.test import TestCase

from apps.pages.models import Page

migration = importlib.import_module('apps.pages.migrations.0002_remove_toshkent_kontingent')


class RemoveToshkentKontingentTests(TestCase):
    def make(self, slug, parent=None):
        return Page.objects.create(template='text', title={'uz': slug}, slug=slug, parent=parent)

    def test_removes_leaf_pages_only(self):
        group = Page.objects.create(template='group', title={'uz': 'G'}, group_key='g')
        self.make('toshkent-haqida', group)
        self.make('kontingent', group)
        keep = self.make('hamkorlarimiz', group)
        migration.remove(apps, None)
        self.assertEqual(list(Page.objects.filter(parent=group)), [keep])

    def test_page_with_children_is_kept(self):
        parent = self.make('kontingent')
        self.make('ichki', parent)
        migration.remove(apps, None)
        self.assertTrue(Page.objects.filter(slug='kontingent').exists())


migration3 = importlib.import_module('apps.pages.migrations.0003_graduates_text_page')


class GraduatesTextPageTests(TestCase):
    def test_pdf_link_becomes_text_page(self):
        group = Page.objects.create(template='group', title={'uz': 'G'}, group_key='activity')
        link = Page.objects.create(template='link', title={'uz': 'Universitet bitiruvchilari haqida'}, parent=group, url='https://x/y.pdf')
        migration3.to_text_page(apps, None)
        link.refresh_from_db()
        self.assertEqual((link.template, link.slug, link.url), ('text', 'universitet-bitiruvchilari-haqida', ''))
        self.assertIn('bitiruvchilar.webp', link.body['uz'])

    def test_already_changed_page_is_untouched(self):
        Page.objects.create(template='text', title={'uz': 'Boshqa'}, slug='universitet-bitiruvchilari-haqida', body={'uz': '<p>mening</p>'})
        Page.objects.create(template='link', title={'uz': 'Universitet bitiruvchilari haqida'}, url='https://x/y.pdf')
        migration3.to_text_page(apps, None)
        self.assertEqual(Page.objects.get(slug='universitet-bitiruvchilari-haqida').body['uz'], '<p>mening</p>')
