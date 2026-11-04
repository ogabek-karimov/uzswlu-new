from django.apps import AppConfig


class PanelConfig(AppConfig):
    """Vue admin panel uchun API (/api/cms/*) — Payload CMS bilan bir xil shakl, admin panel o'zgarishsiz ishlaydi."""

    name = 'apps.panel'
    verbose_name = 'Admin panel (tizim)'
