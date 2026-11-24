"""Bildirishnomalar: yaratish va o'qish. Yaratishdagi xato asosiy amalni to'xtatmaydi (log_activity kabi)."""
import logging

from django.utils import timezone

log = logging.getLogger(__name__)
KEEP = 200  # har foydalanuvchiga eng ko'pi bilan shuncha (eskilari o'chadi)


def notify(users, kind: str, title: str, body: str = '', link: str = '', exclude=None) -> None:
    """`users` — foydalanuvchi yoki ro'yxat; `exclude` — amalni bajargan odam (o'ziga xabar bormaydi). Yopilgan hisobga yuborilmaydi."""
    from .models import Notification
    try:
        targets = users if isinstance(users, (list, tuple, set)) else [users]
        for u in targets:
            if not u or getattr(u, 'status', 'active') == 'disabled' or (exclude is not None and u.pk == getattr(exclude, 'pk', None)):
                continue
            Notification.objects.create(user=u, kind=kind, title=title[:300], body=(body or '')[:500], link=(link or '')[:300])
            stale = Notification.objects.filter(user=u).order_by('-created_at', '-id').values_list('id', flat=True)[KEEP:]
            Notification.objects.filter(id__in=list(stale)).delete()
    except Exception:  # noqa: BLE001
        log.exception('notify failed')


def out(n) -> dict:
    return {'id': n.pk, 'kind': n.kind, 'title': n.title, 'body': n.body or None, 'link': n.link or None,
            'read': n.read_at is not None, 'createdAt': n.created_at.isoformat()}


def listing(user, limit: int = 20) -> dict:
    """Faqat shu foydalanuvchining bildirishnomalari (boshqasinikini ID bilan ham olib bo'lmaydi)."""
    from .models import Notification
    if not user:
        return {'unread': 0, 'docs': []}
    qs = Notification.objects.filter(user=user)
    return {'unread': qs.filter(read_at__isnull=True).count(), 'docs': [out(n) for n in qs[:max(1, min(limit, 50))]]}


def mark_read(user, ids=None) -> int:
    """`ids` bo'lmasa — hammasi. Faqat o'zinikini belgilaydi (begona ID e'tiborsiz qoladi)."""
    from .models import Notification
    if not user:
        return 0
    qs = Notification.objects.filter(user=user, read_at__isnull=True)
    if ids:
        qs = qs.filter(id__in=[int(i) for i in ids if str(i).isdigit()])
    return qs.update(read_at=timezone.now())
