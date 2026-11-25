"""Kirish hodisalari bo'yicha superadmin bildirishnomalari (qo'ng'iroqcha): kim kirdi, xato parollar, bloklanish, ruxsatsiz urinishlar.

Bir xil hodisa qayta-qayta yog'ilib ketmasligi uchun takrorlar `cache.add` bilan 15 daqiqada bir marta yuboriladi.
Xato bo'lsa ham kirishning o'zini to'xtatmaydi (notify ichida ushlanadi)."""
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

WINDOW = 15 * 60  # soniya — takror xabarlar oynasi (bloklanish muddati bilan bir xil)
WARN_AT = 3       # ketma-ket shuncha xato paroldan keyin ogohlantirish
LOCK_AT = 5       # auth.MAX_ATTEMPTS — hisob bloklanadi


def _superadmins():
    from apps.accounts.models import User
    return list(User.objects.filter(role='superadmin').exclude(status='disabled'))


def _where(e) -> str:
    parts = [e.browser, e.os, e.device]
    place = ' · '.join(p for p in parts if p)
    return f'{place} · IP {e.ip}' if place else f'IP {e.ip}'


def _once(key: str) -> bool:
    """Shu oynada birinchi marta bo'lsa True (keyingilari jim)."""
    return cache.add(f'secnote:{key}', 1, WINDOW)


def on_login_event(e) -> None:
    """LoginEvent yaratilgach chaqiriladi (auth.record)."""
    from apps.core.notify import notify
    who = (e.user.name or e.user.username) if e.user_id else (e.username or '—')
    via = 'HEMIS orqali' if e.method == 'hemis' else 'login va parol bilan'
    admins = _superadmins()

    if e.result == 'success':
        # Superadminning o'z kirishiga o'ziga xabar bormaydi; boshqa superadminlar ko'radi
        notify(admins, 'security', f'{who} admin panelga kirdi', f'{via} · {_where(e)}', '/kirish-tarixi', exclude=e.user)
        return

    if e.result == 'bad_password':
        since = timezone.now() - timedelta(seconds=WINDOW)
        from .models import LoginEvent
        n = LoginEvent.objects.filter(username__iexact=e.username, result='bad_password', created_at__gte=since).count()
        label = who if e.user_id else f'«{e.username}» (bunday login yo‘q)'
        if n >= LOCK_AT and _once(f'lock:{e.username.lower()}'):
            body = f'{n} marta noto‘g‘ri parol · {_where(e)}'
            notify(admins, 'security', f'{label} — hisob 15 daqiqaga bloklandi' if e.user_id else f'{label} — parol topishga urinish', body, '/kirish-tarixi')
            if e.user_id:  # hisob egasining o'ziga ham — keyin kirganda ko'radi
                notify(e.user, 'security', 'Hisobingizga 5 marta noto‘g‘ri parol kiritildi — 15 daqiqaga bloklandi',
                       f'{_where(e)} · siz bo‘lmasangiz, parolni almashtiring va 2FA ni yoqing', '/profil?tab=xavfsizlik')
        elif n == WARN_AT and _once(f'warn:{e.username.lower()}'):
            notify(admins, 'security', f'{label} — ketma-ket {n} marta noto‘g‘ri parol', _where(e), '/kirish-tarixi')
        return

    if e.result == 'denied' and _once(f'denied:{e.method}:{(e.username or "").lower()}'):
        title = (f'{who} — HEMIS orqali ruxsatsiz kirishga urinish (admin rol berilmagan)' if e.method == 'hemis'
                 else f'{who} — yopilgan hisob bilan kirishga urinish')
        notify(admins, 'security', title, _where(e), '/kirish-tarixi')
