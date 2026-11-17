"""«Tezkor xizmatlar»: avvalgi 6 ta qat'iy karta bazaga ko'chiriladi; AKT lug'ati havolasi (Aloqa'da kiritilgan bo'lsa) alohida karta bo'ladi."""
from django.db import migrations

SEED = [
    {
        "icon": "lucide:message-square-text",
        "url": "/site/reception",
        "title": {
            "uz": "Virtual qabulxona",
            "ru": "Виртуальная приёмная",
            "en": "Virtual reception",
            "zh": "网上接待室"
        },
        "text": {
            "uz": "Rektorga murojaat yuboriş",
            "ru": "Обращение к ректору",
            "en": "Send an appeal to the rector",
            "zh": "向校长提交申请"
        },
        "order": 0
    },
    {
        "icon": "lucide:graduation-cap",
        "url": "https://student.uzswlu.uz",
        "title": {
            "uz": "Talaba portali",
            "ru": "Портал студента",
            "en": "Student portal",
            "zh": "学生门户"
        },
        "text": {
            "uz": "Baholar, jadval, davomat",
            "ru": "Оценки, расписание, посещаемость",
            "en": "Grades, schedule, attendance",
            "zh": "成绩、课表、考勤"
        },
        "order": 1
    },
    {
        "icon": "lucide:database",
        "url": "https://hemis.uzswlu.uz",
        "title": {
            "uz": "HEMIS",
            "ru": "HEMIS",
            "en": "HEMIS",
            "zh": "HEMIS"
        },
        "text": {
            "uz": "Oliy ta’lim axborot tizimi",
            "ru": "Информационная система высшего образования",
            "en": "Higher education information system",
            "zh": "高等教育信息系统"
        },
        "order": 2
    },
    {
        "icon": "lucide:mail",
        "url": "/services/mail",
        "title": {
            "uz": "Korporativ poçta",
            "ru": "Корпоративная почта",
            "en": "Corporate mail",
            "zh": "企业邮箱"
        },
        "text": {
            "uz": "Xodimlar uçun e-poçta",
            "ru": "Почта для сотрудников",
            "en": "Email for staff",
            "zh": "教职工电子邮箱"
        },
        "order": 3
    },
    {
        "icon": "lucide:briefcase-business",
        "url": "/career",
        "title": {
            "uz": "Karyera markazi",
            "ru": "Центр карьеры",
            "en": "Career centre",
            "zh": "就业中心"
        },
        "text": {
            "uz": "Amaliyot va iş örinlari",
            "ru": "Практика и вакансии",
            "en": "Internships and jobs",
            "zh": "实习与就业"
        },
        "order": 4
    },
    {
        "icon": "lucide:sprout",
        "url": "/sdg-report",
        "title": {
            "uz": "BRM",
            "ru": "ЦУР",
            "en": "SDG",
            "zh": "SDG"
        },
        "text": {
            "uz": "Barqaror rivojlaniş maqsadlari",
            "ru": "Цели устойчивого развития",
            "en": "Sustainable Development Goals",
            "zh": "可持续发展目标"
        },
        "order": 5
    }
]

GLOSSARY = {
    "icon": "lucide:book-a",
    "title": {
        "uz": "AKT izohli luğati",
        "ru": "Толковый словарь ИКТ",
        "en": "ICT glossary",
        "zh": "信息通信技术词典"
    },
    "text": {
        "uz": "Mobil ilova",
        "ru": "Мобильное приложение",
        "en": "Mobile app",
        "zh": "移动应用"
    },
    "order": 6
}


def seed(apps, schema_editor):
    QuickLink = apps.get_model('content', 'QuickLink')
    if QuickLink.objects.exists():
        return
    SiteSettings = apps.get_model('core', 'SiteSettings')
    for row in SEED:
        QuickLink.objects.create(**row)
    s = SiteSettings.objects.first()
    url = (getattr(s, 'glossary_app_url', '') or '').strip() if s else ''
    if url:
        QuickLink.objects.create(url=url, **GLOSSARY)


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0005_quick_link'),
        ('core', '0003_sitesettings_glossary_app_url'),
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
