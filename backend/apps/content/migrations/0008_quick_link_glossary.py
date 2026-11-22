"""«Tezkor xizmatlar»: HEMIS kartasiga globus ikonkasi; AKT izohli lug'ati kartasi (eski saytdagidek, Play Market ilovasi).
0006 da u faqat Sozlamalar → Aloqa'da havola kiritilgan bo'lsa yaratilardi — havola bo'lmagan bazalarda karta yo'qolib qolgan.
Shu havolali yoki «AKT» nomli karta bo'lsa — yangisi qo'shilmaydi, faqat kitob ikonkasi ilova logosiga almashadi."""
from django.db import migrations

ICON = 'app:akt-lugat'   # ilova logosi (frontend public/images/quick/akt-lugat.webp)
URL = 'https://play.google.com/store/apps/details?id=uz.soft.aktlugat23'
TITLE = {'uz': 'AKT izohli luğati', 'ru': 'Толковый словарь ИКТ', 'en': 'ICT glossary', 'zh': '信息通信技术词典'}
TEXT = {'uz': 'Mobil ilova', 'ru': 'Мобильное приложение', 'en': 'Mobile app', 'zh': '移动应用'}


def add(apps, schema_editor):
    QuickLink = apps.get_model('content', 'QuickLink')
    # HEMIS kartasi: ma'lumotlar bazasi ikonkasi → globus (faqat standart ikonka bo'lsa)
    QuickLink.objects.filter(url__icontains='hemis', icon='lucide:database').update(icon='lucide:globe')
    existing = [q for q in QuickLink.objects.all() if 'aktlugat' in q.url or 'AKT' in (q.title or {}).get('uz', '')]
    if existing:
        # Bor kartaga faqat standart kitob ikonkasi bo'lsa — ilova logosi qo'yiladi; boshqa narsaga tegilmaydi
        for q in existing:
            if q.icon == 'lucide:book-a':
                q.icon = ICON
                q.save(update_fields=['icon'])
        return
    last = QuickLink.objects.order_by('-order').first()
    QuickLink.objects.create(icon=ICON, url=URL, title=TITLE, text=TEXT, order=(last.order + 1) if last else 0, visible=True)


class Migration(migrations.Migration):
    dependencies = [('content', '0007_quick_link_inner_pages')]
    operations = [migrations.RunPython(add, migrations.RunPython.noop)]
