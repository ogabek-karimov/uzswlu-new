"""Yoshlar ittifoqi: matn boshidagi qalin sarlavha («YOSHLAR ITTIFOQI … BOSHLANG'ICH TASHKILOTI») — markazda (4 tilda).
Faqat birinchi qator hali tekislanmagan <p><strong>…</strong></p> bo'lsa; admin muharririda ham «Markazga» bilan o'zgartiriladi."""
import re

from django.db import migrations

PAGE = 'yoshlar-ittifoqi-boshlangich-tashkiloti'
FIRST = re.compile(r'^\s*<p>(\s*<strong>)')


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug=PAGE).first()
    if not p or not p.body:
        return
    body = {k: FIRST.sub(r'<p style="text-align: center">\1', v, count=1) if isinstance(v, str) else v for k, v in p.body.items()}
    if body != p.body:
        p.body = body
        p.save(update_fields=['body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0019_page_showcase')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
