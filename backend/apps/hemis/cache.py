"""HEMIS klienti: bazadagi oxirgi nusxadan o'qiydi (HemisSnapshot). Nusxa hali bo'lmasa — namunaga qaytadi."""
from functools import cached_property

from .snapshot import SnapshotHemis


class CachedHemis(SnapshotHemis):
    @cached_property
    def _data(self) -> dict:
        from .models import HemisSnapshot
        snap = HemisSnapshot.objects.filter(pk=1).first()
        if snap and snap.data.get('staff') is not None:
            return snap.data
        return super()._data
