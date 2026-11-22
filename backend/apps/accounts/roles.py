"""Rollar va menyu bo'limlari bo'yicha ruxsat.

Tizim rollari (superadmin/editor/faculty/pages/sdg) kolleksiyalardagi qat'iy `access` to'plamlari bilan ishlashda davom etadi;
superadmin yaratgan rollar esa `Role.permissions` bo'yicha: bo'lim -> 'read' | 'write'.
Ma'lumotlarni O'QISH (ochiq sayt ma'lumotlari) har qanday faol rolga ruxsat; foydalanuvchilar, kirish tarixi, faollik, rollar — faqat superadmin.
"""
from __future__ import annotations

# Admin yon menyusidagi bo'limlar: kalit -> (nomi, guruh). Rolga faqat shular beriladi (tizim bo'limlari — faqat superadmin)
SECTIONS: dict[str, tuple[str, str]] = {
    'dashboard': ('Boshqaruv paneli', 'Asosiy'),
    'news': ('Yangiliklar', 'Kontent'),
    'announcements': ('E’lonlar', 'Kontent'),
    'events': ('Tadbirlar', 'Kontent'),
    'pages': ('Sahifalar', 'Kontent'),
    'quick-links': ('Tezkor xizmatlar', 'Kontent'),
    'phones': ('Telefonlar ma’lumotnomasi', 'Kontent'),
    'rude-words': ('Haqoratli so‘zlar', 'Kontent'),
    'media': ('Media kutubxona', 'Kontent'),
    'documents': ('Hujjatlar', 'Kontent'),
    'videos': ('Video darsliklar', 'Kontent'),
    'faculties': ('Fakultetlar', 'Tuzilma'),
    'departments': ('Kafedralar', 'Tuzilma'),
    'leaders': ('Rahbariyat', 'Tuzilma'),
    'staff': ('Xodimlar', 'Tuzilma'),
    'sdg': ('BRM', 'Tuzilma'),
}
LEVELS = ('read', 'write')
POST_SECTIONS = ('news', 'announcements', 'events')

# Faqat superadmin: bu kolleksiyalarni o'qish ham yopiq
PRIVATE = frozenset({'users', 'login-events', 'activity', 'roles'})

W, R = 'write', 'read'
# Tizim rollari: nom va bo'limlari (menyu shu ma'lumotdan quriladi; kolleksiyalardagi `access` bilan mos)
SYSTEM_ROLES = {
    'superadmin': ('Superadmin', 'Hamma narsa', {k: W for k in SECTIONS}, False),
    'editor': ('Kontent muharriri', 'Yangiliklar, e’lonlar, tadbirlar', {'dashboard': W, 'news': W, 'announcements': W, 'events': W, 'media': W}, False),
    'faculty': ('Fakultet admini', 'O‘z fakulteti va kafedralari', {'dashboard': W, 'news': W, 'announcements': W, 'events': W, 'media': W, 'faculties': W, 'departments': W}, True),
    'pages': ('Sahifalar muharriri', 'Sahifalar, hujjatlar, video', {'dashboard': W, 'news': W, 'announcements': W, 'events': W, 'media': W, 'pages': W, 'quick-links': W, 'phones': W, 'rude-words': W, 'documents': W, 'videos': W}, False),
    'sdg': ('BRM menejeri', 'Faqat BRM bo‘limi', {'sdg': W, 'media': W}, False),
}
# Tayyor namunalar (superadmin o'zgartira yoki o'chira oladi)
PRESET_ROLES = {
    'rektor': ('Rektor', 'Universitet rahbari: hamma tuzilmani ko‘radi, yangilik va e’lon yozadi', {'dashboard': R, 'news': W, 'announcements': W, 'events': W, 'media': W, 'faculties': R, 'departments': R, 'leaders': R, 'staff': R}, False),
    'dekan': ('Dekan', 'O‘z fakulteti: yangilik, tadbir, fakultet va kafedralar', {'dashboard': R, 'news': W, 'announcements': W, 'events': W, 'media': W, 'faculties': W, 'departments': W, 'staff': R}, True),
    'kafedra-mudiri': ('Kafedra mudiri', 'O‘z kafedrasi ma’lumotlari va e’lonlari', {'dashboard': R, 'announcements': W, 'events': W, 'media': W, 'departments': W}, True),
    'oqituvchi': ('O‘qituvchi', 'Yangilik va e’lonlarni ko‘radi, o‘z tadbirini yozadi', {'dashboard': R, 'news': R, 'announcements': R, 'events': W, 'media': W}, False),
}


def clean_permissions(value) -> dict:
    """Faqat mavjud bo'lim va to'g'ri daraja (read/write) qoladi."""
    if not isinstance(value, dict):
        return {}
    return {k: v for k, v in value.items() if k in SECTIONS and v in LEVELS}


def _active(user) -> bool:
    return bool(user and user.is_authenticated and user.status != 'disabled')


def role_obj(user):
    """Foydalanuvchi roli (so'rov davomida keshlanadi)."""
    if not hasattr(user, '_role_obj'):
        from .models import Role
        user._role_obj = Role.objects.filter(slug=user.role).first()
    return user._role_obj


def permissions_of_role(r) -> dict:
    """Rol bo'limlari; tizim rollari uchun — qat'iy ro'yxat (kodda)."""
    if r.slug in SYSTEM_ROLES:
        return dict(SYSTEM_ROLES[r.slug][2])
    return dict(r.permissions) if isinstance(r.permissions, dict) else {}


def permissions_of(user) -> dict:
    if user.role == 'superadmin':
        return {k: W for k in SECTIONS}
    if user.role in SYSTEM_ROLES:
        return dict(SYSTEM_ROLES[user.role][2])
    r = role_obj(user)
    return permissions_of_role(r) if r else {}


def is_custom(user) -> bool:
    """Tizim rollaridan tashqari (superadmin yaratgan) rol."""
    return user.role not in SYSTEM_ROLES


def allows(user, section: str | None, action: str) -> bool:
    """Bo'lim bo'yicha ruxsat: o'qish — read yoki write; yozish/o'chirish — write."""
    if not _active(user) or not section:
        return False
    if user.role == 'superadmin':
        return True
    level = permissions_of(user).get(section)
    return level in LEVELS if action == 'read' else level == W


def has_any(user) -> bool:
    return _active(user) and (user.role == 'superadmin' or bool(permissions_of(user)))


def can_read_public(user, slug: str) -> bool:
    """Ochiq sayt ma'lumotlarini o'qish: har qanday faol rolga (kamida bitta bo'limi bor), shaxsiy kolleksiyalardan tashqari."""
    return has_any(user) and slug not in PRIVATE


def post_types_allowed(user, action: str) -> list[str]:
    return [t for t in POST_SECTIONS if allows(user, t, action)]


# Saytdagi kabinet rollari (HEMIS lavozimidan aniqlanadi) — admin rolga bog'lash mumkin bo'lganlari
HEMIS_ROLES = {'dean': 'Dekan', 'chair_head': 'Kafedra mudiri', 'teacher': 'O‘qituvchi', 'staff': 'Boshqa xodim'}


def is_scoped(user) -> bool:
    """Faqat o'z fakulteti doirasida ishlaydigan rol (User.scope)."""
    if user.role == 'faculty':
        return True
    r = role_obj(user) if is_custom(user) else None
    return bool(r and r.scoped)
