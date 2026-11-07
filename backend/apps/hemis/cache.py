"""HEMIS klienti: bazadagi oxirgi nusxadan o'qiydi (HemisSnapshot). Nusxa hali bo'lmasa — namunaga qaytadi.

Nusxa har so'rovda emas, har HEMIS_CACHE_SECONDS (sukut 300 s) da bir marta bazadan qayta o'qiladi: sinxronlash alohida
jarayonda ishlaydi va yangi ma'lumot qayta ishga tushirmasdan ko'rinadi, baza esa ortiqcha yuklanmaydi.
Xodimlar ro'yxati (til bo'yicha) ham shu muddatga xotirada saqlanadi — har so'rovda minglab xodimni qayta yig'maslik uchun.
"""
import threading
import time

from django.conf import settings

from .snapshot import SnapshotHemis


class CachedHemis(SnapshotHemis):
    _lock = threading.Lock()
    _loaded_at = 0.0
    _loaded: dict | None = None
    _memo: dict = {}

    @property
    def _data(self) -> dict:
        now = time.monotonic()
        if self._loaded is None or now - self._loaded_at > settings.HEMIS_CACHE_SECONDS:
            with self._lock:
                if self._loaded is None or time.monotonic() - self._loaded_at > settings.HEMIS_CACHE_SECONDS:
                    from .models import HemisSnapshot
                    snap = HemisSnapshot.objects.filter(pk=1).first()
                    if snap and snap.data.get('staff') is not None:
                        data = snap.data
                    else:
                        from .snapshot import SnapshotHemis as Base
                        data = Base._data.func(self)  # namuna fayl
                    self._loaded, self._loaded_at, self._memo = data, time.monotonic(), {}
        return self._loaded

    def staff(self, lang: str) -> list[dict]:
        self._data  # muddati o'tgan bo'lsa nusxani yangilaydi (va _memo'ni tozalaydi)
        memo = self._memo
        if lang not in memo:
            memo[lang] = super().staff(lang)
        return memo[lang]
