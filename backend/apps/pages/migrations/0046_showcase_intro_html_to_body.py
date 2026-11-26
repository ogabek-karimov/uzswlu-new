"""Kartali blokning «Kirish gapi» — oddiy matn maydoni; eski saytdan import qilinganda unga HTML tushib qolgan
(«Kelajakka qadam» markazi: <h2>…</h2><p><strong>…) va saytda teglar bilan ko'rinardi. Shunday HTML sahifa matniga
— blok belgisi ([[kartalar-N]]) oldiga — ko'chiriladi, kirish gapi bo'shatiladi. Takror ishlatish xavfsiz."""
import re

from django.db import migrations

TAG = re.compile(r'<(?:h[1-6]|p|strong|b|em|ul|ol|li|br|div)\b', re.I)


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for page in Page.objects.exclude(showcase={}):
        sc = page.showcase or {}
        blocks = sc.get('blocks')
        if not isinstance(blocks, list):
            continue
        body = dict(page.body or {})
        changed = False
        for n, block in enumerate(blocks, start=1):
            intro = block.get('intro') if isinstance(block, dict) else None
            if not isinstance(intro, dict) or not any(TAG.search(str(v or '')) for v in intro.values()):
                continue
            marker = f'<p>[[kartalar-{n}]]</p>'
            for lang, html in intro.items():
                if not html:
                    continue
                text = body.get(lang) or ''
                body[lang] = text.replace(marker, html + marker, 1) if marker in text else html + text
            block['intro'] = {}
            changed = True
        if changed:
            page.body = body
            page.showcase = sc
            page.save(update_fields=['body', 'showcase'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0045_structure_pdfs')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
