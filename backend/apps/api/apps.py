from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'apps.api'
    label = 'api'
    verbose_name = 'Sayt API'

    def ready(self):
        # Xodim kabineti, HEMIS nusxasi yoki media o'zgarsa — ochiq API keshi eskirib qolmasin
        from django.db.models.signals import post_delete, post_save

        from apps.core.models import Media
        from apps.hemis.models import HemisSnapshot
        from apps.structure.models import StaffDocument, StaffProfile

        from .common import bump_content_version

        def bump(sender, **kwargs):
            try:
                bump_content_version()
            except Exception:  # noqa: BLE001 — kesh o'chiq bo'lsa ham saqlash to'xtamasin
                pass

        for model in (StaffProfile, StaffDocument, Media, HemisSnapshot):
            post_save.connect(bump, sender=model, weak=False, dispatch_uid=f'bump-{model.__name__}')
            post_delete.connect(bump, sender=model, weak=False, dispatch_uid=f'bump-del-{model.__name__}')
