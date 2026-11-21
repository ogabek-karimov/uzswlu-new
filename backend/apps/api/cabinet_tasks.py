"""Xodim kabinetidagi vazifalar: dekan kafedra mudirlariga, kafedra mudiri o'z xodimlariga topshiriq beradi;
hamma o'ziga ham vazifa yozishi va o'ziga berilganini «bajarildi» deb belgilashi mumkin.

Kimga topshiriq berish mumkinligi HEMIS lavozimidan (cabinet_roles) aniqlanadi — frontend yuborgan ID ga ishonilmaydi."""
from datetime import date

from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import StaffTask
from apps.core.fields import tr
from apps.hemis import get_client

from .builders_staff import find_person
from .cabinet_roles import _CHAIR_HEAD, _faculty_for, _members, detect_role

MAX_OPEN = 200  # bitta ijrochida ochiq vazifalar chegarasi


def _name(person: dict | None, fallback: str) -> str:
    return (person or {}).get('name') or fallback


def assignees(hemis_id: str) -> list[dict]:
    """Shu xodim topshiriq bera oladigan odamlar (o'zi alohida qo'shiladi)."""
    person = find_person(hemis_id, 'uz')
    if not person:
        return []
    role, emp = detect_role(person)
    out: list[dict] = []
    if role == 'chair_head':
        dept = (emp or {}).get('department') or {}
        out = [{'id': m['id'], 'name': m['name'], 'position': m['position']} for m in _members(dept, hemis_id)]
    elif role == 'dean':
        f = _faculty_for(emp)
        for c in (f or {}).get('departments') or []:
            dept = {'id': c.get('id'), 'name': tr(c.get('name'), 'uz')}
            out += [{'id': m['id'], 'name': m['name'], 'position': m['position']} for m in _members(dept, hemis_id) if _CHAIR_HEAD.search(m['position'] or '')]
    seen, uniq = set(), []
    for a in out:
        if a['id'] not in seen:
            seen.add(a['id'])
            uniq.append(a)
    return uniq


def task_out(t: StaffTask, me: str) -> dict:
    return {
        'id': t.pk, 'title': t.title, 'note': t.note, 'status': t.status,
        'due': t.due.isoformat() if t.due else None,
        'overdue': bool(t.due and t.status == 'open' and t.due < date.today()),
        'assigneeId': t.assignee_id, 'assigneeName': t.assignee_name,
        'authorId': t.author_id, 'authorName': t.author_name,
        'self': t.assignee_id == t.author_id,
        'createdAt': t.created_at.isoformat(),
        'doneAt': t.done_at.isoformat() if t.done_at else None,
    }


def tasks_out(hemis_id: str) -> dict:
    qs = StaffTask.objects.filter(assignee_id=hemis_id) | StaffTask.objects.filter(author_id=hemis_id)
    mine, given = [], []
    for t in qs.distinct().order_by('status', 'due', '-created_at')[:500]:
        row = task_out(t, hemis_id)
        if t.assignee_id == hemis_id:
            mine.append(row)
        if t.author_id == hemis_id and t.assignee_id != hemis_id:
            given.append(row)
    return {'mine': mine, 'given': given, 'assignees': assignees(hemis_id)}


def create_task(hemis_id: str, data) -> dict:
    title = str(data.get('title') or '').strip()
    note = str(data.get('note') or '').strip()
    if not title or len(title) > 200:
        raise ValidationError({'title': 'Vazifa nomi majburiy (200 belgigacha)'})
    if len(note) > 2000:
        raise ValidationError({'note': 'Izoh 2000 belgidan oshmasin'})
    due = None
    if data.get('due'):
        try:
            due = date.fromisoformat(str(data['due'])[:10])
        except ValueError:
            raise ValidationError({'due': 'Muddat YYYY-MM-DD ko‘rinishida bo‘lsin'})
    target = str(data.get('assigneeId') or hemis_id)
    me = find_person(hemis_id, 'uz')
    if not me:
        raise NotFound('Staff member not found')
    if target == hemis_id:
        assignee = me
    else:
        allowed = {a['id'] for a in assignees(hemis_id)}
        if target not in allowed:
            raise PermissionDenied('Bu xodimga topshiriq berish huquqingiz yo‘q')
        assignee = find_person(target, 'uz')
    if StaffTask.objects.filter(assignee_id=target, status='open').count() >= MAX_OPEN:
        raise ValidationError({'assigneeId': 'Ochiq vazifalar chegarasiga yetildi'})
    t = StaffTask.objects.create(title=title, note=note, due=due, assignee_id=target, assignee_name=_name(assignee, target),
                                 author_id=hemis_id, author_name=_name(me, hemis_id))
    return task_out(t, hemis_id)


def _own(hemis_id: str, pk) -> StaffTask:
    try:
        t = StaffTask.objects.filter(pk=int(pk)).first()
    except (TypeError, ValueError):
        t = None
    if not t or hemis_id not in (t.assignee_id, t.author_id):
        raise NotFound('Task not found')
    return t


def set_status(hemis_id: str, pk, status: str) -> dict:
    t = _own(hemis_id, pk)
    if t.assignee_id != hemis_id:
        raise PermissionDenied('Holatni faqat ijrochi o‘zgartiradi')
    if status not in ('open', 'done'):
        raise ValidationError({'status': 'open yoki done'})
    t.status = status
    t.done_at = timezone.now() if status == 'done' else None
    t.save(update_fields=['status', 'done_at'])
    return task_out(t, hemis_id)


def delete_task(hemis_id: str, pk) -> None:
    t = _own(hemis_id, pk)
    if t.author_id != hemis_id:
        raise PermissionDenied('O‘chirishni faqat bergan odam qila oladi')
    t.delete()
