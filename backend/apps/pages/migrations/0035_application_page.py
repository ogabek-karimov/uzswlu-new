"""«Xalqaro talabalar va o'qituvchilar uchun» → «Ariza shakli»: bizning saytdagi sahifa (forma — ApplicationForm, arizalar admin panelda).
Karta endi shu sahifaga olib boradi."""
from django.db import migrations

SLUG = 'ariza-shakli'
PARENT = 'xalqaro-talabalar-va-oqituvchilar-uchun'
TITLE = {'uz': 'Ariza şakli', 'ru': 'Форма заявки', 'en': 'Application form', 'zh': '申请表'}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    parent = Page.objects.filter(slug=PARENT).first()
    if not parent or Page.objects.filter(slug=SLUG).exists():
        return
    Page.objects.create(slug=SLUG, title=TITLE, body={k: '' for k in TITLE}, template='text', parent=parent, in_menu=False, order=6)
    for b in (parent.showcase or {}).get('blocks') or []:
        for c in b.get('cards') or []:
            if c.get('url', '').rstrip('/').endswith('/ariza-shakli'):
                c['url'] = f'/{SLUG}'
    parent.save(update_fields=['showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0034_international_subpages')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
