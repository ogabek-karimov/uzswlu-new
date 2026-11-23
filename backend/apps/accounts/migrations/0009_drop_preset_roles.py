from django.db import migrations

PRESETS = ('rektor', 'dekan', 'kafedra-mudiri', 'oqituvchi')


def drop(apps, schema_editor):
    """Tayyor maxsus rollar (Rektor, Dekan, Kafedra mudiri, O'qituvchi) endi kerak emas: admin panelda tizim rollari qoladi.
    Foydalanuvchisi bor rol o'chirilmaydi (foydalanuvchi rolsiz qolmasin); superadmin yangi rolni «Yangi rol» orqali yaratadi."""
    Role = apps.get_model('accounts', 'Role')
    User = apps.get_model('accounts', 'User')
    for slug in PRESETS:
        if not User.objects.filter(role=slug).exists():
            Role.objects.filter(slug=slug, system=False).delete()


class Migration(migrations.Migration):
    dependencies = [('accounts', '0008_hemis_role')]
    operations = [migrations.RunPython(drop, migrations.RunPython.noop)]
