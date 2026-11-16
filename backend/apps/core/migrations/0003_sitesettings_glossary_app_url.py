from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_sitesettings_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='glossary_app_url',
            field=models.URLField(blank=True, verbose_name='AKT izohli lug‘ati: Play Market havolasi'),
        ),
    ]
