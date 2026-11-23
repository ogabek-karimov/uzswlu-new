"""Rollar: superadmin rol yaratadi, bo'limlar bo'yicha ruxsat beradi; foydalanuvchi faqat o'z bo'limlarini ko'radi va yozadi."""
from apps.accounts.models import User
from tests.panel.test_collections import PanelBase
from tests.support import seed_preset_roles


class RoleTests(PanelBase):
    def make_user(self, role, username='dekan1'):
        u = User(username=username, name='Test', role=role, status='active')
        u.set_password('Parol-12345!')
        u.save()
        return u

    def as_user(self, user):
        self.client.logout()
        self.client.force_login(user)

    def setUp(self):
        super().setUp()
        seed_preset_roles()  # tayyor maxsus rollar migratsiyada o'chiriladi (0009); bu testlar ularga tayanadi

    def test_system_roles_seeded(self):
        slugs = {r['slug'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}
        self.assertTrue({'superadmin', 'editor', 'pages', 'sdg'} <= slugs)

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
        users = self.client.get('/api/cms/users')  # ro'yxat — faqat o'zi; boshqalarning yozuvi — yopiq
        self.assertEqual(users.status_code, 200)
        self.assertEqual([u['id'] for u in self.j(users)['docs']], [User.objects.get(username='teacher2').pk])
        self.assertIn(self.client.get(f'/api/cms/users/{self.superadmin.pk}').status_code, (403, 404))  # boshqaning yozuvi ko'rinmaydi
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

    def test_cannot_delete_superadmin_or_used_role(self):
        rid = {r['slug']: r['id'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}
        self.assertEqual(self.client.delete(f"/api/cms/roles/{rid['superadmin']}").status_code, 403)
        self.make_user('rektor', 'rektor1')
        self.assertEqual(self.client.delete(f"/api/cms/roles/{rid['rektor']}").status_code, 200)  # foydalanuvchisi bor rol ham o'chadi; u ruxsatsiz qoladi
        self.assertEqual(User.objects.get(username='rektor1').role, 'rektor')
        self.assertEqual(self.client.delete(f"/api/cms/roles/{rid['kafedra-mudiri']}").status_code, 200)

    def test_superadmin_deletes_users_but_not_self(self):
        u = self.make_user('editor', 'ketadi1')
        self.assertEqual(self.client.delete(f'/api/cms/users/{self.superadmin.pk}').status_code, 403)
        self.assertEqual(self.client.delete(f'/api/cms/users/{u.pk}').status_code, 200)
        self.assertFalse(User.objects.filter(pk=u.pk).exists())

    def test_superadmin_role_permissions_locked(self):
        rid = {r['slug']: r['id'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}['superadmin']
        self.send('patch', f'/api/cms/roles/{rid}', {'permissions': {'news': 'read'}, 'name': 'Bosh admin'})
        doc = self.j(self.client.get(f'/api/cms/roles/{rid}'))
        self.assertEqual(doc['name'], 'Bosh admin')
        self.assertEqual(doc['permissions']['news'], 'write')  # superadmin hamma narsaga yozadi — o'zgartirib bo'lmaydi

    def test_hemis_role_link_rules(self):
        r = self.send('post', '/api/cms/roles', {'name': 'Dekan 2', 'hemisRole': 'dean', 'permissions': {'news': 'write'}})
        self.assertEqual(r.status_code, 201, r.content[:200])
        self.assertEqual(self.j(r)['doc']['hemisRole'], 'dean')
        # bir HEMIS roli faqat bitta rolga bog'lanadi, noma'lum qiymat rad etiladi
        self.assertEqual(self.send('post', '/api/cms/roles', {'name': 'Dekan 3', 'hemisRole': 'dean'}).status_code, 400)
        self.assertEqual(self.send('post', '/api/cms/roles', {'name': 'Boshqa', 'hemisRole': 'rector'}).status_code, 400)
        # tizim roliga (superadmin) HEMIS roli biriktirilmaydi
        sa = next(x for x in self.j(self.client.get('/api/cms/roles?limit=50'))['docs'] if x['slug'] == 'superadmin')
        self.send('patch', f'/api/cms/roles/{sa["id"]}', {'hemisRole': 'staff'})
        self.assertIsNone(self.j(self.client.get(f'/api/cms/roles/{sa["id"]}'))['hemisRole'])


class NoPresetRolesTests(PanelBase):
    def test_only_system_roles_exist_after_migrations(self):
        """accounts.0009 Rektor/Dekan/Kafedra mudiri/O'qituvchi rollarini o'chiradi: tayyor holatda faqat tizim rollari qoladi."""
        slugs = {r['slug'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}
        self.assertEqual(slugs, {'superadmin', 'editor', 'pages', 'sdg'})


class DefaultRolesEditableTests(PanelBase):
    """editor, pages, sdg ham oddiy rol: superadmin ularning ruxsatlarini o'zgartiradi, olib tashlaydi yoki butunlay o'chiradi."""

    def make_user(self, role, username):
        u = User(username=username, name='Test', role=role, status='active')
        u.set_password('Parol-12345!')
        u.save()
        return u

    def as_user(self, user):
        self.client.logout()
        self.client.force_login(user)

    def rid(self, slug):
        return {r['slug']: r['id'] for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}[slug]

    def test_default_roles_start_with_expected_sections(self):
        docs = {r['slug']: r for r in self.j(self.client.get('/api/cms/roles?limit=50'))['docs']}
        self.assertEqual(docs['sdg']['permissions'], {'sdg': 'write', 'media': 'write'})
        self.assertTrue(docs['editor']['editAll'])
        self.assertFalse(docs['pages']['editAll'])
        self.assertFalse(docs['sdg']['system'])

    def test_changing_editor_permissions_takes_effect(self):
        ed = self.make_user('editor', 'ed_role')
        self.as_user(ed)
        self.assertEqual(self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'A'}, 'status': 'draft'}).status_code, 201)
        self.client.logout()
        self.client.force_login(self.superadmin)
        self.assertEqual(self.send('patch', f"/api/cms/roles/{self.rid('editor')}", {'permissions': {'events': 'write'}}).status_code, 200)
        self.as_user(ed)
        self.assertEqual(self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'B'}, 'status': 'draft'}).status_code, 403)
        self.assertEqual(self.send('post', '/api/cms/posts', {'type': 'events', 'title': {'uz': 'C'}, 'status': 'draft'}).status_code, 201)

    def test_edit_all_flag_controls_foreign_posts(self):
        self.client.force_login(self.superadmin)
        other = self.j(self.send('post', '/api/cms/posts', {'type': 'news', 'title': {'uz': 'Boshqa'}, 'status': 'draft'}))['doc']['id']
        ed = self.make_user('editor', 'ed_all')
        self.as_user(ed)
        self.assertEqual(self.send('patch', f'/api/cms/posts/{other}', {'title': {'uz': 'E'}}).status_code, 200)  # editor — hammasini
        self.client.logout()
        self.client.force_login(self.superadmin)
        self.send('patch', f"/api/cms/roles/{self.rid('editor')}", {'editAll': False})
        self.as_user(ed)
        self.assertEqual(self.send('patch', f'/api/cms/posts/{other}', {'title': {'uz': 'F'}}).status_code, 403)  # belgi olindi — faqat o'ziniki

    def test_default_role_can_be_deleted_when_unused(self):
        self.assertEqual(self.client.delete(f"/api/cms/roles/{self.rid('sdg')}").status_code, 200)
        self.make_user('pages', 'pg_used')
        self.assertEqual(self.client.delete(f"/api/cms/roles/{self.rid('pages')}").status_code, 200)  # foydalanuvchisi bor rol ham o'chadi (ogohlantirishdan so'ng)
