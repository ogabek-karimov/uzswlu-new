"""Rollar: superadmin rol yaratadi, bo'limlar bo'yicha ruxsat beradi; foydalanuvchi faqat o'z bo'limlarini ko'radi va yozadi."""
from apps.accounts.models import User
from tests.panel.test_collections import PanelBase


class RoleTests(PanelBase):
    def make_user(self, role, username='dekan1'):
        u = User(username=username, name='Test', role=role, status='active')
        u.set_password('Parol-12345!')
        u.save()
        return u

    def as_user(self, user):
        self.client.logout()
        self.client.force_login(user)

    def test_system_and_preset_roles_seeded(self):
        slugs = {r['slug'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}
        self.assertTrue({'superadmin', 'editor', 'faculty', 'pages', 'sdg', 'rektor', 'dekan', 'oqituvchi'} <= slugs)

    def test_create_role_clean_permissions_and_assign(self):
        r = self.send('post', '/api/cms/roles', {'name': 'Tutor', 'permissions': {'news': 'write', 'settings': 'write', 'events': 'zzz'}})
        self.assertEqual(r.status_code, 201, r.content[:200])
        doc = self.j(r)['doc']
        self.assertEqual(doc['slug'], 'tutor')
        self.assertEqual(doc['permissions'], {'news': 'write'})  # noma'lum bo'lim va daraja tashlab yuboriladi
        u = self.make_user('tutor')
        self.assertEqual(self.j(self.client.get(f'/api/cms/users/{u.pk}'))['role'], 'tutor')
        # noma'lum rolni tayinlab bo'lmaydi
        self.assertEqual(self.send('patch', f'/api/cms/users/{u.pk}', {'role': 'yoq-rol'}).status_code, 400)

    def test_me_returns_permissions_and_role_name(self):
        self.as_user(self.make_user('oqituvchi', 'teacher1'))
        me = self.j(self.client.get('/api/cms/users/me'))['user']
        self.assertEqual(me['roleName'], 'O‘qituvchi')
        self.assertEqual(me['permissions']['events'], 'write')
        self.assertNotIn('pages', me['permissions'])

    def test_custom_role_writes_only_allowed_sections(self):
        self.as_user(self.make_user('oqituvchi', 'teacher2'))
        # o'qituvchi: tadbir yoza oladi, yangilik (read) — yozolmaydi, sahifalar — yo'q
        ok = self.send('post', '/api/cms/posts', {'type': 'events', 'title': {'uz': 'Seminar'}, 'status': 'draft'})
        self.assertEqual(ok.status_code, 201, ok.content[:200])
        no = self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'Yangilik'}, 'status': 'draft'})
        self.assertEqual(no.status_code, 403, no.content[:200])
        self.assertEqual(self.send('post', '/api/cms/quick-links', {'icon': 'lucide:globe', 'url': '/x', 'title': {'uz': 'A'}}).status_code, 403)
        # ochiq ma'lumotni o'qiy oladi, shaxsiy bo'limlarni — yo'q
        self.assertEqual(self.client.get('/api/cms/faculties').status_code, 200)
        self.assertEqual(self.client.get('/api/cms/users').status_code, 403)  # foydalanuvchilar ro'yxati — faqat superadmin
        self.assertEqual(self.client.get(f'/api/cms/users/{self.superadmin.pk}').status_code, 403)
        self.assertEqual(self.client.get('/api/cms/activity').status_code, 403)
        self.assertEqual(self.client.get('/api/cms/roles').status_code, 403)

    def test_custom_role_edits_only_own_posts(self):
        teacher = self.make_user('oqituvchi', 'teacher3')
        self.as_user(teacher)
        mine = self.j(self.send('post', '/api/cms/posts', {'type': 'events', 'title': {'uz': 'Mening'}, 'status': 'draft'}))['doc']['id']
        self.assertEqual(self.send('patch', f'/api/cms/posts/{mine}', {'title': {'uz': 'Yangi'}}).status_code, 200)
        self.client.logout()
        self.client.force_login(self.superadmin)
        other = self.j(self.send('post', '/api/cms/posts', {'type': 'events', 'title': {'uz': 'Boshqa'}, 'status': 'draft'}))['doc']['id']
        self.as_user(teacher)
        self.assertEqual(self.send('patch', f'/api/cms/posts/{other}', {'title': {'uz': 'Hack'}}).status_code, 403)

    def test_cannot_delete_system_or_used_role(self):
        rid = {r['slug']: r['id'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}
        self.assertEqual(self.client.delete(f"/api/cms/roles/{rid['editor']}").status_code, 403)
        self.make_user('rektor', 'rektor1')
        self.assertEqual(self.client.delete(f"/api/cms/roles/{rid['rektor']}").status_code, 403)  # foydalanuvchisi bor
        self.assertEqual(self.client.delete(f"/api/cms/roles/{rid['kafedra-mudiri']}").status_code, 200)

    def test_system_role_permissions_locked(self):
        rid = {r['slug']: r['id'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}['sdg']
        self.send('patch', f'/api/cms/roles/{rid}', {'permissions': {'news': 'write'}, 'name': 'BRM'})
        doc = self.j(self.client.get(f'/api/cms/roles/{rid}'))
        self.assertEqual(doc['name'], 'BRM')
        self.assertNotIn('news', doc['permissions'])
