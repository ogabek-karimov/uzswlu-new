from django.db import migrations, models

from apps.accounts.roles import BUILTIN as SYSTEM_ROLES  # 0006 vaqtidagi tizim rollari (keyin 0010 ularni oddiy rolga aylantiradi)
from apps.accounts.roles import PRESET_ROLES


def seed(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    for slug, (name, desc, perms, scoped) in SYSTEM_ROLES.items():
        Role.objects.update_or_create(slug=slug, defaults={'name': name, 'description': desc, 'permissions': perms, 'scoped': scoped, 'system': True})
    for slug, (name, desc, perms, scoped) in PRESET_ROLES.items():
        Role.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc, 'permissions': perms, 'scoped': scoped, 'system': False})


class Migration(migrations.Migration):
    dependencies = [('accounts', '0005_two_factor')]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=40, unique=True, verbose_name='Kalit')),
                ('name', models.CharField(max_length=120, verbose_name='Nomi')),
                ('description', models.CharField(blank=True, max_length=300, verbose_name='Izoh')),
                ('permissions', models.JSONField(blank=True, default=dict, verbose_name='Bo‘limlar bo‘yicha ruxsat')),
                ('scoped', models.BooleanField(default=False, verbose_name='Faqat o‘z fakulteti doirasida (User.scope)')),
                ('system', models.BooleanField(default=False, editable=False, verbose_name='Tizim roli')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Rol', 'verbose_name_plural': 'Rollar', 'ordering': ['-system', 'name']},
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(db_index=True, default='editor', max_length=40, verbose_name='Rol'),
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
