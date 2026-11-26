from django.core.management.base import BaseCommand

from apps.core.models import Media
from apps.pages.admission_seed import seed_admission
from apps.pages.models import Page, PageAttachment
from apps.pages.structure_seed import seed_structure


class Command(BaseCommand):
    help = "Qabul bo'limi va Tuzilma sahifalari PDF'lari (eski saytdan); katta fayllar files-large'ga qo'yilgach qayta ishga tushiring"

    def handle(self, *args, **opts):
        n = seed_admission(Page, PageAttachment, Media) + seed_structure(Page, PageAttachment, Media)
        self.stdout.write(self.style.SUCCESS(f'{n} ta PDF ulandi'))
