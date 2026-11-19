from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0005_sitesettings_symbols_background')]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='show_buildings_link',
            field=models.BooleanField(default=True, verbose_name='Chap panelda «O‘quv binolari» belgisini ko‘rsatish'),
        ),
    ]
