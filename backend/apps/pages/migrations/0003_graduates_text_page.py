"""«Universitet bitiruvchilari haqida» — PDF havola o'rniga matnli sahifa (mavjud bazalar uchun).

Boshlang'ich ma'lumot (`pages-seed.json`) faqat bo'sh bazaga yuklanadi, shuning uchun avval o'rnatilgan bazalarda
bu menyu bandi hamon PDF'ga olib borardi. Migratsiya uni matnli sahifaga aylantiradi (manzil
`/universitet-bitiruvchilari-haqida`, infografika rasmi `frontend/public/images/pages/bitiruvchilar.webp`).
Faqat PDF-havola holatida ishlaydi: admin panelda allaqachon o'zgartirilgan bo'lsa, tegmaydi.
"""
from django.db import migrations

SLUG = 'universitet-bitiruvchilari-haqida'

LEAD = {
    "uz": "Universitetimiz bitiruvçilari orasida davlat arboblari, diplomatlar, oliy ta’lim muassasalari rahbarlari, olimlar va sport şarhlovçilari bor.",
    "ru": "Среди выпускников университета — государственные деятели, дипломаты, руководители вузов, учёные и спортивные комментаторы.",
    "en": "Our graduates include statesmen, diplomats, university leaders, scholars and sports commentators.",
    "zh": "我校毕业生中有国务活动家、外交官、高校领导、学者和体育评论员。"
}

BODY = {
    "uz": "<figure><img src=\"/images/pages/bitiruvchilar.webp\" alt=\"ÖzDJTU bitiruvçilari haqida ma’lumot: 14 nafar bitiruvçining surati, ismi va lavozimi\" width=\"2400\" height=\"1350\"><figcaption>Kattalaştiriş uçun rasm ustiga bosing.</figcaption></figure>",
    "ru": "<figure><img src=\"/images/pages/bitiruvchilar.webp\" alt=\"Информация о выпускниках УзГУМЯ: фотографии, имена и должности 14 выпускников\" width=\"2400\" height=\"1350\"><figcaption>Нажмите на изображение, чтобы увеличить.</figcaption></figure>",
    "en": "<figure><img src=\"/images/pages/bitiruvchilar.webp\" alt=\"Information about UzSWLU graduates: photos, names and positions of 14 graduates\" width=\"2400\" height=\"1350\"><figcaption>Click the image to enlarge.</figcaption></figure>",
    "zh": "<figure><img src=\"/images/pages/bitiruvchilar.webp\" alt=\"乌兹别克斯坦国立世界语言大学毕业生信息：14位毕业生的照片、姓名和职务\" width=\"2400\" height=\"1350\"><figcaption>点击图片可放大。</figcaption></figure>"
}


def to_text_page(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    if Page.objects.filter(slug=SLUG).exists():
        return
    page = Page.objects.filter(template='link', title__uz='Universitet bitiruvchilari haqida').first()
    if page is None:
        return
    page.template, page.slug, page.url, page.file = 'text', SLUG, '', None
    page.lead, page.body = LEAD, BODY
    page.save()


class Migration(migrations.Migration):
    dependencies = [('pages', '0002_remove_toshkent_kontingent')]
    operations = [migrations.RunPython(to_text_page, migrations.RunPython.noop)]
