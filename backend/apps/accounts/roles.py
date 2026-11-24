"""Rollar va menyu bo'limlari bo'yicha ruxsat.

Faqat `superadmin` tizim roli (hamma narsa, o'zgartirilmaydi va o'chirilmaydi — aks holda hech kim kira olmay qolishi mumkin).
Qolgan barcha rollar (editor, pages, sdg ham) oddiy: `Role.permissions` bo'yicha — bo'lim -> 'read' | 'write'; superadmin ularni
admin panelda o'zgartiradi yoki o'chiradi.
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
    'admission': ('Qabul yillari', 'Kontent'),
    'units': ('Bo‘limlar', 'Kontent'),
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
# Bo'lim -> admin panel sahifasi (admin/src/components/AppSidebar.vue bilan bir xil). Saytdagi «Mening bo'limlarim» menyusi shu yerdan oladi
SECTION_PATHS: dict[str, str] = {
    'dashboard': '/', 'news': '/postlar/news', 'announcements': '/postlar/announcements', 'events': '/postlar/events', 'pages': '/sahifalar',
    'quick-links': '/tezkor-xizmatlar', 'phones': '/telefonlar', 'rude-words': '/haqoratli-sozlar', 'admission': '/qabul-yillari', 'units': '/bolimlar',
    'media': '/media', 'documents': '/hujjatlar', 'videos': '/video', 'faculties': '/fakultetlar', 'departments': '/kafedralar',
    'leaders': '/rahbariyat', 'staff': '/xodimlar', 'sdg': '/brm',
}
POST_SECTIONS = ('news', 'announcements', 'events')

# Faqat superadmin: bu kolleksiyalarni o'qish ham yopiq
PRIVATE = frozenset({'users', 'login-events', 'activity', 'roles', 'applications'})

W, R = 'write', 'read'
# Tayyor rollarning boshlang'ich holati (migratsiya 0006 va testlar shundan oladi; keyin ular bazada o'zgartiriladi)
BUILTIN = {
    'superadmin': ('Superadmin', 'Hamma narsa', {k: W for k in SECTIONS}, False),
    'editor': ('Kontent muharriri', 'Yangiliklar, e’lonlar, tadbirlar', {'dashboard': W, 'news': W, 'announcements': W, 'events': W, 'media': W}, False),
    'faculty': ('Fakultet admini', 'O‘z fakulteti va kafedralari', {'dashboard': W, 'news': W, 'announcements': W, 'events': W, 'media': W, 'faculties': W, 'departments': W}, True),
    'pages': ('Sahifalar muharriri', 'Sahifalar, hujjatlar, video', {'dashboard': W, 'news': W, 'announcements': W, 'events': W, 'media': W, 'pages': W, 'quick-links': W, 'phones': W, 'rude-words': W, 'admission': W, 'units': W, 'documents': W, 'videos': W}, False),
    'sdg': ('BRM menejeri', 'Faqat BRM bo‘limi', {'sdg': W, 'media': W}, False),
}
# Tizim roli — faqat superadmin: ruxsatlari kodda qat'iy, o'chirilmaydi
SYSTEM_ROLES = {'superadmin': BUILTIN['superadmin']}
# Tayyor namunalar (accounts.0009 bazadan o'chirgan; testlar qayta yaratadi)
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
    """Rol bo'limlari: superadmin — hammasi (kodda), qolganlari — bazadan (`Role.permissions`)."""
    if r.slug in SYSTEM_ROLES:
        return dict(SYSTEM_ROLES[r.slug][2])
    return dict(r.permissions) if isinstance(r.permissions, dict) else {}


def permissions_of(user) -> dict:
    if user.role == 'superadmin':
        return {k: W for k in SECTIONS}
    r = role_obj(user)
    return permissions_of_role(r) if r else {}


def is_custom(user) -> bool:
    """Superadmindan boshqa har qanday rol: ruxsati bazadagi bo'limlari bo'yicha."""
    return user.role not in SYSTEM_ROLES


def edits_all_posts(user) -> bool:
    """Boshqalarning post/e'lon/tadbirlarini ham tahrirlay va o'chira oladimi (aks holda — faqat o'zi yozganini)."""
    if user.role == 'superadmin':
        return True
    r = role_obj(user)
    return bool(r and r.edit_all)


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
    r = role_obj(user) if is_custom(user) else None
    return bool(r and r.scoped)


def sections_of(perms: dict) -> list[dict]:
    """Rol bo'limlari ro'yxati (menyudagi tartibda; «Boshqaruv paneli» alohida tugma — bu yerga kirmaydi): kalit, nom, guruh, daraja."""
    return [{'key': k, 'label': SECTIONS[k][0], 'group': SECTIONS[k][1], 'level': perms[k]}
            for k in SECTIONS if k != 'dashboard' and perms.get(k) in LEVELS]
