"""Video bölimi: Online translatsiya va Video darsliklar uçun menyu belgilari (faqat belgi böş bölsa)."""
from django.db import migrations


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Page.objects.filter(slug='online-translatsiya', icon='').update(icon='radio-tower')
    Page.objects.filter(url='/video-darsliklar', icon='').update(icon='clapperboard')


class Migration(migrations.Migration):
    dependencies = [('pages', '0046_showcase_intro_html_to_body')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
