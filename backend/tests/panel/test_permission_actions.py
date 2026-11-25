"""Amallar bo'yicha ruxsat (ko'rish / qo'shish / tahrirlash / o'chirish) va ruxsatlar kutubxonasi (PermissionSet)."""
from apps.accounts.models import PermissionSet, Role, User
from apps.content.models import Post
from tests.panel.test_collections import PanelBase


class PermissionActionTests(PanelBase):
    def make(self, role):
        u = User(username='amal1', name='Amal', role=role, status='active')
        u.set_password('Parol-12345!')
        u.save()
        self.client.logout()
        self.client.force_login(u)
        return u

    def test_create_and_update_but_not_delete(self):
        Role.objects.create(slug='qoshuvchi', name='Qo‘shuvchi', permissions={'news': ['read', 'create', 'update']}, edit_all=True)
        self.make('qoshuvchi')
        r = self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'Yangi'}, 'status': 'draft'})
        self.assertEqual(r.status_code, 201, r.content[:200])
        pid = self.j(r)['doc']['id']
        self.assertEqual(self.send('patch', f'/api/cms/posts/{pid}', {'title': {'uz': 'Tahrir'}}).status_code, 200)
        self.assertEqual(self.client.delete(f'/api/cms/posts/{pid}').status_code, 403)  # o'chirish yo'q
        self.assertIsNone(Post.objects.get(pk=pid).deleted_at)

    def test_update_only_cannot_create(self):
        Role.objects.create(slug='tahrirchi', name='Tahrirchi', permissions={'news': ['update']}, edit_all=True)
        self.make('tahrirchi')
        p = Post.objects.create(type='news', title={'uz': 'Bor'}, status='draft')
        self.assertEqual(self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'X'}}).status_code, 403)
        self.assertEqual(self.send('patch', f'/api/cms/posts/{p.pk}', {'title': {'uz': 'Y'}}).status_code, 200)
        self.assertEqual(self.client.get('/api/cms/posts?limit=1').status_code, 200)  # tahrirlash — ko'rishni ham beradi

    def test_permission_set_adds_to_role(self):
        r = self.send('post', '/api/cms/permission-sets', {'name': 'Yangilik muharriri', 'permissions': {'news': ['read', 'create'], 'zzz': ['read']}})
        self.assertEqual(r.status_code, 201, r.content[:200])
        ps = self.j(r)['doc']
        self.assertEqual(ps['permissions'], {'news': ['read', 'create']})
        role = Role.objects.create(slug='bosh', name='Bo‘sh rol', permissions={'media': ['read']})
        res = self.send('patch', f'/api/cms/roles/{role.pk}', {'permissionSets': [ps['id']]})
        doc = self.j(res)['doc']
        self.assertEqual(doc['permissionSets'], [ps['id']])
        self.assertEqual(doc['effective'], {'news': ['read', 'create'], 'media': ['read']})
        self.make('bosh')
        self.assertEqual(self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'To‘plamdan'}}).status_code, 201)
        # to'plamlar faqat superadmin uchun
        self.assertEqual(self.client.get('/api/cms/permission-sets').status_code, 403)

    def test_deleting_set_removes_it_from_role(self):
        ps = PermissionSet.objects.create(name='Vaqtinchalik', permissions={'events': ['read', 'create']})
        role = Role.objects.create(slug='vaqt', name='Vaqt', permissions={})
        role.permission_sets.add(ps)
        self.assertEqual(self.client.delete(f'/api/cms/permission-sets/{ps.pk}').status_code, 200)
        self.assertEqual(list(role.permission_sets.all()), [])
