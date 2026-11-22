"""«Yoshlar ittifoqi boshlang'ich tashkiloti»: eski saytdagi matn uz/ru/en (uz — yangi alifboda), xitoychasi — tarjima;
ish vaqti (xodimlar kartasida) va Telegram kanaliga chaqiruv bloki. Faqat hali bo'sh/namunaviy bo'lsa yoziladi.
Xodimlar: admin → Sahifalar → «Sahifadagi xodimlar» (HEMIS bo'limi yoki zaxira)."""
import json
from pathlib import Path

from django.db import migrations

SEED = Path(__file__).resolve().parents[3] / 'seed_data' / 'youth_union_page.json'
PLACEHOLDER = ('namunaviy', 'примерный', 'sample text', '示例')
HOURS = {
    'uz': 'Iş vaqti: 09:00–18:00',
    'ru': 'Рабочее время: 09:00–18:00',
    'en': 'Working hours: 9:00 a.m. – 6:00 p.m.',
    'zh': '工作时间：09:00–18:00',
}
CTA = {
    'cta_title': {
        'uz': 'Faol yoşlar safiga qöşiling!',
        'ru': 'Присоединяйтесь к активной молодёжи!',
        'en': 'Join the most active students!',
        'zh': '加入最活跃的青年行列！',
    },
    'cta_text': {
        'uz': 'Loyihalar, festivallar, tanlovlar va yangi döstlar — barçasi bir joyda. Yoşlar ittifoqining Telegram kanaliga obuna böling va yangiliklardan birinçilardan bölib xabardor böling!',
        'ru': 'Проекты, фестивали, конкурсы и новые друзья — всё в одном месте. Подпишитесь на Telegram-канал Союза молодёжи и узнавайте все новости первыми!',
        'en': 'Projects, festivals, contests and new friends — all in one place. Subscribe to the Youth Union Telegram channel and be the first to hear the news!',
        'zh': '项目、节庆、比赛和新朋友——尽在一处。订阅青年联盟 Telegram 频道，第一时间获取最新动态！',
    },
    'cta_label': {
        'uz': 'Telegram kanalga obuna böliş',
        'ru': 'Подписаться в Telegram',
        'en': 'Join on Telegram',
        'zh': '订阅 Telegram 频道',
    },
}


def fill(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='yoshlar-ittifoqi-boshlangich-tashkiloti').first()
    if not p or not SEED.exists():
        return
    seed = json.loads(SEED.read_text(encoding='utf-8'))
    body = dict(p.body or {})
    changed = False
    for lang, text in seed.items():
        old = body.get(lang) or ''
        if len(old) < 500 or any(w in old for w in PLACEHOLDER):
            body[lang] = text
            changed = True
    p.body = body
    if not any((p.staff_hours or {}).values()):
        p.staff_hours = HOURS
    if not p.cta_url:
        for field, value in CTA.items():
            setattr(p, field, value)
        p.cta_url = 'https://t.me/yoshlarittifoqi_uzdjtu'
    # Matn yangilangan bo'lsa — «Oxirgi yangilanish» ham (auto_now faqat update_fields'da bo'lsa yangilanadi)
    p.save(update_fields=['body', 'staff_hours', *CTA, 'cta_url', *(['updated_at'] if changed else [])])


class Migration(migrations.Migration):
    dependencies = [('pages', '0016_touch_updated_pages')]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
