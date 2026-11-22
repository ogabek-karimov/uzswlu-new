"""«Universitet tarixi» va «Universitet ta'lim siyosati» o'zbekcha matni — yangi alifboda (qonun bo'yicha):
Oʻ→Ö, Gʻ→Ğ, Sh→Ş, Ch→Ç; tutuq (ʼ) va boshqa harflar o'zgarmaydi. HTML teglarga tegilmaydi; takror ishlatilsa ham xavfsiz."""
import re

from django.db import migrations

SLUGS = ('universitet-tarixi', 'universitet-talim-siyosati')
APOS = "[\u2018\u02bb'\u2019`\u02bc]"
RULES = [
    (re.compile('O' + APOS), 'Ö'), (re.compile('o' + APOS), 'ö'),
    (re.compile('G' + APOS), 'Ğ'), (re.compile('g' + APOS), 'ğ'),
    (re.compile('SH'), 'Ş'), (re.compile('Sh'), 'Ş'), (re.compile('sh'), 'ş'),
    (re.compile('CH'), 'Ç'), (re.compile('Ch'), 'Ç'), (re.compile('ch'), 'ç'),
]


def convert(html: str) -> str:
    def text(chunk: str) -> str:
        for rx, rep in RULES:
            chunk = rx.sub(rep, chunk)
        return chunk
    return ''.join(part if part.startswith('<') else text(part) for part in re.split(r'(<[^>]+>)', html))


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for p in Page.objects.filter(slug__in=SLUGS):
        body = dict(p.body or {})
        if body.get('uz'):
            body['uz'] = convert(body['uz'])
            p.body = body
            p.save(update_fields=['body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0010_zh_history_policy')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
