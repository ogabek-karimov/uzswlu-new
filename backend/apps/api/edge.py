"""Kontent o'zgarganda sayt qatlamlari keshini darrov yangilash (Nuxt + nginx).

Backend keshi `content_ver` bilan zumda eskiradi. Lekin oldindagi qatlamlar o'z muddati (Nuxt 5 daqiqagacha, nginx 30–60 s)
tugamaguncha eski sahifani berardi. Shuning uchun `bump_content_version()` dan keyin fonda:
  1. Nuxt'ning ichki keshi tozalanadi (`POST EDGE_PURGE_URL`, `Authorization: Bearer <API_TOKEN>`);
  2. nginx orqali bosh sahifalar `X-Cache-Refresh: <EDGE_REFRESH_TOKEN>` sarlavhasi bilan so'raladi — nginx keshni chetlab
     o'tib yangi nusxani saqlaydi (ochiq nginx'da `purge` yo'q, shuning uchun «yangilash» usuli).
Hammasi ixtiyoriy: sozlama bo'sh bo'lsa hech narsa qilinmaydi. Xato bo'lsa saqlash to'xtamaydi — TTL baribir yangilaydi.
Ketma-ket ko'p saqlash (masalan 20 ta rasm) bitta yangilanishga birlashtiriladi.
"""
import logging
import threading
import time
import urllib.request

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 1.5   # shu oraliqdagi barcha o'zgarishlar bitta yangilanish bo'ladi
TIMEOUT = 5


def edge_enabled() -> bool:
    return bool(settings.EDGE_PURGE_URL or (settings.EDGE_REFRESH_URLS and settings.EDGE_REFRESH_TOKEN))


def _first_token() -> str:
    return next((t.strip() for t in (settings.API_TOKEN or '').split(',') if t.strip()), '')


def _request(url: str, method: str, headers: dict) -> None:
    req = urllib.request.Request(url, method=method, headers=headers, data=b'' if method == 'POST' else None)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 — manzillar .env dan (ishonchli)
        resp.read(1)


def refresh_edge() -> dict:
    """Nuxt keshini tozalaydi, so'ng nginx'dagi sahifalarni yangilaydi. Natija: {'purge': bool|None, 'refreshed': n}."""
    out = {'purge': None, 'refreshed': 0}
    if settings.EDGE_PURGE_URL:
        try:
            _request(settings.EDGE_PURGE_URL, 'POST', {'Authorization': f'Bearer {_first_token()}'})
            out['purge'] = True
        except Exception as exc:  # noqa: BLE001
            out['purge'] = False
            log.warning('Nuxt keshini tozalab bo‘lmadi: %s', exc)
    if settings.EDGE_REFRESH_URLS and settings.EDGE_REFRESH_TOKEN:
        for url in settings.EDGE_REFRESH_URLS:
            try:
                _request(url, 'GET', {'X-Cache-Refresh': settings.EDGE_REFRESH_TOKEN})
                out['refreshed'] += 1
            except Exception as exc:  # noqa: BLE001
                log.warning('nginx sahifasini yangilab bo‘lmadi (%s): %s', url, exc)
    return out


def _worker() -> None:
    time.sleep(DEBOUNCE_SECONDS)
    refresh_edge()


def schedule_edge_refresh() -> bool:
    """Fon oqimida yangilashni rejalashtiradi. Qaytadi: rejalashtirildimi (o'chiq yoki allaqachon rejalangan bo'lsa — False)."""
    if not edge_enabled():
        return False
    try:
        if not cache.add('edge_refresh_pending', 1, DEBOUNCE_SECONDS):
            return False   # shu oynada allaqachon rejalangan — o'zgarish unda hisobga olinadi
    except Exception:  # noqa: BLE001 — kesh o'chiq bo'lsa ham yangilashga urinamiz
        pass
    threading.Thread(target=_worker, name='edge-refresh', daemon=True).start()
    return True
