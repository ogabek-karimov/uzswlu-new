"""Ob‘ekt darajasidagi ruxsat: id almashtirib begona ma’lumot olish (IDOR), kabinet izolyatsiyasi, post egaligi."""

from django.test import Client, override_settings
from apps.accounts.models import StaffSession, User
from apps.structure.models import Department, StaffDocument
from tests.support import HOST, Base, api, jwt_for


class ObjectLevelAccessTests(Base):
    """Fakultet admini faqat o'z fakultetini o'zgartira oladi; boshqasi id orqali ham mumkin emas."""

    def setUp(self):
        super().setUp()
        User.objects.create_user('fac_a', password='Pw-12345678!', role='faculty', name='A admin', scope='fa')
        User.objects.create_user('fac_none', password='Pw-12345678!', role='faculty', name='Doirasiz')

    def test_own_faculty_ok_other_forbidden(self):
        h = jwt_for('fac_a')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'phone': '1'}).status_code, 200)
        res = api('patch', f'/api/cms/faculties/{self.fb.pk}', h, {'phone': '2'})
        self.assertEqual(res.status_code, 403)
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.phone, '')

    def test_faculty_without_scope_can_edit_nothing(self):
        h = jwt_for('fac_none')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'phone': '1'}).status_code, 403)
        self.assertEqual(api('patch', f'/api/cms/departments/{self.da.pk}', h, {'room': '1'}).status_code, 403)

    def test_department_scope(self):
        h = jwt_for('fac_a')
        self.assertEqual(api('patch', f'/api/cms/departments/{self.da.pk}', h, {'room': '12'}).status_code, 200)
        self.assertEqual(api('patch', f'/api/cms/departments/{self.db.pk}', h, {'room': '12'}).status_code, 403)

    def test_cannot_move_department_to_other_faculty(self):
        h = jwt_for('fac_a')
        res = api('patch', f'/api/cms/departments/{self.da.pk}', h, {'faculty': 'fb'})
        self.assertEqual(res.status_code, 403)
        self.da.refresh_from_db()
        self.assertEqual(self.da.faculty_slug, 'fa')

    def test_cannot_create_department_in_other_faculty(self):
        h = jwt_for('fac_a')
        res = api('post', '/api/cms/departments', h, {'hemisId': 'new', 'faculty': 'fb', 'name': {'uz': 'X'}})
        self.assertEqual(res.status_code, 403)
        self.assertFalse(Department.objects.filter(hemis_id='new').exists())
        res = api('post', '/api/cms/departments', h, {'hemisId': 'new', 'faculty': 'fa', 'name': {'uz': 'X'}})
        self.assertEqual(res.status_code, 201)

    def test_bulk_patch_respects_scope(self):
        h = jwt_for('fac_a')
        res = api('patch', '/api/cms/departments?where[hemisId][like]=d-', h, {'room': '99'})
        self.assertEqual(res.status_code, 200)
        self.da.refresh_from_db()
        self.db.refresh_from_db()
        self.assertEqual(self.da.room, '99')
        self.assertEqual(self.db.room, '')
        self.assertEqual(len(res.json()['errors']), 1)

    def test_editor_cannot_touch_faculty_at_all(self):
        h = jwt_for('ed')
        self.assertEqual(api('patch', f'/api/cms/faculties/{self.fa.pk}', h, {'phone': '1'}).status_code, 403)


class UserRecordTests(Base):
    def test_editor_sees_only_self(self):
        h = jwt_for('ed')
        res = api('get', '/api/cms/users', h)
        self.assertEqual(res.json()['totalDocs'], 1)
        self.assertEqual(api('get', f'/api/cms/users/{self.admin.pk}', h).status_code, 404)
        self.assertEqual(api('patch', f'/api/cms/users/{self.admin.pk}', h, {'name': 'x'}).status_code, 404)

    def test_editor_cannot_raise_own_role(self):
        h = jwt_for('ed')
        api('patch', f'/api/cms/users/{self.editor.pk}', h, {'role': 'superadmin'})
        self.editor.refresh_from_db()
        self.assertEqual(self.editor.role, 'editor')

    def test_login_history_only_superadmin(self):
        self.assertEqual(api('get', '/api/cms/login-events', jwt_for('ed')).status_code, 403)


