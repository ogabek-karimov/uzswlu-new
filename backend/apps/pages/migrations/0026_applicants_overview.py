"""«Abituriyentlar» menyu bo'limining «Bo'lim sahifasi» tugmasi Qabul sahifasiga (/qabul) olib borardi. Endi — Universitet
bo'limidagi kabi matnli sahifa: «Nima uchun bu universitet» (chapda bo'lim sahifalari ro'yxati bilan).
Faqat havola hali Qabul (yoki oraliq /bolim/abituriyentlar) bo'lsa — admin boshqasini qo'ygan bo'lsa tegilmaydi."""
from django.db import migrations

TARGET = '/nima-uchun-bu-universitet'
OLD = ['/qabul', '/qabul-20262027', '/bolim/abituriyentlar']


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    if not Page.objects.filter(slug=TARGET.strip('/')).exists():
        return
    for g in Page.objects.filter(template='group', overview__in=OLD):
        title = g.title or {}
        if g.group_key == 'applicants' or 'abituriyent' in title.get('uz', '').lower() or title.get('en', '').lower().startswith(('applicant', 'admission')):
            g.overview = TARGET
            g.save(update_fields=['overview'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0025_open_days_text')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
