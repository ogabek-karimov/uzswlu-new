from django.db import migrations, models

from apps.accounts.roles import BUILTIN


def convert(apps, schema_editor):
    """Tayyor rollar (editor, pages, sdg) oddiy rolga aylanadi: bo'limlari bazada, superadmin tahrirlaydi yoki o'chiradi;
    boshlang'ich bo'limlari kodning hozirgi tayyor holatiga tenglanadi (0006 dan keyin kodga qo'shilganlar ham kirsin).
    Fakultet admini va Dekan o'chiriladi (foydalanuvchisi bor bo'lsa — oddiy rol sifatida qoladi)."""
    Role = apps.get_model('accounts', 'Role')
    User = apps.get_model('accounts', 'User')
    for slug in ('editor', 'pages', 'sdg'):
        Role.objects.filter(slug=slug).update(system=False, permissions=BUILTIN[slug][2])
    Role.objects.filter(slug='editor').update(edit_all=True)  # kontent muharriri hamma postni boshqaradi (avvalgidek)
    for slug in ('faculty', 'dekan'):
        if User.objects.filter(role=slug).exists():
            Role.objects.filter(slug=slug).update(system=False)
        else:
            Role.objects.filter(slug=slug).delete()


class Migration(migrations.Migration):
    dependencies = [('accounts', '0009_drop_preset_roles')]
    operations = [
        migrations.AddField(
            model_name='role',
            name='edit_all',
            field=models.BooleanField(default=False, verbose_name='Boshqalarning postlarini ham tahrirlaydi'),
        ),
        migrations.RunPython(convert, migrations.RunPython.noop),
    ]
