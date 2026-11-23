"""«O'zbekiston–Xitoy II ta'lim forumi dasturi»: eski saytdagi PDF (21 varaq) sahifaning o'zida ochilib turadi —
«Ichi ko'rinadi» (PDF ko'rgiç: birinchi varaq, ostida 1 2 3 …). Namunaviy matn olib tashlanadi.
Faqat sahifada hali hujjat bo'lmasa (seed_data/files/forum/)."""
from pathlib import Path

from django.core.files import File
from django.db import migrations

FILE = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'forum' / 'ozbekiston-xitoy-talim-forumi.pdf'
PLACEHOLDER = ('namunaviy', 'примерный', 'демонстрационный', 'sample text', 'are added in the admin', '示例')
TITLE = {
    'uz': 'Özbekiston–Xitoy ikkinçi ta’lim forumi dasturi',
    'ru': 'Программа второго образовательного форума Узбекистан – Китай',
    'en': 'Programme of the Second Uzbekistan–China Education Forum',
    'zh': '第二届乌兹别克斯坦—中国教育论坛议程',
}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    p = Page.objects.filter(slug='ozbekiston-xitoy-ii-talim-forumi-dasturi').first()
    if not p or not FILE.exists() or PageAttachment.objects.filter(page=p).exists():
        return
    with FILE.open('rb') as fh:
        size = FILE.stat().st_size
        media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
        media.file.save(FILE.name, File(fh, name=FILE.name), save=False)
        media.save()
    PageAttachment.objects.create(page=p, file=media, title=TITLE, display='embed', order=1)
    body = dict(p.body or {})
    for lang, text in list(body.items()):
        if isinstance(text, str) and any(w in text for w in PLACEHOLDER):
            body[lang] = ''
    p.body = body
    p.save(update_fields=['body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0023_innovation_text'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
