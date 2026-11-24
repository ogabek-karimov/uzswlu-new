"""«Magistrlik dasturlari» kartalari uçun 4 ta ichki sahifa (eski saytdagi ma'lumotlar bizning saytda): Eslatma (matn + havolalar),
Qabul nizomi (4 PDF), Qabul kvotasi (2 PDF), Qabul hujjatlari töplami (2 ta; Word — PDF'ga ögirilgan). Kartalar endi şularga olib boradi.
Fayllar: seed_data/files/applicants-master/. Nomlar 4 tilda."""
from pathlib import Path

from django.core.files import File
from django.db import migrations

FILES = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'applicants-master'
PARENT = 'magistrlik-dasturlari'


def T(uz, ru, en, zh):
    return {'uz': uz, 'ru': ru, 'en': en, 'zh': zh}


ESLATMA = T(
    '<p>Barça abituriyentlar savollari böyiça <a href="tel:+998712301373">+998 71 230 13 73</a> (Call center) telefon raqamiga murojaat qilişlari mumkin.</p>'
    '<p>5-iyundan boşlab abituriyentlar <a href="https://my.uzbmb.uz/" target="_blank" rel="noopener">my.uzbmb.uz</a> sayti orqali onlayn röyxatdan ötişlari mumkin.</p>'
    '<p>ÖzDJTU rasmiy Telegram kanali: <a href="https://t.me/UzSWLU" target="_blank" rel="noopener">t.me/UzSWLU</a></p>',
    '<p>По всем вопросам абитуриенты могут обращаться по телефону <a href="tel:+998712301373">+998 71 230 13 73</a> (Call center).</p>'
    '<p>С 5 июня абитуриенты могут пройти онлайн-регистрацию на сайте <a href="https://my.uzbmb.uz/" target="_blank" rel="noopener">my.uzbmb.uz</a>.</p>'
    '<p>Официальный Telegram-канал УзГУМЯ: <a href="https://t.me/UzSWLU" target="_blank" rel="noopener">t.me/UzSWLU</a></p>',
    '<p>Applicants may call <a href="tel:+998712301373">+998 71 230 13 73</a> (Call center) with any questions.</p>'
    '<p>From 5 June applicants can register online at <a href="https://my.uzbmb.uz/" target="_blank" rel="noopener">my.uzbmb.uz</a>.</p>'
    '<p>Official Telegram channel of UzSWLU: <a href="https://t.me/UzSWLU" target="_blank" rel="noopener">t.me/UzSWLU</a></p>',
    '<p>考生如有任何问题，可拨打 <a href="tel:+998712301373">+998 71 230 13 73</a>（呼叫中心）咨询。</p>'
    '<p>自6月5日起，考生可通过 <a href="https://my.uzbmb.uz/" target="_blank" rel="noopener">my.uzbmb.uz</a> 网站进行在线报名。</p>'
    '<p>乌兹别克斯坦国立世界语言大学官方 Telegram 频道：<a href="https://t.me/UzSWLU" target="_blank" rel="noopener">t.me/UzSWLU</a></p>',
)
EMPTY = T('', '', '', '')
PAGES = [
    ('magistratura-eslatma', T('Eslatma', 'Напоминание', 'Reminder', '提示'), ESLATMA, []),
    ('magistratura-qabul-nizomi', T('Qabul nizomi', 'Правила приёма', 'Admission regulations', '招生章程'), EMPTY, [
        ('17409896485897.pdf', T('Qabul nizomi', 'Положение о приёме', 'Admission regulations', '招生章程')),
        ('17416887692118.pdf', T('36-son qaror', 'Постановление № 36', 'Resolution No. 36', '第36号决议')),
        ('17416890262977.pdf', T('3515-son qaror', 'Постановление № 3515', 'Resolution No. 3515', '第3515号决议')),
        ('17416892180804.pdf', T('Bölim nizomi', 'Положение об отделе', 'Department regulations', '部门条例')),
    ]),
    ('magistratura-qabul-kvotasi', T('Qabul kvotasi', 'Квота приёма', 'Admission quota', '招生名额'), EMPTY, [
        ('17416886215249.pdf', T('Magistratura kvotasi — 2024', 'Квота магистратуры — 2024', 'Master’s quota — 2024', '硕士招生名额（2024）')),
        ('17416888293512.pdf', T('Magistratura kvotasi — 2023', 'Квота магистратуры — 2023', 'Master’s quota — 2023', '硕士招生名额（2023）')),
    ]),
    ('magistratura-qabul-hujjatlari', T('Qabul hujjatlari töplami', 'Пакет документов для поступления', 'Admission documents package', '入学申请材料'), EMPTY, [
        ('17416889003966.pdf', T('Qabul hujjatlari töplami', 'Пакет документов для поступления', 'Admission documents package', '入学申请材料')),
        ('17416889893485.pdf', T('Hujjatlar röyxati', 'Список документов', 'List of documents', '材料清单')),
    ]),
]


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    parent = Page.objects.filter(slug=PARENT).first()
    if not parent:
        return
    for order, (slug, title, body, docs) in enumerate(PAGES, start=1):
        if Page.objects.filter(slug=slug).exists():
            continue
        p = Page.objects.create(slug=slug, title=title, body=body, template='text', parent=parent, in_menu=False, order=order)
        for n, (fname, dtitle) in enumerate(docs, start=1):
            src = FILES / fname
            if not src.exists():
                continue
            with src.open('rb') as fh:
                size = src.stat().st_size
                m = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
                m.file.save(f'{slug}-{n}.pdf', File(fh, name=f'{slug}-{n}.pdf'), save=False)
                m.save()
            PageAttachment.objects.create(page=p, file=m, url='', title=dtitle, meta={}, display='embed', order=n)
    # Kartalar — endi bizning sahifalarga
    blocks = (parent.showcase or {}).get('blocks') or []
    for b in blocks:
        for c, (slug, *_r) in zip(b.get('cards') or [], PAGES):
            c['url'] = f'/{slug}'
    parent.save(update_fields=['showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0032_master_cards'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
