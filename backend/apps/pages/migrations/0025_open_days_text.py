"""«Ochiq eshiklar kunlari»: eski saytdagi matn (uz/ru/en; uz — yangi alifboda) + xitoycha tarjima; tadbir kollaji (bitta rasm,
o'z nisbatida — kesilmaydi, bosilsa kattalashadi) va «Qachon va kimga murojaat» bloki (har oyning oxirgi haftasi, telefonlar).
Faqat sahifa hali namunaviy va bloklar bo'sh bo'lsa (seed_data/open_days_page.json, seed_data/files/open-days/)."""
import json
from pathlib import Path

from django.core.files import File
from django.db import migrations

DATA = Path(__file__).resolve().parents[3] / 'seed_data'
FILES = DATA / 'files' / 'open-days'
PLACEHOLDER = ('namunaviy', 'примерный', 'демонстрационный', 'sample text', 'are added in the admin', '示例')
ALT = {'uz': 'Öçiq eşiklar kunlari — tadbirdan lavhalar', 'ru': 'Дни открытых дверей — моменты мероприятия',
       'en': 'Open Door Days — moments from the event', 'zh': '开放日活动剪影'}


def _media(name: str):
    from apps.core.models import Media  # haqiqiy model: WebP + o'lchamlar (admin yuklagandagi kabi)
    path = FILES / f'{name}.jpg'
    if not path.exists():
        return None
    with path.open('rb') as fh:
        m = Media(folder='posts', alt=ALT, file=File(fh, name=path.name))
        m.save()
    return m.pk


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='ochiq-eshiklar-kunlari').first()
    seed_path = DATA / 'open_days_page.json'
    if not p or not seed_path.exists() or p.showcase:
        return
    uz = (p.body or {}).get('uz') or ''
    if len(uz) >= 500 and not any(w in uz for w in PLACEHOLDER):
        return
    seed = json.loads(seed_path.read_text(encoding='utf-8'))
    blocks = seed['showcase']['blocks']
    for b in blocks:
        b['photos'] = [pk for pk in (_media(n) for n in b.get('photos') or []) if pk]
    p.body = {**(p.body or {}), **seed['body']}
    p.showcase = {'blocks': blocks}
    p.save(update_fields=['body', 'showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0024_forum_pdf'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
