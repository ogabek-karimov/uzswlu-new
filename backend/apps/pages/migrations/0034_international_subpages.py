"""«Xalqaro talabalar va o'qituvchilar uchun» kartalari uchun 8 ta ichki sahifa (eski saytdagi ma'lumotlar bizning saytda, 4 tilda):
Bakalavriat / Magistratura yo'nalishlari, Doktorantura, Mustaqil izlanuvchi, Qabul shartlari, Viza, Summer camp (fakultet kartalari),
Til o'qitish markazi (2 PDF). Kartalar endi shularga olib boradi; «Ariza shakli» (fayl yuklanadigan forma) — hozircha eski saytda.
Ma'lumot: seed_data/international_pages.json, fayllar: seed_data/files/applicants-intl/."""
import json
from pathlib import Path

from django.core.files import File
from django.db import migrations

DATA = Path(__file__).resolve().parents[3] / 'seed_data'
FILES = DATA / 'files' / 'applicants-intl'
PARENT = 'xalqaro-talabalar-va-oqituvchilar-uchun'
# Karta (tartib raqami) → yangi sahifa
CARD_SLUG = {1: 'xalqaro-bakalavriat', 2: 'xalqaro-magistratura', 3: 'xalqaro-doktorantura', 4: 'xalqaro-mustaqil-izlanuvchi',
             5: 'xalqaro-qabul-shartlari', 7: 'viza-va-royxatga-olish', 8: 'summer-camp', 9: 'til-oqitish-markazi'}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    parent = Page.objects.filter(slug=PARENT).first()
    path = DATA / 'international_pages.json'
    if not parent or not path.exists():
        return
    for order, spec in enumerate(json.loads(path.read_text(encoding='utf-8')), start=1):
        slug = spec['slug']
        if Page.objects.filter(slug=slug).exists():
            continue
        p = Page.objects.create(slug=slug, title=spec['title'], body=spec['body'], showcase={'blocks': spec['showcase']},
                                template='text', parent=parent, in_menu=False, order=order)
        for n, (fname, title) in enumerate(spec.get('docs') or [], start=1):
            src = FILES / fname
            if not src.exists():
                continue
            with src.open('rb') as fh:
                size = src.stat().st_size
                m = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                m.file.save(f'{slug}-{n}.pdf', File(fh, name=f'{slug}-{n}.pdf'), save=False)
                m.save()
            PageAttachment.objects.create(page=p, file=m, url='', title=title, meta={}, display='embed', order=n)
    for b in (parent.showcase or {}).get('blocks') or []:
        for i, c in enumerate(b.get('cards') or []):
            if i in CARD_SLUG and Page.objects.filter(slug=CARD_SLUG[i]).exists():
                c['url'] = f'/{CARD_SLUG[i]}'
    parent.save(update_fields=['showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0033_master_subpages'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
