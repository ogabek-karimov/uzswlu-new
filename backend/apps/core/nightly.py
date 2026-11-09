"""Kechki vazifalar: har biri mustaqil, biri yiqilsa qolganlari ishlayveradi. `run_nightly` shularni tinch oynada ishga tushiradi."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

log = logging.getLogger('nightly')


def hemis_sync(force: bool = False) -> str:
    if not settings.HEMIS_API_URL:
        return 'o‘tkazib yuborildi (HEMIS_API_URL bo‘sh)'
    call_command('sync_hemis', force=force)
    return 'ok'


def cleanup_sessions(force: bool = False) -> str:
    from apps.accounts.models import StaffSession
    from apps.panel.models import RevokedToken
    now = timezone.now()
    sessions = StaffSession.objects.filter(expires_at__lt=now).delete()[0]
    tokens = RevokedToken.objects.filter(expires_at__lt=now).delete()[0]
    call_command('clearsessions')
    return f'{sessions} xodim sessiyasi, {tokens} bekor qilingan token tozalandi'


def prune_login_events(force: bool = False) -> str:
    from apps.panel.models import LoginEvent
    days = settings.LOGIN_EVENT_RETENTION_DAYS
    if not days:
        return 'o‘chirilgan (LOGIN_EVENT_RETENTION_DAYS=0)'
    deleted = LoginEvent.objects.filter(created_at__lt=timezone.now() - timedelta(days=days)).delete()[0]
    return f'{deleted} eski kirish yozuvi o‘chirildi (> {days} kun)'


def prune_hits(force: bool = False) -> str:
    """Sayt statistikasi jadvali cheksiz o'smasin: eski yozuvlar bo'laklab (bazani qotirmasdan) o'chiriladi."""
    from apps.core.models import Hit
    days = settings.HIT_RETENTION_DAYS
    if not days:
        return 'o‘chirilgan (HIT_RETENTION_DAYS=0)'
    cutoff, total = timezone.now() - timedelta(days=days), 0
    while True:
        ids = list(Hit.objects.filter(ts__lt=cutoff).values_list('pk', flat=True)[:5000])
        if not ids:
            break
        total += Hit.objects.filter(pk__in=ids).delete()[0]
    return f'{total} eski statistika yozuvi o‘chirildi (> {days} kun)'


def backup(force: bool = False) -> str:
    if not settings.BACKUP_ENABLED:
        return 'o‘chirilgan (BACKUP_ENABLED=0)'
    from apps.core import backup as bk
    try:
        return bk.run_scheduled()
    except bk.BackupError as exc:
        raise CommandError(str(exc)) from exc


TASKS = [('backup', backup), ('hemis', hemis_sync), ('sessions', cleanup_sessions), ('login-events', prune_login_events), ('hits', prune_hits)]


def run_all(only: str | None = None, force: bool = False) -> dict[str, str]:
    results = {}
    for name, fn in TASKS:
        if only and name != only:
            continue
        try:
            results[name] = fn(force=force)
        except CommandError as exc:
            results[name] = f'XATO: {exc}'
        except Exception as exc:  # noqa: BLE001 — bitta vazifa boshqasini to'xtatmasin
            log.exception('nightly %s', name)
            results[name] = f'XATO: {exc}'
        log.info('nightly %s: %s', name, results[name])
    return results
