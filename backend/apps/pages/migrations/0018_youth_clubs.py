"""Sahifa: karta belgisi (icon) va «Ichki sahifalar kartalari» (show_children).
Yoshlar ittifoqi → 8 ta tadbir sahifasi (eski manzillar: /zakovat, /futbol …; menyuda emas) va ularning hujjatlari (eski saytdagi
Word fayllar PDF'ga o'girilgan — seed_data/files/youth/), shuningdek Yoshlar ittifoqi sahifasining o'z hujjati.
Faqat sahifa hali yo'q bo'lsa yaratiladi; admin o'zgartirganlariga tegilmaydi."""
import json
from pathlib import Path

from django.core.files import File
from django.db import migrations, models

DATA = Path(__file__).resolve().parents[3] / 'seed_data'
FILES = DATA / 'files' / 'youth'
PARENT = 'yoshlar-ittifoqi-boshlangich-tashkiloti'


def _media(Media, name: str):
    path = FILES / name
    if not path.exists():
        return None
    with path.open('rb') as fh:
        size = path.stat().st_size
        media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
        media.file.save(name, File(fh, name=name), save=False)
        media.save()
    return media


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    PageAttachment = apps.get_model('pages', 'PageAttachment')
    Media = apps.get_model('core', 'Media')
    parent = Page.objects.filter(slug=PARENT).first()
    seed_path = DATA / 'youth_clubs.json'
    if not parent or not seed_path.exists():
        return
    seed = json.loads(seed_path.read_text(encoding='utf-8'))

    if seed.get('yi') and not parent.attachments.exists():
        media = _media(Media, seed['yi']['file'])
        if media:
            PageAttachment.objects.create(page=parent, file=media, title=seed['yi']['title'], display='open', order=1)
    if not parent.show_children:
        parent.show_children = True
        parent.save(update_fields=['show_children'])

    for order, club in enumerate(seed['clubs'], start=1):
        if Page.objects.filter(slug=club['slug']).exists():
            continue
        page = Page.objects.create(
            slug=club['slug'], title=club['title'], template='text', parent=parent, icon=club['icon'],
            in_menu=False, published=True, order=order, body={}, lead={}, description={},
        )
        for n, doc in enumerate(club['docs'], start=1):
            media = _media(Media, doc['file'])
            if media:
                PageAttachment.objects.create(page=page, file=media, title=doc['title'], display='open', order=n)


class Migration(migrations.Migration):
    dependencies = [('pages', '0017_youth_union_text'), ('core', '0007_uz_new_alphabet')]
    operations = [
        migrations.AddField('page', 'icon', models.CharField(
            'Belgi (karta uchun)', max_length=40, blank=True,
            help_text='Lucide belgisi nomi, masalan: brain, chess-knight, volleyball (lucide.dev/icons)')),
        migrations.AddField('page', 'show_children', models.BooleanField(
            'Matndan keyin ichki sahifalar kartalari', default=False,
            help_text='Shu sahifa ichidagi sahifalar — belgi, nom va hujjatlari bilan kartalar')),
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