class CabinetIsolationTests(Base):
    """Xodim kabineti: boshqa xodim hujjatini id raqamini o'zgartirib ko'rib/o'chirib bo'lmaydi."""

    def setUp(self):
        super().setUp()
        self.tok_a, self.tok_b = StaffSession.issue('1001'), StaffSession.issue('1002')
        self.doc_b = StaffDocument.objects.create(hemis_id='1002', section='articles', title={'uz': 'B maqolasi'}, url='https://example.org/b')
        self.doc_a = StaffDocument.objects.create(hemis_id='1001', section='articles', title={'uz': 'A maqolasi'}, url='https://example.org/a')

    def h(self, token):
        return {'HTTP_AUTHORIZATION': f'Bearer {token}', **HOST}

    def test_cannot_delete_foreign_document(self):
        res = api('delete', f'/api/me/documents/articles/{self.doc_b.pk}', self.h(self.tok_a))
        self.assertEqual(res.status_code, 404)
        self.assertTrue(StaffDocument.objects.filter(pk=self.doc_b.pk).exists())

    def test_wrong_section_is_not_found(self):
        res = api('delete', f'/api/me/documents/books/{self.doc_a.pk}', self.h(self.tok_a))
        self.assertEqual(res.status_code, 404)

    def test_list_contains_only_own(self):
        res = api('get', '/api/me/documents/articles', self.h(self.tok_a))
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('B maqolasi', res.content.decode())

    def test_no_session_no_access(self):
        self.assertEqual(api('get', '/api/me', HOST).status_code, 401)
        self.assertEqual(api('get', '/api/me', self.h('yaroqsiz-token')).status_code, 401)

    def test_admin_jwt_is_not_a_staff_session(self):
        self.assertEqual(api('get', '/api/me', jwt_for('root')).status_code, 401)


class HiddenStaffTests(Base):
    def test_hidden_list_needs_token_when_configured(self):
        from apps.structure.models import StaffProfile
        StaffProfile.objects.create(hemis_id='777', hidden=True)
        with override_settings(API_TOKEN='site-secret'):
            self.assertEqual(Client(**HOST).get('/api/site/staff-hidden').status_code, 403)
            ok = Client(**HOST).get('/api/site/staff-hidden', HTTP_AUTHORIZATION='Bearer site-secret')
            self.assertEqual(ok.json()['ids'], ['777'])

    def test_hidden_staff_not_in_public_list_or_detail(self):
        from apps.structure.models import StaffProfile
        StaffProfile.objects.create(hemis_id='888', hidden=True)
        self.assertNotIn('888', Client(**HOST).get('/api/staff').content.decode())
        self.assertEqual(Client(**HOST).get('/api/staff/888').status_code, 404)


class PostOwnershipTests(Base):
    def setUp(self):
        super().setUp()
        from apps.content.models import Post
        self.pages = User.objects.create_user('pg', password='Pw-12345678!', role='pages', name='Pages')
        self.fac = User.objects.create_user('fc', password='Pw-12345678!', role='faculty', name='Fac', scope='fa')
        self.mine = Post.objects.create(type='news', slug='mine', title={'uz': 'Meniki'}, author=self.pages)
        self.other = Post.objects.create(type='news', slug='other', title={'uz': 'Boshqaniki'}, author=self.editor)
        self.orphan = Post.objects.create(type='news', slug='orphan', title={'uz': 'Egasiz'})

    def test_pages_role_edits_only_own_posts(self):
        h = jwt_for('pg')
        self.assertEqual(api('patch', f'/api/cms/posts/{self.mine.pk}', h, {'title': {'uz': 'Yangi'}}).status_code, 200)
        self.assertEqual(api('patch', f'/api/cms/posts/{self.other.pk}', h, {'title': {'uz': 'Buzildi'}}).status_code, 403)
        self.assertEqual(api('patch', f'/api/cms/posts/{self.orphan.pk}', h, {'title': {'uz': 'Buzildi'}}).status_code, 403)
        self.other.refresh_from_db()
        self.assertEqual(self.other.title['uz'], 'Boshqaniki')

    def test_cannot_delete_foreign_post(self):
        from apps.content.models import Post
        h = jwt_for('fc')
        self.assertEqual(api('delete', f'/api/cms/posts/{self.other.pk}', h).status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.other.pk).exists())

    def test_bulk_patch_only_touches_own_posts(self):
        h = jwt_for('pg')
        res = api('patch', '/api/cms/posts?where[type][equals]=news', h, {'category': None, 'title': {'uz': 'Ommaviy'}})
        self.other.refresh_from_db()
        self.assertEqual(self.other.title['uz'], 'Boshqaniki')

    def test_editor_and_superadmin_manage_all(self):
        self.assertEqual(api('patch', f'/api/cms/posts/{self.mine.pk}', jwt_for('ed'), {'title': {'uz': 'E'}}).status_code, 200)
        self.assertEqual(api('patch', f'/api/cms/posts/{self.other.pk}', jwt_for('root'), {'title': {'uz': 'R'}}).status_code, 200)

    def test_new_post_belongs_to_creator(self):
        from apps.content.models import Post
        h = jwt_for('pg')
        res = api('post', '/api/cms/posts', h, {'type': 'news', 'title': {'uz': 'Yangi post'}, 'slug': 'yangi-post'})
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(Post.objects.get(slug='yangi-post').author_id, self.pages.pk)
