"""«Bitiruvchilar klubi» (Abituriyentlar) menyudan olib tashlanadi — «Universitet bitiruvchilari haqida» (Faoliyat) bilan bir xil mavzu.
Sahifa o'chirilmaydi: menyudan va saytdan yashiriladi (admin → Sahifalar'da qayta yoqish mumkin)."""
from django.db import migrations


def hide(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Page.objects.filter(slug='bitiruvchilar-klubi').update(in_menu=False, published=False)


def show(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    Page.objects.filter(slug='bitiruvchilar-klubi').update(in_menu=True, published=True)


class Migration(migrations.Migration):
    dependencies = [('pages', '0004_admission_url')]
    operations = [migrations.RunPython(hide, show)]
