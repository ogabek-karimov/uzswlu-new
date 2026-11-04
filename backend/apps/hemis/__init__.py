from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string


@lru_cache(maxsize=1)
def get_client():
    """Sozlamadagi HEMIS klienti (bitta nusxa)."""
    return import_string(settings.HEMIS_CLIENT)()
