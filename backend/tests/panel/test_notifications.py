"""Bildirishnomalar: hodisalar (post boshqa odam tomonidan o'zgardi/o'chdi, rol o'zgardi), faqat egasiga ko'rinishi
(admin panel va kabinet), o'qildi belgisi — begona ID bilan boshqasinikiga tegib bo'lmaydi."""
from apps.accounts.models import Role, StaffSession, User
from apps.content.models import Post
from apps.core.models import Notification
from tests.panel.test_collections import PanelBase


class NotificationTests(PanelBase):
    def setUp(self):
        super().setUp()
        Role.objects.get_or_create(slug='muallif', defaults={'name': 'Muallif', 'permissions': {'dashboard': 'read', 'news': 'write'}})
        self.author = User(username='muallif1', name='Muallif', role='muallif', status='active', hemis_id='9300')
        self.author.set_password('Parol-12345!')
        self.author.save()

    def test_author_notified_when_someone_else_edits_or_deletes(self):
        p = Post.objects.create(type='news', title={'uz': 'Mening postim'}, status='draft', author=self.author)
        self.send('patch', f'/api/cms/posts/{p.pk}', {'title': {'uz': 'Tahrir'}})
        self.client.delete(f'/api/cms/posts/{p.pk}')
        titles = list(Notification.objects.filter(user=self.author).values_list('title', flat=True))
        self.assertTrue(any('tahrirlandi' in t for t in titles), titles)
        self.assertTrue(any('savatga tashlandi' in t for t in titles), titles)
        self.assertEqual(Notification.objects.filter(user=self.superadmin).count(), 0)  # o'z amaliga xabar yo'q

    def test_own_edit_does_not_notify(self):
        p = Post.objects.create(type='news', title={'uz': 'O‘zim'}, status='draft', author=self.author)
        self.client.logout()
        self.client.force_login(self.author)
        self.send('patch', f'/api/cms/posts/{p.pk}', {'title': {'uz': 'O‘zim 2'}})
        self.assertFalse(Notification.objects.filter(user=self.author).exists())

    def test_role_change_notifies_user_and_list_is_private(self):
        self.send('patch', f'/api/cms/users/{self.author.pk}', {'role': 'editor'})
        mine = Notification.objects.get(user=self.author, kind='role')
        other = Notification.objects.create(user=self.superadmin, title='Superadminniki')
        # muallif: faqat o'ziniki; begona ID ni «o'qildi» qila olmaydi
        self.client.logout()
        self.client.force_login(self.author)
        res = self.j(self.client.get('/api/cms/panel/notifications'))
        self.assertEqual(res['unread'], 1)
        self.assertEqual([d['id'] for d in res['docs']], [mine.pk])
        self.send('post', '/api/cms/panel/notifications', {'ids': [other.pk]})
        other.refresh_from_db()
        self.assertIsNone(other.read_at)
        self.send('post', '/api/cms/panel/notifications', {})
        self.assertEqual(self.j(self.client.get('/api/cms/panel/notifications'))['unread'], 0)

    def test_cabinet_sees_own_account_notifications_only(self):
        Notification.objects.create(user=self.author, title='Kabinet uchun')
        Notification.objects.create(user=self.superadmin, title='Begona')
        h = {'HTTP_AUTHORIZATION': f'Bearer {StaffSession.issue("9300")}'}
        res = self.client.get('/api/me/notifications', **h).json()
        self.assertEqual([d['title'] for d in res['docs']], ['Kabinet uchun'])
        # rolsiz (hisobi yo'q) xodim — bo'sh
        res = self.client.get('/api/me/notifications', HTTP_AUTHORIZATION=f'Bearer {StaffSession.issue("7909")}').json()
        self.assertEqual(res, {'unread': 0, 'docs': []})
        self.assertEqual(self.client.get('/api/me/notifications').status_code, 401)


class SecurityNotificationTests(PanelBase):
    """Superadminga: kim kirdi, xato parollar (3 — ogohlantirish, 5 — bloklandi), ruxsatsiz urinishlar; takrorlar yog'ilmaydi."""

    def setUp(self):
        super().setUp()
        from django.core.cache import cache
        cache.clear()
        self.editor = User(username='muharrir1', name='Muharrir', role='editor', status='active')
        self.editor.set_password('Parol-12345!')
        self.editor.save()
        self.client.logout()

    def login(self, username, password):
        return self.send('post', '/api/cms/users/login', {'username': username, 'password': password})

    def notes(self):
        return list(Notification.objects.filter(user=self.superadmin, kind='security').values_list('title', flat=True))

    def test_successful_login_notifies_superadmin(self):
        self.assertEqual(self.login('muharrir1', 'Parol-12345!').status_code, 200)
        self.assertTrue(any('admin panelga kirdi' in t for t in self.notes()), self.notes())

    def test_bad_passwords_warn_then_lock_once(self):
        for _ in range(5):
            self.login('muharrir1', 'xato-parol')
        titles = self.notes()
        self.assertEqual(sum('3 marta noto‘g‘ri parol' in t for t in titles), 1)
        self.assertEqual(sum('bloklandi' in t for t in titles), 1)
        self.assertTrue(Notification.objects.filter(user=self.editor, kind='security').exists())  # egasining o'ziga ham
        for _ in range(3):  # bloklangan holatdagi urinishlar — xabar ko'paymaydi
            self.login('muharrir1', 'xato-parol')
        self.assertEqual(len(self.notes()), len(titles))

    def test_unknown_login_guessing_is_reported(self):
        for _ in range(5):
            self.login('yoq-login', 'nimadir')
        self.assertTrue(any('bunday login yo‘q' in t for t in self.notes()), self.notes())
