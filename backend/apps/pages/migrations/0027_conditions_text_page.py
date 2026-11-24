"""«Sharoitlar» (Abituriyentlar): «Havola / PDF» edi — menyudan eski saytdagi PDF'ga olib borardi. Endi matnli sahifa
(/sharoitlar): admin «PDF hujjatlar»ga PDF yuklaydi va «Ichi ko'rinadi» tanlaydi — PDF sayt ichida varaqlanadi.
Faqat sahifa hali eski saytdagi havola bo'lsa."""
from django.db import migrations

OLD_URL = 'https://uzswlu.uz/backend/web/uploads/pagepdf/icon/17437679069420.pdf'


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(template='link', url=OLD_URL).first()
    if not p:
        return
    slug = 'sharoitlar'
    if Page.objects.filter(slug=slug).exclude(pk=p.pk).exists():
        slug = f'sharoitlar-{p.pk}'
    p.template, p.slug, p.url, p.file_id = 'text', slug, '', None
    p.save(update_fields=['template', 'slug', 'url', 'file', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0026_applicants_overview')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
