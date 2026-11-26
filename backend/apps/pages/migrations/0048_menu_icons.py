"""Menyu belgilari: Yangiliklar va Ta'lim yönalişlari ichidagi sahifalarga mos belgi
(lucide nomlari). Faqat belgi hali böş sahifalar yangilanadi — admin qöygan belgiga tegilmaydi."""
from django.db import migrations

ICONS = {
    # Yangiliklar
    '/yangiliklar?type=news': 'newspaper', '/yangiliklar?type=events': 'calendar-days', '/yangiliklar?type=announcements': 'megaphone',
    # Ta'lim yönalişlari
    '/bakalavriat': 'book-open', '/magistratura': 'graduation-cap',
}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for key, icon in ICONS.items():
        qs = Page.objects.filter(url=key) if key.startswith('/') else Page.objects.filter(slug=key)
        qs.filter(icon='').update(icon=icon)


class Migration(migrations.Migration):
    dependencies = [('pages', '0047_video_icons')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
