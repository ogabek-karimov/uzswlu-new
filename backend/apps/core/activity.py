"""Faollik jurnali va sayt keshini yangilash."""
import json
import logging
import urllib.request

from django.conf import settings
from django.db import transaction

from .models import Activity
from .utils import client_ip

log = logging.getLogger(__name__)


def short(value) -> str:
    if hasattr(value, 'pk') and not isinstance(value, (str, bytes)):
        return str(getattr(value, 'name', None) or value.pk)
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return s if len(s) <= 120 else s[:117] + '…'


def log_activity(request, *, action: str, entity: str, entity_id=None, label: str | None = None, changes: dict | None = None):
    """Xato bo'lsa ham asosiy amalni to'xtatmaydi."""
    try:
        user = getattr(request, 'user', None)
        authed = bool(user and user.is_authenticated)
        Activity.objects.create(
            user=user if authed else None,
            user_name=(getattr(user, 'name', '') or getattr(user, 'username', '') or 'tizim') if authed else 'tizim',
            action=action,
            entity=entity,
            entity_id='' if entity_id is None else str(entity_id),
            label=(label or '')[:300],
            changes=changes or {},
            ip=client_ip(request) if request is not None else '',
        )
    except Exception:  # noqa: BLE001
        log.exception('activity log failed')


def purge_site_cache(tags) -> None:
    """Nuxt keshini yangilash: o'zgargan kontent darhol ko'rinsin. Sayt o'chiq bo'lsa ham saqlash davom etadi."""
    from apps.api.common import bump_content_version
    bump_content_version()
    url = settings.SITE_PURGE_URL
    if not url:
        return

    def send():
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps({'tags': list(tags)}).encode(),
                headers={'content-type': 'application/json', 'authorization': f'Bearer {settings.SITE_PURGE_TOKEN}'},
                method='POST',
            )
            urllib.request.urlopen(req, timeout=3).close()  # noqa: S310 — manzil .env'dan
        except Exception:  # noqa: BLE001
            log.warning('site purge failed', exc_info=True)

    transaction.on_commit(send)
