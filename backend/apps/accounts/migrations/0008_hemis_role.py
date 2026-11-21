from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_stafftask'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='hemis_role',
            field=models.CharField(blank=True, db_index=True, max_length=12, verbose_name='HEMIS roli'),
        ),
        migrations.AddField(
            model_name='user',
            name='hemis_auto',
            field=models.BooleanField(default=False, editable=False, verbose_name='HEMIS bo‘yicha avtomatik'),
        ),
    ]
