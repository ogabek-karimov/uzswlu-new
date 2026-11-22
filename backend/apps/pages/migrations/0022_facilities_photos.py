"""«Mavjud qulayliklar»: eski saytdagi buklet rasmlaridan kesib olingan suratlar (matn qismisiz) — o'z bo'limlariga:
yashash muddati va to'lov (xona, zal), ovqatlanish (oshxona binosi + 3), sport (maydon + 3; yangi 7-blok, Sport matnidan keyin),
axborot-resurs markazi (bino + 6). Fayllar: seed_data/files/facilities/. Faqat bloklarda hali surat bo'lmasa."""
import re
from pathlib import Path

from django.core.files import File
from django.db import migrations

FILES = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'facilities'
PAGE = 'mavjud-qulayliklar'


def T(uz, ru, en, zh):
    return {'uz': uz, 'ru': ru, 'en': en, 'zh': zh}


ROOM = T('Talabalar turar joyidagi xona', 'Комната в студенческом общежитии', 'A room in the student residence hall', '学生宿舍房间')
HALL = T('Talabalar turar joyidagi umumiy zal', 'Общий зал студенческого общежития', 'Common hall of the residence', '宿舍公共大厅')
CAFE = T('Kampusdagi oşxona', 'Столовая в кампусе', 'Campus cafeteria', '校园食堂')
SPORT = T('Talabalar sporti', 'Студенческий спорт', 'Student sports', '学生体育')
ARM = T('Axborot-resurs markazi', 'Информационно-ресурсный центр', 'Information Resource Center', '信息资源中心')
# blok raqami (1 dan) → suratlar (fayl, tavsif)
PHOTOS = {
    4: [('turar-joy-xona', ROOM), ('turar-joy-zal', HALL)],
    5: [('oshxona-bino', T('Oşxona binosi', 'Здание столовой', 'Cafeteria building', '食堂大楼')),
        ('oshxona-1', CAFE), ('oshxona-2', CAFE), ('oshxona-3', CAFE)],
    7: [('sport-maydon', T('Futbol maydoni', 'Футбольное поле', 'Football pitch', '足球场')),
        ('sport-1', SPORT), ('sport-2', SPORT), ('sport-3', SPORT)],
    6: [('arm-bino', T('Axborot-resurs markazi binosi', 'Здание информационно-ресурсного центра', 'Information Resource Center building', '信息资源中心大楼')),
        *[(f'arm-{i}', ARM) for i in range(1, 7)]],
}
# Sport bo'limi matnidan keyin (keyingi sarlavhadan oldin) 7-blok belgisi
NEXT_H2 = {'uz': 'Axborot-resurs markazi', 'ru': 'Информационно-ресурсный центр', 'en': 'Information Resource Center', 'zh': '信息资源中心'}


def _media(name: str, alt: dict):
    # Haqiqiy model: rasm admin yuklagandagi kabi WebP'ga o'giriladi, kichik nusxalari yaratiladi
    from apps.core.models import Media
    path = FILES / f'{name}.jpg'
    if not path.exists():
        return None
    with path.open('rb') as fh:
        m = Media(folder='posts', alt=alt, file=File(fh, name=path.name))
        m.save()
    return m.pk


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug=PAGE).first()
    if not p or not isinstance(p.showcase, dict) or not isinstance(p.showcase.get('blocks'), list):
        return
    blocks = p.showcase['blocks']
    if len(blocks) < 6 or any(isinstance(b, dict) and b.get('photos') for b in blocks):
        return
    while len(blocks) < 7:
        blocks.append({'intro': {}, 'stats': {}, 'columns': [], 'outro': {}})
    for n, items in PHOTOS.items():
        blocks[n - 1]['photos'] = [pk for pk in (_media(name, alt) for name, alt in items) if pk]
    body = dict(p.body or {})
    for lang, title in NEXT_H2.items():
        html = body.get(lang) or ''
        if '[[kartalar-7]]' in html:
            continue
        html, count = re.subn(rf'(<h2>\s*{re.escape(title)}\s*</h2>)', r'<p>[[kartalar-7]]</p>\1', html, count=1)
        body[lang] = html
    p.showcase = {**p.showcase, 'blocks': blocks}
    p.body = body
    p.save(update_fields=['showcase', 'body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0021_facilities_text'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
