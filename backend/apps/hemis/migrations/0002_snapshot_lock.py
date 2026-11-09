from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('hemis', '0001_initial')]
    operations = [
        migrations.AddField(model_name='hemissnapshot', name='running_since',
                            field=models.DateTimeField(blank=True, null=True, verbose_name='Sinxronlash boshlangan')),
    ]
