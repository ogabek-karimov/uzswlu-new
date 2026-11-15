"""Kabinetdagi rol (rolga asoslangan panel): HEMIS lavozimidan avtomatik aniqlanadi.

Admin paneldagi rollar (`accounts.User.role`) bilan aralashtirmang — bu saytdagi xodim kabineti uchun:

  dean        — fakultet dekani (lavozimi «Dekan»; o'rinbosarlari emas)
  chair_head  — kafedra mudiri
  teacher     — professor-o'qituvchi xodim (HEMIS xodim turi «12»)
  staff       — boshqa xodimlar
  student     — talaba (HEMIS talaba kirishi ulanganda; hozircha xodim kabinetida chiqmaydi)

Eng yuqori rol tanlanadi: dean > chair_head > teacher > staff. Panel ma'lumotlari ham shu yerda yig'iladi.
"""
import re

from apps.core.fields import tr
from apps.hemis import get_client

ROLES = ('dean', 'chair_head', 'teacher', 'staff', 'student')
PANEL_LIMIT = 200  # panelga chiqadigan xodimlar chegarasi (javob hajmi)

_DEAN = re.compile(r'\bdekan\b', re.I)
_DEPUTY = re.compile(r"o['‘’ʻʼ`]?rinbosar|muovin|zamestitel|deputy|помощник|заместитель", re.I)
_CHAIR_HEAD = re.compile(r'kafedra\s+mudiri|заведующ\w*\s+кафедр|head\s+of\s+(the\s+)?department', re.I)


def _norm(value: str) -> str:
    return re.sub(r"[‘’ʻʼ`']", '', (value or '').lower()).strip()


def _employments(person: dict) -> list[dict]:
    return person.get('employments') or []


def detect_role(person: dict) -> tuple[str, dict | None]:
    """(rol, shu rolni bergan ish joyi). Ish joyi — lavozim va bo'lim nomini panelda ko'rsatish uchun."""
    emps = _employments(person)
    for e in emps:
        pos = (e.get('position') or {}).get('name') or ''
        if _DEAN.search(pos) and not _DEPUTY.search(pos):
            return 'dean', e
    for e in emps:
        if _CHAIR_HEAD.search((e.get('position') or {}).get('name') or ''):
            return 'chair_head', e
    for e in emps:
        if (e.get('type') or {}).get('code') == '12':
            return 'teacher', e
    return 'staff', (emps[0] if emps else None)


def _dept_name(emp: dict | None) -> str:
    return ((emp or {}).get('department') or {}).get('name') or ''


def _members(department: dict, exclude_id: str) -> list[dict]:
    """Shu bo'limda ishlaydigan boshqa xodimlar (id yoki nom bo'yicha moslik)."""
    dep_id, dep_name = department.get('id'), _norm(department.get('name'))
    out = []
    for who in get_client().staff('uz'):
        if str(who['id']) == str(exclude_id):
            continue
        for e in _employments(who):
            d = e.get('department') or {}
            if (dep_id and d.get('id') == dep_id) or (dep_name and _norm(d.get('name')) == dep_name):
                out.append({'id': str(who['id']), 'name': who['name'], 'position': (e.get('position') or {}).get('name') or '', 'photo': who.get('photo')})
                break
    return out


def _faculty_for(emp: dict | None) -> dict | None:
    name = _norm(_dept_name(emp))
    if not name:
        return None
    for f in get_client().faculties():
        if name in {_norm((f.get('name') or {}).get(lang)) for lang in ('uz', 'ru', 'en', 'zh')}:
            return f
    return None


def panel_out(person: dict, role: str, emp: dict | None, lang: str) -> dict:
    """Rolga mos panel ma'lumoti. Barcha rollar uchun: lavozim va bo'lim."""
    base = {
        'position': ((emp or {}).get('position') or {}).get('name') or '',
        'department': _dept_name(emp),
    }
    if role == 'dean':
        f = _faculty_for(emp)
        if f:
            members = {}
            for who in get_client().staff('uz'):
                for e in _employments(who):
                    members.setdefault(_norm(((e.get('department') or {}).get('name'))), set()).add(str(who['id']))
            base['faculty'] = {
                'slug': f['slug'],
                'name': tr(f["name"], lang),
                'stats': f.get('stats') or {},
                'chairs': [
                    {
                        'id': c['id'],
                        'name': tr(c["name"], lang),
                        'staffCount': len(members.get(_norm((c.get('name') or {}).get('uz')), ())),
                    }
                    for c in (f.get('departments') or [])
                ],
            }
    elif role == 'chair_head':
        dept = (emp or {}).get('department') or {}
        team = _members(dept, person['id'])
        base['team'] = {'count': len(team), 'members': team[:PANEL_LIMIT]}
    return base


def cabinet_role(person: dict, lang: str) -> dict:
    role, emp = detect_role(person)
    return {'role': role, 'panel': panel_out(person, role, emp, lang)}
