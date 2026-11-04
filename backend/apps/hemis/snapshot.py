"""Namuna HEMIS klienti: `seed_data/hemis-snapshot.json` dan o'qiydi (haqiqiy API ulanguncha)."""
import json
import re
from datetime import datetime
from functools import cached_property

from django.conf import settings

from .base import HemisClient

POSITION_CODES = {
    'Stajer-o‘qituvchi': '11', 'Assistent': '12', 'Katta o‘qituvchi': '13', 'Dotsent': '14', 'Professor': '15',
    'Rektor': '21', 'O‘quv ishlari bo‘yicha birinchi prorektor': '22', 'Rektor yordamchisi': '24', 'Matbuot kotibi': '25',
    'Dekan': '31', 'Dekan muovini': '32', 'Tyutor': '33', 'Kafedra mudiri': '34',
    'Tizim administratori': '41', 'Muhandis': '42', '1-toifali muhandis': '43', 'Bo‘lim mudiri': '44',
    'Bo‘lim boshlig‘i': '45', 'Bosh mutaxassis': '46',
}
FORM_MAIN = {'code': '11', 'name': 'Asosiy ish joy'}
FORM_INNER = {'code': '12', 'name': 'O‘rindoshlik (ichki-asosiy)'}
WORKING = {'code': '11', 'name': 'Ishlamoqda'}


def position_code(name: str) -> str:
    if name in POSITION_CODES:
        return POSITION_CODES[name]
    return '23' if re.search(r'prorektor', name, re.I) else '99'


class SnapshotHemis(HemisClient):
    @cached_property
    def _data(self) -> dict:
        with open(settings.HEMIS_SNAPSHOT, encoding='utf-8') as fh:
            return json.load(fh)

    def synced_at(self) -> datetime | None:
        value = self._data.get('syncedAt')
        return datetime.fromisoformat(value) if value else None

    def summary(self) -> dict:
        return self._data['summary']

    def faculties(self) -> list[dict]:
        return self._data['faculties']

    def staff(self, lang: str) -> list[dict]:
        groups = {d['id']: d['group'] for d in self._data['staffDepartments']}
        out = []
        for s in self._data['staff']:
            employments = []
            for i, e in enumerate(s['employments']):
                code = position_code(e['position'])
                group = groups.get(e['department']['id'], s['group'])
                employments.append({
                    'department': {'id': e['department']['id'], 'name': e['department']['name']},
                    'position': {'code': code, 'name': e['position']},
                    'form': FORM_INNER if i else FORM_MAIN,
                    'rate': 1,
                    'status': WORKING,
                    'type': (
                        {'code': '12', 'name': 'Professor-o‘qituvchi xodim'} if re.fullmatch(r'1[1-5]', code)
                        else {'code': '11', 'name': 'Administrativ-boshqaruv xodim'} if group == 'lead'
                        else {'code': '10', 'name': 'Boshqa'}
                    ),
                })
            out.append({
                'id': s['id'], 'name': s['name'], 'patronymic': s.get('patronymic'),
                'photo': None, 'group': s['group'], 'employments': employments,
            })
        return out

    def staff_departments(self, lang: str) -> list[dict]:
        return list(self._data['staffDepartments'])

    def person(self, hemis_id: str) -> dict | None:
        s = next((x for x in self._data['staff'] if x['id'] == str(hemis_id)), None)
        if not s:
            return None
        patronymic = s.get('patronymic')
        words = [w for w in s['name'].split() if w not in (patronymic or '').split()]
        return {
            'firstName': ' '.join(words[1:]) if len(words) > 1 else (words[0] if words else ''),
            'lastName': words[0] if len(words) > 1 else '',
            'patronymic': patronymic,
            'birthDate': None, 'phone': None, 'email': None,
        }
