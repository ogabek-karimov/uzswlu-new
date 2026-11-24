"""Savat: birinchi o'chirish — savatga, savatdagini o'chirish — butunlay (versiyalari bilan); ommaviy tozalash; jurnalda «purge»."""
from django.utils import timezone

from apps.content.models import Post
from apps.core.models import Activity
from apps.panel.models import Version
from tests.panel.test_collections import PanelBase


class TrashTests(PanelBase):
    def make(self, title, trashed=False, type_='news'):
        return Post.objects.create(type=type_, title={'uz': title}, status='published', deleted_at=timezone.now() if trashed else None)

    def test_delete_twice_trash_then_purge(self):
        p = self.make('Bir')
        self.send('patch', f'/api/cms/posts/{p.pk}', {'title': {'uz': 'Bir (tahrir)'}})  # versiya yoziladi
        self.assertTrue(Version.objects.filter(entity='posts', entity_id=str(p.pk)).exists())
        self.assertEqual(self.client.delete(f'/api/cms/posts/{p.pk}').status_code, 200)
        self.assertIsNotNone(Post.objects.get(pk=p.pk).deleted_at)  # savatda
        self.assertEqual(self.client.delete(f'/api/cms/posts/{p.pk}?trash=true').status_code, 200)
        self.assertFalse(Post.objects.filter(pk=p.pk).exists())
        self.assertFalse(Version.objects.filter(entity='posts', entity_id=str(p.pk)).exists())
        self.assertTrue(Activity.objects.filter(action='purge', entity_id=str(p.pk)).exists())

    def test_empty_trash_only_removes_trashed_of_that_type(self):
        a, b = self.make('A', trashed=True), self.make('B', trashed=True)
        live = self.make('Tirik')
        other = self.make('E’lon', trashed=True, type_='announcements')
        r = self.client.delete('/api/cms/posts?trash=true&where[and][0][type][equals]=news&where[and][1][deletedAt][exists]=true')
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.assertLessEqual({a.pk, b.pk}, {d['id'] for d in self.j(r)['docs']})
        self.assertFalse(Post.objects.filter(type='news', deleted_at__isnull=False).exists())  # savat (yangiliklar) bo'sh
        self.assertTrue(Post.objects.filter(pk=live.pk, deleted_at__isnull=True).exists())
        self.assertTrue(Post.objects.filter(pk=other.pk).exists())
