"""Kabinet vazifalari: dekan → kafedra mudiri → o'qituvchi (namunaviy HEMIS ma'lumoti)."""
from django.test import TestCase

from apps.accounts.models import StaffSession, StaffTask

DEAN, CHAIR, TEACHER = '8654', '7768', '7792'


def auth(hemis_id):
    return {'HTTP_AUTHORIZATION': f'Bearer {StaffSession.issue(hemis_id)}'}


class CabinetTasksTests(TestCase):
    def test_requires_login(self):
        self.assertEqual(self.client.get('/api/me/tasks').status_code, 401)

    def test_dean_assigns_to_chair_head_who_completes_it(self):
        res = self.client.get('/api/me/tasks', **auth(DEAN))
        self.assertEqual(res.status_code, 200)
        self.assertIn(CHAIR, {a['id'] for a in res.json()['assignees']})
        res = self.client.post('/api/me/tasks', {'title': 'Hisobot', 'assigneeId': CHAIR, 'due': '2030-01-01'}, content_type='application/json', **auth(DEAN))
        self.assertEqual(res.status_code, 201)
        tid = res.json()['id']
        self.assertEqual(len(self.client.get('/api/me/tasks', **auth(DEAN)).json()['given']), 1)
        mine = self.client.get('/api/me/tasks', **auth(CHAIR)).json()['mine']
        self.assertEqual([t['title'] for t in mine], ['Hisobot'])
        # beruvchi holatni o'zgartira olmaydi, ijrochi o'zgartiradi
        self.assertEqual(self.client.patch(f'/api/me/tasks/{tid}', {'status': 'done'}, content_type='application/json', **auth(DEAN)).status_code, 403)
        res = self.client.patch(f'/api/me/tasks/{tid}', {'status': 'done'}, content_type='application/json', **auth(CHAIR))
        self.assertEqual(res.json()['status'], 'done')
        # ijrochi o'chira olmaydi, bergan odam o'chiradi
        self.assertEqual(self.client.delete(f'/api/me/tasks/{tid}', **auth(CHAIR)).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/me/tasks/{tid}', **auth(DEAN)).status_code, 200)
        self.assertEqual(StaffTask.objects.count(), 0)

    def test_teacher_cannot_assign_to_others_only_self(self):
        body = {'title': 'Boshqaga', 'assigneeId': CHAIR}
        res = self.client.post('/api/me/tasks', body, content_type='application/json', **auth(TEACHER))
        self.assertEqual(res.status_code, 403)
        res = self.client.post('/api/me/tasks', {'title': 'O‘zimga'}, content_type='application/json', **auth(TEACHER))
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json()['self'])

    def test_validation_and_foreign_task_hidden(self):
        self.assertEqual(self.client.post('/api/me/tasks', {'title': ' '}, content_type='application/json', **auth(DEAN)).status_code, 400)
        self.assertEqual(self.client.post('/api/me/tasks', {'title': 'x', 'due': 'kecha'}, content_type='application/json', **auth(DEAN)).status_code, 400)
        res = self.client.post('/api/me/tasks', {'title': 'Maxfiy'}, content_type='application/json', **auth(DEAN))
        tid = res.json()['id']
        self.assertEqual(self.client.patch(f'/api/me/tasks/{tid}', {'status': 'done'}, content_type='application/json', **auth(TEACHER)).status_code, 404)
        self.assertEqual(self.client.get('/api/me/tasks', **auth(TEACHER)).json()['mine'], [])
