from django.db import migrations


def keep_auto_accounts(apps, schema_editor):
    """«HEMIS roli» (lavozim bo'yicha avtomatik rol) olib tashlanadi: rolni faqat admin beradi (Foydalanuvchilar → rol + HEMIS ID).
    Avval avtomatik yaratilgan hisoblar o'chirilmaydi — oddiy (admin bergan) hisobga aylanadi, roli va holati saqlanadi;
    keragini admin Foydalanuvchilar sahifasida yopadi yoki o'chiradi."""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(hemis_auto=True).update(hemis_auto=False)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0010_roles_editable')]
    operations = [
        migrations.RunPython(keep_auto_accounts, migrations.RunPython.noop),
        migrations.RemoveField(model_name='role', name='hemis_role'),
        migrations.RemoveField(model_name='user', name='hemis_auto'),
    ]
