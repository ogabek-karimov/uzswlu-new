"""HEMIS orqali kirgan xodim → admin panel hisobi.

Rolni FAQAT admin beradi: Foydalanuvchilar sahifasida hisob yaratadi, rol tanlaydi va HEMIS ID yozadi. Shu xodim HEMIS orqali
kirganda shu hisob (va roli) ishlatiladi — admin panelga ham, saytdagi kabinetga ham. HEMIS lavozimi (dekan, mudir, o'qituvchi)
hech qanday rol yoki kirish huquqi bermaydi; HEMIS'dan faqat ism, lavozim va bo'lim nomi yangilanadi.
(Avvalgi «HEMIS roli» — lavozim bo'yicha avtomatik rol berish — accounts.0011 bilan olib tashlangan.)"""
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import permissions_of, role_obj


def _context(hemis_id: str):
    from apps.api.builders_staff import find_person
    from apps.api.cabinet_roles import detect_role

    person = find_person(str(hemis_id), 'uz')
    if not person:
        return None
    role, emp = detect_role(person)
    return person, role, emp


def account(hemis_id: str) -> User | None:
    """Admin bergan faol hisob (HEMIS ID bo'yicha) yoki None."""
    return User.objects.filter(hemis_id=str(hemis_id)).exclude(hemis_id='').exclude(status='disabled').first()


def panel_access(hemis_id: str):
    """Shu xodim admin panelga kira oladimi va nimalarga: (rol nomi, {bo'lim: daraja}) yoki None. Hech narsa yozmaydi.
    Saytdagi kabinet tugmasi va profil menyusi («Mening bo'limlarim») shundan foydalanadi."""
    user = account(hemis_id)
    if not user:
        return None
    r = role_obj(user)
    return (r.name if r else user.role), permissions_of(user)


def cabinet_allowed(hemis_id: str) -> bool:
    """Saytdagi kabinetga kirish: faqat admin HEMIS ID biriktirgan faol hisob egasi. Keshlanmaydi — hisob yopilsa yoki HEMIS ID
    olib tashlansa darhol yopiladi."""
    return account(hemis_id) is not None


def eligible(hemis_id: str) -> bool:
    """Shu xodim admin panelga kira oladimi (kabinetda «Admin panel» tugmasi uchun) — hech narsa yozmaydi."""
    return account(hemis_id) is not None


def provision(hemis_id: str, name: str = '') -> User | None:
    """HEMIS orqali kirish: admin bergan hisobni topadi va ism/lavozim/bo'limni HEMIS'dan yangilaydi (roli o'zgarmaydi).
    Hisob bo'lmasa yoki yopilgan bo'lsa — None (hisob o'zi yaratilmaydi)."""
    user = account(hemis_id)
    if not user:
        return None
    ctx = _context(str(hemis_id))
    if ctx:
        user.name = (name or ctx[0].get('name') or user.name)[:200]
        user.position = (((ctx[2] or {}).get('position') or {}).get('name') or user.position)[:200]
        user.department = (((ctx[2] or {}).get('department') or {}).get('name') or user.department)[:200]
    user.last_login = timezone.now()
    user.save()
    return user
