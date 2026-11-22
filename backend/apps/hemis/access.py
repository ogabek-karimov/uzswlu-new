"""HEMIS lavozimi → admin panel hisobi.

Superadmin «Rollar» sahifasida rolga «HEMIS roli» (dekan, kafedra mudiri, o'qituvchi, xodim) biriktiradi. Shundan keyin
shu lavozimdagi xodim HEMIS orqali admin panelga kirganda hisob o'zi yaratiladi (parolsiz) va har kirishda lavozim/doira
HEMIS bo'yicha yangilanadi. Qo'lda yaratilgan (HEMIS ID biriktirilgan) hisoblarga tegilmaydi.

Xavfsizlik: avtomatik hisob faqat tizim bo'lmagan rolni oladi (superadmin hech qachon); doirali rolda doira HEMIS'dan topilmasa
hisob hech narsani o'zgartira olmaydi (`in_scope`); lavozim bog'lanishi o'chsa hisob yopiladi va o'zi qayta yoqilmaydi."""
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.roles import permissions_of, permissions_of_role, role_obj


def _context(hemis_id: str):
    from apps.api.builders_staff import find_person
    from apps.api.cabinet_roles import detect_role

    person = find_person(str(hemis_id), 'uz')
    if not person:
        return None
    role, emp = detect_role(person)
    return person, role, emp


def _scope(role: str, emp: dict | None) -> str:
    """Doirali rol uchun fakultet manzili (slug): dekan — o'z fakulteti, kafedra mudiri — kafedrasi kirgan fakultet."""
    from apps.api.cabinet_roles import _dept_name, _faculty_for, _norm
    from apps.hemis import get_client

    if role == 'dean':
        return (_faculty_for(emp) or {}).get('slug') or ''
    dept = _norm(_dept_name(emp))
    if not dept:
        return ''
    for f in get_client().faculties():
        for d in f.get('departments') or []:
            if dept in {_norm((d.get('name') or {}).get(lang)) for lang in ('uz', 'ru', 'en', 'zh')}:
                return f.get('slug') or ''
    return ''


def mapped_role(hemis_role: str) -> Role | None:
    return Role.objects.filter(hemis_role=hemis_role, system=False).first() if hemis_role else None


def panel_access(hemis_id: str):
    """Shu xodim admin panelga kira oladimi va nimalarga: (rol nomi, {bo'lim: daraja}) yoki None. Hech narsa yozmaydi.
    Saytdagi kabinet tugmasi va profil menyusi («Mening bo'limlarim») shundan foydalanadi."""
    existing = User.objects.filter(hemis_id=str(hemis_id)).first()
    if existing and not existing.hemis_auto:
        if existing.status == 'disabled':
            return None
        r = role_obj(existing)
        return (r.name if r else existing.role), permissions_of(existing)
    ctx = _context(hemis_id)
    role = mapped_role(ctx[1]) if ctx else None
    if not role or (existing and existing.status == 'disabled'):
        return None
    return role.name, permissions_of_role(role)


def eligible(hemis_id: str) -> bool:
    """Shu xodim admin panelga kira oladimi (kabinetda «Admin panel» tugmasi uchun) — hech narsa yozmaydi."""
    return panel_access(hemis_id) is not None


def provision(hemis_id: str, name: str = '') -> User | None:
    """Admin panelga kirish uchun hisobni topadi/yaratadi/yangilaydi; ruxsat bo'lmasa None."""
    hemis_id = str(hemis_id)
    existing = User.objects.filter(hemis_id=hemis_id).first()
    if existing and not existing.hemis_auto:
        if existing.status == 'disabled':
            return None
        # Qo'lda tayinlangan: roli o'zgarmaydi, faqat profil HEMIS'dan yangilanadi
        ctx = _context(hemis_id)
        if ctx:
            existing.name = (name or ctx[0].get('name') or existing.name)[:200]
            existing.position = (((ctx[2] or {}).get('position') or {}).get('name') or existing.position)[:200]
            existing.department = (((ctx[2] or {}).get('department') or {}).get('name') or existing.department)[:200]
        existing.status, existing.last_login = 'active', timezone.now()
        existing.save()
        return existing
    ctx = _context(hemis_id)
    role = mapped_role(ctx[1]) if ctx else None
    if not ctx or not role:
        if existing and existing.status != 'disabled':
            existing.status = 'disabled'  # lavozim bog'lanishi yo'q — kirish yopiladi (o'zi qayta yoqilmaydi)
            existing.save(update_fields=['status'])
        return None
    if existing and existing.status == 'disabled':
        return None
    person, hemis_role, emp = ctx
    user = existing or User(username=f'hemis-{hemis_id}', hemis_id=hemis_id, hemis_auto=True)
    if not existing:
        user.set_unusable_password()
    user.name = (name or person.get('name') or user.name or hemis_id)[:200]
    user.position = (((emp or {}).get('position') or {}).get('name') or '')[:200]
    user.department = (((emp or {}).get('department') or {}).get('name') or '')[:200]
    user.role = role.slug
    user.scope = _scope(hemis_role, emp) if role.scoped else ''
    user.status, user.last_login = 'active', timezone.now()
    user.save()
    return user
