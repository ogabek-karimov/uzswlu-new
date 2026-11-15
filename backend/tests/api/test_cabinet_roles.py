from django.test import SimpleTestCase

from apps.api.builders_staff import cabinet_out
from apps.api.cabinet_roles import detect_role
from tests.support import SeededTestCase


def person(*positions, type_code='10'):
    return {'id': '1', 'name': 'Test', 'employments': [
        {'department': {'id': 'd', 'name': 'Bo‘lim'}, 'position': {'code': '99', 'name': p}, 'type': {'code': type_code}} for p in positions
    ]}


class CabinetRoleTests(SimpleTestCase):
    def test_dean(self):
        self.assertEqual(detect_role(person('Dekan'))[0], 'dean')

    def test_dean_deputy_is_not_dean(self):
        self.assertNotEqual(detect_role(person('Dekan o‘rinbosari'))[0], 'dean')
        self.assertEqual(detect_role(person('Dekan o‘rinbosari'))[0], 'staff')

    def test_chair_head(self):
        self.assertEqual(detect_role(person('Kafedra mudiri'))[0], 'chair_head')

    def test_teacher_by_employment_type(self):
        self.assertEqual(detect_role(person('Dotsent', type_code='12'))[0], 'teacher')

    def test_highest_role_wins(self):
        self.assertEqual(detect_role(person('Professor', 'Kafedra mudiri', type_code='12'))[0], 'chair_head')
        self.assertEqual(detect_role(person('Professor', 'Dekan', type_code='12'))[0], 'dean')

    def test_staff_and_empty(self):
        self.assertEqual(detect_role(person('Kadrlar bo‘limi boshlig‘i'))[0], 'staff')
        self.assertEqual(detect_role({'id': '2', 'employments': []}), ('staff', None))


class CabinetPanelDataTests(SeededTestCase):
    """HEMIS snapshot ma'lumotlari bilan: rolga mos panel."""

    def test_dean_panel_has_faculty_and_chairs(self):
        me = cabinet_out('7949', 'uz')  # Tarjimonlik fakulteti dekani
        self.assertEqual(me['role'], 'dean')
        faculty = me['panel']['faculty']
        self.assertTrue(faculty['slug'])
        self.assertIn('students', faculty['stats'])
        self.assertIsInstance(faculty['chairs'], list)

    def test_chair_head_panel_lists_department_team(self):
        me = cabinet_out('7768', 'uz')  # Pedagogika va psixologiya kafedrasi mudiri
        self.assertEqual(me['role'], 'chair_head')
        team = me['panel']['team']
        self.assertEqual(team['count'], len(team['members']))
        self.assertNotIn('7768', [m['id'] for m in team['members']])

    def test_every_staff_member_gets_a_role(self):
        from apps.hemis import get_client
        for p in get_client().staff('uz')[:60]:
            self.assertIn(cabinet_out(str(p['id']), 'uz')['role'], ('dean', 'chair_head', 'teacher', 'staff'))

    def test_dean_deputy_in_snapshot_is_not_dean(self):
        self.assertNotEqual(detect_role(person('Dekan muovini'))[0], 'dean')
