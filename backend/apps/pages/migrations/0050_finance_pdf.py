"""«Moliyaviy faoliyat» sahifasiga eski saytdagi (uzswlu.uz/moliyaviy-faoliyat) hujjat qo'shiladi:
«Elektrotexnika sanoati mahsulotlari xaridi rejasi» (PDF, uchala tilda bir xil fayl).

Fayl: seed_data/files/finance/. Sahifada shu nomli hujjat bo'lsa yoki fayl topilmasa — o'tkazib yuboriladi.
"""
from pathlib import Path

from django.core.files import File
from django.db import migrations

from apps.core.alphabet import to_new_alphabet as N

SRC = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'finance' / 'elektrotexnika-xarid-rejasi.pdf'
TITLE = {
    'uz': N('Elektrotexnika sanoati mahsulotlari xaridi rejasi'),
    'ru': 'План закупки продукции электротехнической промышленности',
    'en': 'Procurement plan for electrical engineering products',
    'zh': '电工产品采购计划',
}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    page = Page.objects.filter(slug='moliyaviy-faoliyat').first()
    if not page or not SRC.exists():
        return
    if any((a.title or {}).get('uz') == TITLE['uz'] for a in PageAttachment.objects.filter(page=page)):
        return
    with SRC.open('rb') as fh:
        size = SRC.stat().st_size
        media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
        media.file.save('elektrotexnika-xarid-rejasi.pdf', File(fh, name='elektrotexnika-xarid-rejasi.pdf'), save=False)
        media.save()
    PageAttachment.objects.create(page=page, file=media, url='', title=TITLE, meta={}, order=1)


class Migration(migrations.Migration):
    dependencies = [('pages', '0049_contact_buttons')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
