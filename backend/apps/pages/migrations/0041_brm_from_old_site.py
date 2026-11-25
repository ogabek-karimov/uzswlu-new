"""BRM: eski saytdagi 1–17 maqsadlar ichki bölimlari (matn, tablar) va hujjatlari, «SDG report» va «Ta’lim va barqarorlik»
ichki sahifalari. PDF'lar fayl bölsa ulanadi, aks holda `manage.py seed_activity --part 3`."""
from django.db import migrations

from apps.pages.activity_seed import seed_files, seed_goal_files, seed_goals, seed_pages


def forward(apps, schema_editor):
    Page, Media = apps.get_model('pages', 'Page'), apps.get_model('core', 'Media')
    seed_pages(Page, 3)
    seed_files(Page, apps.get_model('pages', 'PageAttachment'), Media, 3)
    SdgGoal = apps.get_model('pages', 'SdgGoal')
    seed_goals(SdgGoal, apps.get_model('pages', 'SdgSection'))
    seed_goal_files(SdgGoal, apps.get_model('pages', 'SdgGoalReport'), Media)


class Migration(migrations.Migration):
    dependencies = [('pages', '0040_sdg_report_section')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
