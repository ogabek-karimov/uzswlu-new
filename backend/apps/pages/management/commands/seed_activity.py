from pathlib import Path

from django.core.management.base import BaseCommand

from apps.core.models import Media
from apps.pages.activity_seed import BRM_FILES, FILES, seed_files, seed_goal_files, seed_goals, seed_pages
from apps.pages.models import Page, PageAttachment, SdgGoal, SdgGoalReport, SdgSection


class Command(BaseCommand):
    help = "«Faoliyat» sahifalari va PDF'larini eski sayt ma'lumotlaridan ulaydi; --part 3 — BRM (SDG report, Ta’lim va barqarorlik, 1–17 maqsadlar). Takror işlatiş xavfsiz."

    def add_arguments(self, parser):
        parser.add_argument('--part', type=int, default=1)
        parser.add_argument('--dir', default=str(FILES), help="PDF'lar papkasi")

    def handle(self, *args, part, dir, **opts):
        seed_pages(Page, part)
        n = seed_files(Page, PageAttachment, Media, part, Path(dir))
        if part == 3:
            seed_goals(SdgGoal, SdgSection)
            n += seed_goal_files(SdgGoal, SdgGoalReport, Media, BRM_FILES)
        self.stdout.write(self.style.SUCCESS(f'{n} ta PDF ulandi'))
