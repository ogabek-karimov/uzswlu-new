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
