"""HEMIS REST API (v1) bilan ishlash: universitetning o'z HEMIS serveri, token bilan, faqat o'qish.

Manzil va token .env'da: HEMIS_API_URL=https://hemis.<universitet>.uz/rest/v1, HEMIS_API_TOKEN=...
Javob shakli: {"success": true, "data": {"items": [...], "pagination": {"totalCount", "pageCount", "page"}}}.
"""
import json
import time
import urllib.parse
import urllib.request

from django.conf import settings


class HemisError(RuntimeError):
    pass


class HemisApi:
    def __init__(self, base: str | None = None, token: str | None = None, timeout: int | None = None):
        self.base = (base or settings.HEMIS_API_URL).rstrip('/')
        self.token = token or settings.HEMIS_API_TOKEN
        self.timeout = timeout or settings.HEMIS_TIMEOUT
        if not self.base or not self.token:
            raise HemisError('HEMIS ulanmagan: .env faylida HEMIS_API_URL va HEMIS_API_TOKEN yo‘q')

    def get(self, path: str, **params) -> dict:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{self.base}/{path.lstrip('/')}" + (f'?{query}' if query else '')
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'})
        body, last = None, None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as res:  # noqa: S310 — manzil .env'dan
                    body = json.loads(res.read(64 * 1024 * 1024))
                break
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(min(2 ** attempt, 4))  # 1s, 2s — HEMIS vaqtincha band bo'lsa urinib ko'ramiz, lekin bosmaymiz
        else:
            raise HemisError(f'HEMIS javob bermadi: {path} — {last}') from last
        if isinstance(body, dict) and body.get('success') is False:
            raise HemisError(f"HEMIS xato: {path} — {body.get('error') or body}")
        return body.get('data', body) if isinstance(body, dict) else {'items': body}

    def items(self, path: str, limit: int = 200, max_pages: int = 200, **params) -> list[dict]:
        """Barcha sahifalarni yig'ib beradi."""
        out: list[dict] = []
        page = 1
        while page <= max_pages:
            if page > 1:
                time.sleep(settings.HEMIS_REQUEST_DELAY)  # sahifalar orasida pauza: HEMIS'ga bosim tushmasin
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
