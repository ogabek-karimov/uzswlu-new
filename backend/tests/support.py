"""Testlar uchun umumiy yordamchilar. Hamma test modullari shu yerdan import qiladi.

  Base            — sof (bo'sh) baza: 2 foydalanuvchi (root, ed), 2 fakultet va kafedra. Tez, izolyatsiyalangan.
  SeededTestCase  — demo ma'lumot (seed_demo) yuklangan baza: shartnoma/oqim testlari uchun (sinf boshida bir marta).
  jwt_for / api   — panelga JWT bilan kirish va so'rov yuborish.
  loose           — cheklovni (throttle) vaqtincha kengaytiradi (login ko'p urinadigan testlar uchun).
"""
import io
import json

from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from apps.accounts.models import User
from apps.structure.models import Department, Faculty

HOST = {'HTTP_HOST': 'localhost'}
PASSWORD = 'Pw-12345678!'


def jwt_for(username: str, password: str = PASSWORD) -> dict:
    res = Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': username, 'password': password}),
                              content_type='application/json')
    assert res.status_code == 200, res.content
    return {'HTTP_AUTHORIZATION': f"Bearer {res.json()['token']}", **HOST}


def api(method: str, url: str, headers: dict, body: dict | None = None):
    c = Client()
    kw = dict(headers)
    if body is not None:
        kw.update(data=json.dumps(body), content_type='application/json')
    return getattr(c, method)(url, **kw)


def loose(scope='login', rate='1000/min'):
    from django.conf import settings as st
    rf = {**st.REST_FRAMEWORK, 'DEFAULT_THROTTLE_RATES': {**st.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], scope: rate}}
    return override_settings(REST_FRAMEWORK=rf)


class Base(TestCase):
    def setUp(self):
        cache.clear()
        mk = User.objects.create_user
        self.admin = mk('root', password=PASSWORD, role='superadmin', name='Root')
        self.editor = mk('ed', password=PASSWORD, role='editor', name='Editor')
        self.fa = Faculty.objects.create(slug='fa', name={'uz': 'A fakultet'})
        self.fb = Faculty.objects.create(slug='fb', name={'uz': 'B fakultet'})
        self.da = Department.objects.create(hemis_id='d-a', faculty_slug='fa', name={'uz': 'A kafedra'})
        self.db = Department.objects.create(hemis_id='d-b', faculty_slug='fb', name={'uz': 'B kafedra'})


class SeededTestCase(TestCase):
    """Demo ma'lumot bilan (55 xodim, 7 slayd, 11 fakultet, ...). `superadmin` foydalanuvchisi ham bor.

    Seed sinf boshida bir marta (≈3 s), tranzaksiya ichida — testlar orasida qayta tiklanadi.
    Faqat shartnoma/oqim kabi «to'liq ma'lumot» kerak bo'lgan testlar uchun; boshqalar `Base` dan foydalansin.
    """

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0, stdout=io.StringIO(), stderr=io.StringIO())
        cls.superadmin = User.objects.get(username='superadmin')

    def setUp(self):
        cache.clear()
        self.client = Client(**HOST)
