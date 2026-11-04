"""HEMIS → sayt uchun nusxa (seed_data/hemis-snapshot.json bilan bir xil tuzilma).

HEMIS'dagi tuzilma kodlari .env orqali sozlanadi (universitetda farq qilishi mumkin):
  HEMIS_FACULTY_TYPES=11   — fakultet (structureType.code)
  HEMIS_CHAIR_TYPES=12     — kafedra
Fakultet saytdagi qaysi sahifa (Faculty.slug) ekani — Faculty.hemis_id orqali, bo'lmasa nomi bo'yicha topiladi.
"""
import os
import re
from collections import defaultdict

from django.utils import timezone

from apps.structure.models import Faculty

from .api import HemisApi

LANGS = ('uz', 'ru', 'en', 'zh')
LEAD_WORDS = ('rektorat', 'rahbariyat')


def _codes(name: str, default: str) -> set[str]:
    return {c.strip() for c in os.environ.get(name, default).split(',') if c.strip()}


def _same(value: str) -> dict:
    """HEMIS'da nomlar faqat o'zbekcha — boshqa tillar uchun ham o'zbekchasi (tarjimasi admin panelda)."""
    return {lang: value for lang in LANGS}


def _person_name(e: dict) -> tuple[str, str | None]:
    full = e.get('full_name') or ' '.join(x for x in (e.get('second_name'), e.get('first_name'), e.get('third_name')) if x)
    return re.sub(r'\s+', ' ', full or '').strip(), e.get('third_name') or None


def _parent_id(dep: dict) -> str:
    parent = dep.get('parent')
    return str(parent.get('id') if isinstance(parent, dict) else parent or '')


def _code(obj, key: str) -> str:
    return str(((obj or {}).get(key) or {}).get('code') or '')


def build_snapshot(api: HemisApi) -> dict:
    faculty_types = _codes('HEMIS_FACULTY_TYPES', '11')
    chair_types = _codes('HEMIS_CHAIR_TYPES', '12')
    departments = api.items('data/department-list')
    employees = api.items('data/employee-list', type='all')
    by_id = {str(d.get('id')): d for d in departments}

    def group_of(dep: dict) -> str:
        t = _code(dep, 'structureType')
        if t in faculty_types:
            return 'faculty'
        if t in chair_types:
            return 'chair'
        return 'lead' if any(w in (dep.get('name') or '').lower() for w in LEAD_WORDS) else 'unit'

    staff: dict[str, dict] = {}
    counts: dict[str, int] = defaultdict(int)
    for e in employees:
        if _code(e, 'employeeStatus') == '14':  # ishdan bo'shagan
            continue
        dep = e.get('department') or {}
        dep_id = str(dep.get('id') or '')
        employment = {'department': {'id': dep_id, 'name': dep.get('name') or ''}, 'position': ((e.get('staffPosition') or {}).get('name')) or ''}
        sid = str(e.get('id'))
        if sid in staff:
            staff[sid]['employments'].append(employment)
        else:
            name, patronymic = _person_name(e)
            staff[sid] = {'id': sid, 'name': name, 'patronymic': patronymic, 'photo': e.get('image'),
                          'group': group_of(by_id.get(dep_id, dep)), 'employments': [employment]}
        counts[dep_id] += 1

    def holder(dep_id: str, word: str, exclude: str = '') -> dict | None:
        for s in staff.values():
            for emp in s['employments']:
                pos = emp['position'].lower()
                if emp['department']['id'] == dep_id and word in pos and not (exclude and exclude in pos):
                    return s
        return None

    site_by_hemis = {f.hemis_id: f for f in Faculty.objects.exclude(hemis_id='')}
    site_by_name = {(f.name.get('uz') or '').strip().lower(): f for f in Faculty.objects.all()}
    faculties = []
    for d in departments:
        if _code(d, 'structureType') not in faculty_types:
            continue
        fid = str(d.get('id'))
        site = site_by_hemis.get(fid) or site_by_name.get((d.get('name') or '').strip().lower())
        if not site:
            continue
        chairs = [c for c in departments if _code(c, 'structureType') in chair_types and _parent_id(c) == fid]
        dean = holder(fid, 'dekan', exclude='o‘rinbosar')
        try:
            students = api.total('data/student-list', _department=fid)
        except Exception:  # noqa: BLE001 — talaba soni ixtiyoriy
            students = 0
        dean_info = {'staffId': dean['id'] if dean else None, 'name': dean['name'] if dean else '', 'role': 'Dekan', 'photo': dean['photo'] if dean else None}
        faculties.append({
            'slug': site.slug, 'order': site.order, 'logo': None, 'name': _same(d.get('name') or ''), 'about': _same(''),
            'stats': {'students': students, 'departments': len(chairs), 'programs': 0,
                      'teachers': sum(counts[str(c.get('id'))] for c in chairs)},
            'dean': {lang: dean_info for lang in LANGS},
            'deanery': {lang: [] for lang in LANGS},
            'programs': {lang: [] for lang in LANGS},
            'departments': [{
                'id': str(c.get('id')), 'name': _same(c.get('name') or ''),
                'head': (holder(str(c.get('id')), 'mudir') or {}).get('name'),
            } for c in chairs],
            'contact': {lang: {'address': '', 'phone': '', 'email': None, 'mapUrl': None} for lang in LANGS},
        })
    staff_departments = sorted(
        ({'id': str(d.get('id')), 'name': d.get('name') or '', 'group': group_of(d), 'count': counts[str(d.get('id'))]}
         for d in departments if counts[str(d.get('id'))]),
        key=lambda x: x['name'],
    )
    return {
        'syncedAt': timezone.now().isoformat(),
        'summary': {'faculties': len(faculties), 'departments': sum(1 for d in departments if _code(d, 'structureType') in chair_types)},
        'faculties': faculties, 'staff': list(staff.values()), 'staffDepartments': staff_departments,
    }
