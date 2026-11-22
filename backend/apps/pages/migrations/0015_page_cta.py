"""Sahifa: matndan keyin animatsiyali chaqiruv bloki (sarlavha, matn, tugma, havola — 4 tilda).
«Axborot-resurs markazi» — uzlib.uz portaliga taklif (faqat blok hali bo'sh bo'lsa)."""
from django.db import migrations, models

import apps.core.fields

ARM = {
    'cta_title': {
        'uz': 'Kutubxona — bir bosiş masofasida',
        'ru': 'Библиотека — в одном клике',
        'en': 'The library is one click away',
        'zh': '图书馆，一键即达',
    },
    'cta_text': {
        'uz': 'Elektron katalog, darsliklar va ilmiy adabiyotlar uzlib.uz portalida kecha-kunduz oçiq. Kerakli kitobni uydan turib toping, öqing va bilimingizni bugunoq boyiting!',
        'ru': 'Электронный каталог, учебники и научная литература на портале uzlib.uz доступны круглосуточно. Находите и читайте нужные книги, не выходя из дома, — и пополняйте знания уже сегодня!',
        'en': 'The electronic catalogue, textbooks and academic literature are open around the clock on uzlib.uz. Find and read the books you need from anywhere — and start learning today!',
        'zh': '电子目录、教材和学术文献在 uzlib.uz 门户全天候开放。足不出户即可查找和阅读所需图书——今天就开始充实自己吧！',
    },
    'cta_label': {
        'uz': 'uzlib.uz ni oçiş',
        'ru': 'Открыть uzlib.uz',
        'en': 'Open uzlib.uz',
        'zh': '访问 uzlib.uz',
    },
}


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='axborot-resurs-markazi').first()
    if p and not p.cta_url:
        for field, value in ARM.items():
            setattr(p, field, value)
        p.cta_url = 'https://uzlib.uz/'
        p.save(update_fields=[*ARM, 'cta_url'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0014_page_staff_contacts')]
    operations = [
        migrations.AddField('page', 'cta_title', apps.core.fields.I18nField(verbose_name='Chaqiruv bloki: sarlavha')),
        migrations.AddField('page', 'cta_text', apps.core.fields.I18nField(multiline=True, verbose_name='Chaqiruv bloki: matn')),
        migrations.AddField('page', 'cta_label', apps.core.fields.I18nField(verbose_name='Chaqiruv bloki: tugma yozuvi')),
        migrations.AddField('page', 'cta_url', models.CharField(
            'Chaqiruv bloki: havola', max_length=500, blank=True,
            help_text='Matndan keyin animatsiyali blok; havola va tugma yozuvi bo‘lsa ko‘rinadi')),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
