"""Ikki sahifadagi aloqa ma'lumotlari tugmalar qatoriga keltiriladi (sayt faqat havolalardan iborat abzatsni
tugma ko'rinishida chiqaradi — `builders_site.link_buttons`).

* «Korrupsiyaga qarshi kurashish»: «Ishchi tel: +99871-230-13-42» va «Telegram» qatorlari → telefon (tel:) va
  Telegram tugmalari.
* «Xalqaro aloqalar»: boshidagi ikki havola (matn ichida, manzili bilan) → «Ariza topshirish» va «Study in Uzbekistan»
  tugmalari; oxiridagi «Telefon / Telegram / Email» matni → bosiladigan tugmalar (telefondagi xato: +998761 → +99871).
  Xitoycha matn boshidagi tarjimon izohi («Here’s the translation…») olib tashlanadi.

Matn kutilgan ko'rinishda bo'lmasa (admin'da o'zgartirilgan) — tegilmaydi.
"""
import re

from django.db import migrations

from apps.core.alphabet import to_new_alphabet as N

BLANK = 'target="_blank" rel="noopener"'

# --- Korrupsiyaga qarshi kurashish ---
ANTI_TG = 'https://t.me/uzdjtu_antikorrupsiya'
ANTI = re.compile(
    r'<p><strong>([^<]{2,24}):</strong></p>\s*'
    r'<p><strong>[^<]{2,30}:</strong>\s*\+?[\d\s()-]{9,}</p>\s*'
    r'<p>(?:<strong>)?<a href="https://t\.me/uzdjtu_antikorrupsiya"[^>]*>(?:<strong>)?[^<]*(?:</strong>)?</a>(?:</strong>)?</p>'
)
ANTI_ROW = (f'<p><a href="tel:+998712301342">+998 71 230-13-42</a> '
            f'<a href="{ANTI_TG}" {BLANK}>Telegram</a></p>')

# --- Xalqaro aloqalar ---
STUDY = 'https://studyin-uzbekistan.uz/universities/35/'
TOP = re.compile(r'(<p>\s*|<br>\s*|\s*)<a href="[^"]+"[^>]*>[^<]*</a>\s*(?:va|и|and|和)\s*'
                 r'<a href="https://studyin-uzbekistan\.uz/universities/35/"[^>]*>[^<]*</a>(?=\s*</p>)')
APPLY = {'uz': N('Ariza topshirish'), 'ru': 'Подать заявку', 'en': 'Application form', 'zh': '提交申请'}
CONTACT = re.compile(r'(<br>\s*|<p>)\s*([^<>]{5,90}?[:：])\s*<br>\s*(?:Телефон|Phone|电话)[\s\S]*?international@uzswlu\.uz</p>')
CONTACT_ROW = ('<p><a href="tel:+998712301289">+998 71 230-12-89</a> '
               f'<a href="https://t.me/+998974490967" {BLANK}>+998 97 449-09-67</a> '
               f'<a href="https://t.me/+998901853804" {BLANK}>+998 90 185-38-04</a> '
               '<a href="mailto:international@uzswlu.uz">international@uzswlu.uz</a></p>')
ZH_NOTE = re.compile(r'^\s*<p>Here[’\']s the translation[^<]*</p>\s*')


def _anti(html, lang):
    return ANTI.sub(lambda m: f'<p><strong>{m.group(1)}:</strong></p>{ANTI_ROW}', html, count=1)


def _intl(html, lang):
    if lang == 'zh':
        html = ZH_NOTE.sub('', html, count=1)
    row = (f'<p><a href="/ariza-shakli">{APPLY.get(lang, APPLY["en"])}</a> '
           f'<a href="{STUDY}" {BLANK}>Study in Uzbekistan</a></p>')
    # abzatsning yopuvchi </p> si joyida qoladi
    html = TOP.sub(lambda m: ('' if m.group(1).startswith('<p>') else '</p>') + row[:-4], html, count=1)

    def contact(m):
        intro = m.group(2).strip().replace('bilanboğlaning', 'bilan boğlaning')
        return ('' if m.group(1).startswith('<p>') else '</p>') + f'<p><strong>{intro}</strong></p>{CONTACT_ROW}'
    return CONTACT.sub(contact, html, count=1)


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for slug, fix in (('korrupsiyaga-qarshi-kurashish', _anti), ('xalqaro-aloqalar', _intl)):
        page = Page.objects.filter(slug=slug).first()
        if not page:
            continue
        body = {lang: (fix(html, lang) if html else html) for lang, html in (page.body or {}).items()}
        if body != page.body:
            page.body = body
            page.save(update_fields=['body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0048_menu_icons')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
