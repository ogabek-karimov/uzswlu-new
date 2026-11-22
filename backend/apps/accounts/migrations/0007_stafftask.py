from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Vazifa')),
                ('note', models.TextField(blank=True, max_length=2000, verbose_name='Izoh')),
                ('assignee_id', models.CharField(db_index=True, max_length=40, verbose_name='Ijrochi (HEMIS ID)')),
                ('assignee_name', models.CharField(blank=True, max_length=200, verbose_name='Ijrochi')),
                ('author_id', models.CharField(db_index=True, max_length=40, verbose_name='Bergan (HEMIS ID)')),
                ('author_name', models.CharField(blank=True, max_length=200, verbose_name='Bergan')),
                ('due', models.DateField(blank=True, null=True, verbose_name='Muddat')),
                ('status', models.CharField(choices=[('open', 'Bajarilmoqda'), ('done', 'Bajarildi')], default='open', max_length=8, verbose_name='Holat')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('done_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Xodim vazifasi',
                'verbose_name_plural': 'Xodim vazifalari',
                'ordering': ['status', 'due', '-created_at'],
            },
        ),
    ]
