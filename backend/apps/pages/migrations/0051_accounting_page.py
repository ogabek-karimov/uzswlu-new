"""«Hisob-kitob bo'limi» sahifasi eski saytdan (uzswlu.uz/accounting) to'ldiriladi: kirish matni (4 tilda) va
PF-6247-son Farmon nazorat-rejasi bo'yicha hisobotlar (PDF).

Eski sahifadagi 15 ta havoladan faqat 2 tasi ishlaydi (5-band va 9-band hisobotlari); qolganlari eski saytning
o'zida ham, Web Archive'da ham 404 — ular ko'chirilmadi. Fayllar: seed_data/files/finance/accounting/.
Matn faqat bo'sh bo'lsa yoziladi; hujjat sahifada shu nomli hujjat bo'lmasa qo'shiladi.
"""
from pathlib import Path

from django.core.files import File
from django.db import migrations

from apps.core.alphabet import to_new_alphabet as N

FILES = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'finance' / 'accounting'
BODY = {
    'uz': N('<h2>PF-6247-son Farmon ijrosi yuzasidan hisobotlar</h2>'
            '<p>O‘zbekiston Respublikasi Prezidentining 2021-yil 16-iyundagi PF-6247-son Farmoni Nazorat-rejasi bandlari '
            'ijrosi yuzasidan universitet hisob-kitob bo‘limi tayyorlagan hisobotlar. Hujjatni tanlang — u shu sahifaning '
            'o‘zida ochiladi yoki yuklab olinadi.</p>'),
    'ru': ('<h2>Отчёты об исполнении Указа УП-6247</h2>'
           '<p>Отчёты бухгалтерии университета об исполнении пунктов Плана контроля по Указу Президента Республики '
           'Узбекистан от 16 июня 2021 года № УП-6247. Выберите документ — он откроется на этой странице или будет скачан.</p>'),
    'en': ('<h2>Reports on the implementation of Decree PF-6247</h2>'
           '<p>Reports of the university accounting department on the implementation of the Control Plan of the Decree of '
           'the President of the Republic of Uzbekistan No. PF-6247 of 16 June 2021. Choose a document to open or download it.</p>'),
    'zh': ('<h2>第PF-6247号总统令执行情况报告</h2>'
           '<p>大学会计部关于执行乌兹别克斯坦共和国总统2021年6月16日第PF-6247号令监督计划各项条款的报告。'
           '选择文件即可在本页打开或下载。</p>'),
}
META = {'uz': N('PF-6247 · 2023-yil'), 'ru': 'УП-6247 · 2023 г.', 'en': 'PF-6247 · 2023', 'zh': 'PF-6247 · 2023年'}
DOCS = [
    ('5-band-xorijiy-safarlar.pdf', {
        'uz': N('5-band. Xorijiy safarlar'), 'ru': 'Пункт 5. Зарубежные командировки',
        'en': 'Clause 5. Foreign business trips', 'zh': '第5项：出国公务'}),
    ('9-band-xizmat-avto-va-uylar.pdf', {
        'uz': N('9-band. Xizmat avtomobillari va uylari'), 'ru': 'Пункт 9. Служебные автомобили и жильё',
        'en': 'Clause 9. Official vehicles and housing', 'zh': '第9项：公务用车与住房'}),
]


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    page = Page.objects.filter(slug='xisob-kitob-bolimi').first()
    if not page:
        return
    if not any((v or '').strip() for v in (page.body or {}).values()):
        page.body = BODY
        page.save(update_fields=['body'])
    have = {(a.title or {}).get('uz') for a in PageAttachment.objects.filter(page=page)}
    for n, (name, title) in enumerate(DOCS, start=1):
        src = FILES / name
        if title['uz'] in have or not src.exists():
            continue
        with src.open('rb') as fh:
            size = src.stat().st_size
            media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
            media.file.save(name, File(fh, name=name), save=False)
            media.save()
        PageAttachment.objects.create(page=page, file=media, url='', title=title, meta=META, order=n)


class Migration(migrations.Migration):
    dependencies = [('pages', '0050_finance_pdf')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
