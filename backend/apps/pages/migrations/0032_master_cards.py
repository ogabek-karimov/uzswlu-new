"""«Magistrlik dasturlari»: eski saytdagidek 4 ta havolali karta (rasmsiz) — Eslatma, Qabul nizomi, Qabul kvotasi,
Qabul hujjatlari töplami. Bizda hali bu sahifalar yöq — eski saytdagi sahifasiga olib boradi. Nomlar 4 tilda."""
from django.db import migrations

SLUG = 'magistrlik-dasturlari'
OLD = 'https://uzswlu.uz'
CARDS = [
    (f'{OLD}/eslatma', {'uz': 'Eslatma', 'ru': 'Напоминание', 'en': 'Reminder', 'zh': '提示'}),
    (f'{OLD}/qabul-nizomi', {'uz': 'Qabul nizomi', 'ru': 'Правила приёма', 'en': 'Admission regulations', 'zh': '招生章程'}),
    (f'{OLD}/qabul-kvotasi', {'uz': 'Qabul kvotasi', 'ru': 'Квота приёма', 'en': 'Admission quota', 'zh': '招生名额'}),
    (f'{OLD}/qabul-hujjatlari-toplami', {'uz': 'Qabul hujjatlari töplami', 'ru': 'Пакет документов для поступления',
                                         'en': 'Admission documents package', 'zh': '入学申请材料'}),
]


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug=SLUG, template='text').first()
    if not p:
        return
    blocks = (p.showcase or {}).get('blocks') or []
    if any(b.get('cards') for b in blocks if isinstance(b, dict)):
        return
    cards = [{'title': t, 'url': u, 'photo': None} for u, t in CARDS]
    p.showcase = {'blocks': [{'intro': {}, 'stats': {}, 'columns': [], 'outro': {}, 'photos': [], 'cards': cards}]}
    p.body = {k: '<p>[[kartalar-1]]</p>' for k in ('uz', 'ru', 'en', 'zh')}
    p.save(update_fields=['showcase', 'body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0031_international_cards')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
