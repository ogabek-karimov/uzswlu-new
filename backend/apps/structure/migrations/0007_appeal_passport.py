from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('structure', '0006_seed_phones')]
    operations = [
        migrations.AddField(
            model_name='appeal', name='passport',
            field=models.CharField(blank=True, help_text='Masalan AA1234567', max_length=9, verbose_name='Pasport seriyasi va raqami'),
        ),
    ]
