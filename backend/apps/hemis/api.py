"""HEMIS REST API (v1) bilan ishlash: universitetning o'z HEMIS serveri, token bilan, faqat o'qish.

Manzil va token .env'da: HEMIS_API_URL=https://hemis.<universitet>.uz/rest/v1, HEMIS_API_TOKEN=...
Javob shakli: {"success": true, "data": {"items": [...], "pagination": {"totalCount", "pageCount", "page"}}}.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


class HemisError(RuntimeError):
    pass


class HemisApi:
    """Bitta sinxronlash uchun klient. HEMIS'ga bosim tushmasligi uchun:
      - har ikki so'rov orasida kamida HEMIS_REQUEST_DELAY pauza (sahifalar ham, sonlar ham);
      - bitta sinxronlashda ko'pi bilan HEMIS_MAX_REQUESTS so'rov;
      - ketma-ket HEMIS_MAX_CONSECUTIVE_FAILURES marta xato bo'lsa — to'xtaydi (HEMIS'ni urib o'tirmaymiz);
      - 429/503 da `Retry-After` kutiladi; 4xx (401/403/404 …) da qayta urinilmaydi — foydasiz.
    """

    def __init__(self, base: str | None = None, token: str | None = None, timeout: int | None = None):
        self.base = (base or settings.HEMIS_API_URL).rstrip('/')
        self.token = token or settings.HEMIS_API_TOKEN
        self.timeout = timeout or settings.HEMIS_TIMEOUT
        if not self.base or not self.token:
            raise HemisError('HEMIS ulanmagan: .env faylida HEMIS_API_URL va HEMIS_API_TOKEN yo‘q')
        self.requests = 0          # yuborilgan so'rovlar (qayta urinishlar bilan)
        self._failures = 0         # ketma-ket xatolar
        self._last = 0.0

    def _pace(self) -> None:
        wait = self._last + settings.HEMIS_REQUEST_DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def _guard(self) -> None:
        if self.requests >= settings.HEMIS_MAX_REQUESTS:
            raise HemisError(f'HEMIS so‘rovlar chegarasiga yetdi ({settings.HEMIS_MAX_REQUESTS}) — sinxronlash to‘xtatildi')
        if self._failures >= settings.HEMIS_MAX_CONSECUTIVE_FAILURES:
            raise HemisError(f'HEMIS ketma-ket {self._failures} marta xato berdi — sinxronlash to‘xtatildi')

    def get(self, path: str, **params) -> dict:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base}/{path.lstrip('/')}" + (f'?{query}' if query else '')
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'})
        body, last = None, None
        for attempt in range(3):
            self._guard()
            self._pace()
            self.requests += 1
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as res:  # noqa: S310 — manzil .env'dan
                    body = json.loads(res.read(64 * 1024 * 1024))
                self._failures = 0
                break
            except urllib.error.HTTPError as exc:
                last = exc
                self._failures += 1
                if exc.code not in (429, 502, 503, 504):
                    break  # 401/403/404 …: qayta urinish foydasiz
                retry_after = exc.headers.get('Retry-After', '') if exc.headers else ''
                time.sleep(min(int(retry_after), 120) if retry_after.isdigit() else min(2 ** attempt, 4))
            except Exception as exc:  # noqa: BLE001
                last = exc
                self._failures += 1
                time.sleep(min(2 ** attempt, 4))  # 1s, 2s — HEMIS vaqtincha band bo'lsa urinib ko'ramiz, lekin bosmaymiz
        else:
            raise HemisError(f'HEMIS javob bermadi: {path} — {last}') from last
        if body is None:
            raise HemisError(f'HEMIS javob bermadi: {path} — {last}') from last
        if isinstance(body, dict) and body.get('success') is False:
            raise HemisError(f"HEMIS xato: {path} — {body.get('error') or body}")
        return body.get('data', body) if isinstance(body, dict) else {'items': body}

    def items(self, path: str, limit: int = 200, max_pages: int = 200, **params) -> list[dict]:
        """Barcha sahifalarni yig'ib beradi."""
        out: list[dict] = []
        page = 1
        while page <= max_pages:
            data = self.get(path, page=page, limit=limit, **params)
            items = data.get('items') if isinstance(data, dict) else data
            out.extend(items or [])
            pages = ((data.get('pagination') or {}).get('pageCount') if isinstance(data, dict) else None) or 1
            if page >= pages or not items:
                break
            page += 1
        return out

    def total(self, path: str, **params) -> int:
        """Faqat soni (masalan, fakultetdagi talabalar): pagination.totalCount."""
        data = self.get(path, page=1, limit=1, **params)
        return int(((data.get('pagination') or {}).get('totalCount')) or 0) if isinstance(data, dict) else 0
