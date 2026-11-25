"""Rollar va menyu bo'limlari bo'yicha ruxsat.

Faqat `superadmin` tizim roli (hamma narsa, o'zgartirilmaydi va o'chirilmaydi — aks holda hech kim kira olmay qolishi mumkin).
Qolgan barcha rollar (editor, pages, sdg ham) oddiy: `Role.permissions` bo'yicha — bo'lim -> amallar ro'yxati
(`read` ko'rish, `create` qo'shish, `update` tahrirlash, `delete` o'chirish) va rolga biriktirilgan ruxsat to'plamlari (`PermissionSet`) —
yakuniy ruxsat ularning yig'indisi. Eski yozuv ('read' | 'write') ham o'qiladi: 'write' = qo'shish + tahrirlash + o'chirish.
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
LEVELS = ('read', 'write')  # eski (ixcham) daraja — saytdagi menyu va eski yozuvlar uchun
ACTIONS = ('read', 'create', 'update', 'delete')
WRITE_ACTIONS = ('create', 'update', 'delete')
# Bo'lim -> admin panel sahifasi (admin/src/components/AppSidebar.vue bilan bir xil). Saytdagi «Mening bo'limlarim» menyusi shu yerdan oladi
SECTION_PATHS: dict[str, str] = {
    'dashboard': '/', 'news': '/postlar/news', 'announcements': '/postlar/announcements', 'events': '/postlar/events', 'pages': '/sahifalar',
    'quick-links': '/tezkor-xizmatlar', 'phones': '/telefonlar', 'rude-words': '/haqoratli-sozlar', 'admission': '/qabul-yillari', 'units': '/bolimlar',
    'media': '/media', 'documents': '/hujjatlar', 'videos': '/video', 'faculties': '/fakultetlar', 'departments': '/kafedralar',
    'leaders': '/rahbariyat', 'staff': '/xodimlar', 'sdg': '/brm',
}
POST_SECTIONS = ('news', 'announcements', 'events')

# Faqat superadmin: bu kolleksiyalarni o'qish ham yopiq
PRIVATE = frozenset({'users', 'login-events', 'activity', 'roles', 'permission-sets', 'applications'})
# Ruxsatlar jadvalida bo'limi YO'Q kolleksiya/global'lar — ularni faqat superadmin yozadi (ataylab). Yangi model qo'shilganda u yoki
# `section` (SECTIONS kaliti) oladi, yoki shu ro'yxatga yoziladi — aks holda tests/panel/test_sections_registry.py xato beradi.
SUPER_ONLY = PRIVATE | frozenset({'categories', 'slides', 'settings', 'symbols', 'home-banner'})

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


def actions_of(value) -> list[str]:
    """Bitta bo'lim qiymati → amallar: 'read' | 'write' (eski) yoki ['read','create',…]. Har qanday yozish amali ko'rishni ham beradi."""
    if value == 'read':
        got = {'read'}
    elif value == 'write':
        got = set(ACTIONS)
    elif isinstance(value, (list, tuple, set)):
        got = {a for a in value if a in ACTIONS}
    else:
        got = set()
    if got & set(WRITE_ACTIONS):
        got.add('read')
    return [a for a in ACTIONS if a in got]


def normalize(perms) -> dict:
    """{bo'lim: amallar} — faqat mavjud bo'limlar, bo'sh bo'limlar tashlanadi."""
    if not isinstance(perms, dict):
        return {}
    out = {k: actions_of(v) for k, v in perms.items() if k in SECTIONS}
    return {k: v for k, v in out.items() if v}


def merge(*perm_dicts) -> dict:
    """Bir nechta ruxsat to'plamining yig'indisi (rol o'zi + biriktirilgan to'plamlar)."""
    got: dict[str, set] = {}
    for d in perm_dicts:
        for k, acts in normalize(d).items():
            got.setdefault(k, set()).update(acts)
    return {k: [a for a in ACTIONS if a in v] for k, v in got.items()}


def level_of(actions) -> str | None:
    """Ixcham daraja (saytdagi menyu, eski mijozlar): biror yozish amali bo'lsa 'write', faqat ko'rish — 'read'."""
    acts = actions_of(actions)
    return 'write' if set(acts) & set(WRITE_ACTIONS) else ('read' if acts else None)


def clean_permissions(value) -> dict:
    """Faqat mavjud bo'lim va to'g'ri amallar qoladi (eski 'read'/'write' ham qabul qilinadi)."""
    return normalize(value)


def _active(user) -> bool:
    return bool(user and user.is_authenticated and user.status != 'disabled')


def role_obj(user):
    """Foydalanuvchi roli (so'rov davomida keshlanadi)."""
    if not hasattr(user, '_role_obj'):
        from .models import Role
        user._role_obj = Role.objects.filter(slug=user.role).first()
    return user._role_obj


def permissions_of_role(r) -> dict:
    """Rolning yakuniy ruxsati {bo'lim: amallar}: superadmin — hammasi (kodda); qolganlari — o'z belgilari + biriktirilgan
    ruxsat to'plamlari (`PermissionSet`) yig'indisi."""
    if r.slug in SYSTEM_ROLES:
        return normalize(SYSTEM_ROLES[r.slug][2])
    sets = [ps.permissions for ps in r.permission_sets.all()] if r.pk else []
    return merge(r.permissions, *sets)


def permissions_of(user) -> dict:
    if user.role == 'superadmin':
        return {k: list(ACTIONS) for k in SECTIONS}
    if not hasattr(user, '_perms'):
        r = role_obj(user)
        user._perms = permissions_of_role(r) if r else {}
    return user._perms


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
    """Bo'lim bo'yicha ruxsat: `read`, `create`, `update`, `delete` — aniq amal; `write` — biror yozish amali (qo'shish/tahrirlash/o'chirish)."""
    if not _active(user) or not section:
        return False
    if user.role == 'superadmin':
        return True
    acts = permissions_of(user).get(section) or []
    if action == 'write':
        return bool(set(acts) & set(WRITE_ACTIONS))
    return action in acts


def has_any(user) -> bool:
    return _active(user) and (user.role == 'superadmin' or bool(permissions_of(user)))


def can_read_public(user, slug: str) -> bool:
    """Ochiq sayt ma'lumotlarini o'qish: har qanday faol rolga (kamida bitta bo'limi bor), shaxsiy kolleksiyalardan tashqari."""
    return has_any(user) and slug not in PRIVATE


def post_types_allowed(user, action: str) -> list[str]:
    return [t for t in POST_SECTIONS if allows(user, t, action)]



def is_scoped(user) -> bool:
    """Faqat o'z fakulteti doirasida ishlaydigan rol (User.scope)."""
    r = role_obj(user) if is_custom(user) else None
    return bool(r and r.scoped)


def catalog() -> list[dict]:
    """Ruxsatlar jadvali uchun barcha bo'limlar (admin panel shu ro'yxatdan quradi — yangi bo'lim bu yerga qo'shilsa, «Rollar» va
    «Ruxsatlar kutubxonasi» jadvallarida o'zi paydo bo'ladi): kalit, nom, guruh, admin sahifasi."""
    return [{'key': k, 'label': label, 'group': group, 'path': SECTION_PATHS.get(k, '/')} for k, (label, group) in SECTIONS.items()]


def sections_of(perms: dict) -> list[dict]:
    """Rol bo'limlari ro'yxati (menyudagi tartibda; «Boshqaruv paneli» alohida tugma — bu yerga kirmaydi): kalit, nom, guruh,
    ixcham daraja (read/write) va aniq amallar."""
    perms = normalize(perms)
    return [{'key': k, 'label': SECTIONS[k][0], 'group': SECTIONS[k][1], 'level': level_of(perms[k]), 'actions': perms[k]}
            for k in SECTIONS if k != 'dashboard' and perms.get(k)]
