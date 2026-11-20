from django.db import migrations, models
import django.db.models.deletion

# Hozirgi binolarning fakultetlari (avval frontendda qattiq yozilgan edi)
LINKS = {'philology': 'english-philology', 'journalism': 'international-journalism', 'russian': 'russian-philology'}


def link(apps, schema_editor):
    Campus, Faculty = apps.get_model('structure', 'Campus'), apps.get_model('structure', 'Faculty')
    for key, slug in LINKS.items():
        f = Faculty.objects.filter(slug=slug).first()
        if f:
            Campus.objects.filter(key=key, faculty__isnull=True).update(faculty=f)


class Migration(migrations.Migration):

    dependencies = [
        ('structure', '0004_campus_email_coords'),
    ]

    operations = [
        migrations.AddField(
            model_name='campus',
            name='faculty',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='structure.faculty', verbose_name='Fakultet (logo uchun)'),
        ),
        migrations.RunPython(link, migrations.RunPython.noop),
    ]
