"""Oxirgi faol superadmin himoyasi va rol ruxsatlari o'zgarishining faollik jurnalidagi (bo'lim-ma-bo'lim) yozuvi."""
from apps.accounts.models import Role, User
from apps.core.models import Activity
from tests.panel.test_collections import PanelBase


class LastSuperadminTests(PanelBase):
    def test_last_superadmin_cannot_be_demoted_disabled_or_deleted(self):
        others = User.objects.filter(role='superadmin').exclude(pk=self.superadmin.pk)
        others.update(status='disabled')
        url = f'/api/cms/users/{self.superadmin.pk}'
        for body in ({'role': 'editor'}, {'status': 'disabled'}):
            r = self.send('patch', url, body)
            self.assertEqual(r.status_code, 400, r.content[:200])
            self.assertIn('yagona faol superadmin', self.j(r)['errors'][0]['message'])
        self.superadmin.refresh_from_db()
        self.assertEqual((self.superadmin.role, self.superadmin.status), ('superadmin', 'active'))

    def test_second_superadmin_allows_demotion_but_not_of_the_last(self):
        second = User(username='super2', name='Ikkinchi', role='superadmin', status='active')
        second.set_password('Parol-12345!')
        second.save()
        User.objects.filter(role='superadmin').exclude(pk__in=[self.superadmin.pk, second.pk]).update(status='disabled')
        self.assertEqual(self.send('patch', f'/api/cms/users/{second.pk}', {'role': 'editor'}).status_code, 200)
        # endi o'zi yagona — o'zini ham pasaytira olmaydi
        self.assertEqual(self.send('patch', f'/api/cms/users/{self.superadmin.pk}', {'role': 'editor'}).status_code, 400)
        # o'zini o'chira olmaydi (oxirgi superadminni o'chirish — Users.before_delete — qo'shimcha himoya)
        self.assertEqual(self.client.delete(f'/api/cms/users/{self.superadmin.pk}').status_code, 403)

    def test_dashboard_reports_superadmin_count(self):
        n = User.objects.filter(role='superadmin').exclude(status='disabled').count()
        self.assertEqual(self.j(self.client.get('/api/cms/panel/overview'))['superadmins'], n)

    def test_role_permission_change_logged_per_section(self):
        role = Role.objects.create(slug='jurnal', name='Jurnal', permissions={'news': 'write', 'media': 'read'})
        self.send('patch', f'/api/cms/roles/{role.pk}', {'permissions': {'news': 'read', 'pages': 'write'}})
        changes = Activity.objects.filter(entity='roles', entity_id=str(role.pk)).latest('created_at').changes
        self.assertEqual(changes['permissions.news'], {'before': 'read, create, update, delete', 'after': 'read'})
        self.assertEqual(changes['permissions.media'], {'before': 'read', 'after': '—'})
        self.assertEqual(changes['permissions.pages'], {'before': '—', 'after': 'read, create, update, delete'})
