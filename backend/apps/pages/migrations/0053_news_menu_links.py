"""Yuqori menyu: «Yangiliklar» ochiladigan ro'yxati qaytarildi — sarlavha (bo'lim sahifasi /yangiliklar) va
uchta band: Yangiliklar, Tadbirlar, E'lonlar (belgilari bilan). Guruh to'g'ridan-to'g'ri havolaga aylanib, bandlari
yo'qolgan bazalar uchun; bandlari bor bazaga tegilmaydi."""
from django.db import migrations

LINKS = [
    ('/yangiliklar?type=news', 'newspaper', {'uz': 'Yangiliklar', 'ru': 'Новости', 'en': 'News', 'zh': '新闻'}),
    ('/yangiliklar?type=events', 'calendar-days', {'uz': 'Tadbirlar', 'ru': 'Мероприятия', 'en': 'Events', 'zh': '活动'}),
    ('/yangiliklar?type=announcements', 'megaphone', {'uz': 'E’lonlar', 'ru': 'Объявления', 'en': 'Announcements', 'zh': '公告'}),
]


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    group = Page.objects.filter(group_key='news', template='group', parent=None).first()
    if not group or Page.objects.filter(parent=group).exists():
        return
    group.url = ''
    group.overview = group.overview or '/yangiliklar'
    group.save(update_fields=['url', 'overview'])
    for i, (url, icon, title) in enumerate(LINKS, 1):
        Page.objects.create(parent=group, template='link', url=url, icon=icon, title=title, order=i)


class Migration(migrations.Migration):
    dependencies = [('pages', '0052_children_tabs')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
