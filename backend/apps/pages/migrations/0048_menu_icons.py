"""Menyu belgilari: Universitet, Abituriyentlar, Faoliyat, Yangiliklar va Ta'lim yönalişlari sahifalariga mos belgi
(lucide nomlari). Faqat belgi hali böş sahifalar yangilanadi — admin qöygan belgiga tegilmaydi."""
from django.db import migrations

ICONS = {
    # Universitet
    'universitet-haqida': 'info', '/rektorat': 'users-round', 'tuzilma': 'network', 'bolimlar': 'layout-grid',
    '/fakultetlar-va-kafedralar': 'building-2', 'universitet-tarixi': 'history', '/staff': 'id-card',
    'universitet-talim-siyosati': 'book-marked', 'axborot-resurs-markazi': 'library',
    'yoshlar-ittifoqi-boshlangich-tashkiloti': 'users', 'oquv-binolari': 'school', 'mavjud-qulayliklar': 'armchair',
    'innovatsion-yechimlar': 'lightbulb', 'ozbekiston-xitoy-ii-talim-forumi-dasturi': 'messages-square',
    'ochiq-eshiklar-kunlari': 'door-open',
    # Abituriyentlar
    'nima-uchun-bu-universitet': 'sparkles', 'qoshma-talim-dasturlari': 'arrow-left-right', 'tolov-kontrakt-miqdori': 'wallet',
    'stipendiyalar': 'award', 'xalqaro-talabalar-va-oqituvchilar-uchun': 'globe', 'rektor-tabrigi': 'message-square-quote',
    'hamkorlarimiz': 'handshake', '/qabul': 'clipboard-check', 'magistrlik-dasturlari': 'graduation-cap',
    'phd-dasturlari': 'microscope', 'sharoitlar': 'house', 'vakansiya': 'briefcase', 'talim-grantlar-soni': 'badge-percent',
    # Faoliyat
    'korrupsiyaga-qarshi-kurashish': 'shield-check', 'yashil-universitet': 'leaf', 'madaniy-marifiy-faoliyat': 'palette',
    'universitet-bitiruvchilari-haqida': 'users-round', 'xalqaro-aloqalar': 'earth', 'moliyaviy-faoliyat': 'chart-pie',
    'ilmiy-faoliyat': 'flask-conical', 'oquv-uslubiy-hujjatlar': 'book-open-text', '/meyoriy-hujjatlar': 'scale',
    'xalqaro-akkreditatsiya': 'badge-check', 'kelajakka-qadam-markazi': 'footprints',
    # Yangiliklar
    '/yangiliklar?type=news': 'newspaper', '/yangiliklar?type=events': 'calendar-days', '/yangiliklar?type=announcements': 'megaphone',
    # Ta'lim yönalişlari
    '/bakalavriat': 'book-open', '/magistratura': 'graduation-cap',
}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    for key, icon in ICONS.items():
        qs = Page.objects.filter(url=key) if key.startswith('/') else Page.objects.filter(slug=key)
        qs.filter(icon='').update(icon=icon)
    Page.objects.filter(template='link', title__uz='Universitet nizomi', icon='').update(icon='scroll-text')


class Migration(migrations.Migration):
    dependencies = [('pages', '0047_video_icons')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
