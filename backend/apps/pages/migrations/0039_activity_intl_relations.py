"""«Xalqaro aloqalar» bölim sahifasi eski saytdagi matn va 5 ta karta bilan (0037 da u boşqa sahifaning ichki sahifasi deb
olinib, böş qolgan edi). Uzun xatboşilar sarlavha emas, oddiy matn; eski saytdagi işlamaydigan ariza havolasi — bizning
«Ariza şakli». Namunaviy matnli yoki eski havolali bölsa yangilanadi."""
from django.db import migrations

from apps.pages.activity_seed import seed_pages, specs

SLUG = 'xalqaro-aloqalar'


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    seed_pages(Page, 2)
    p = Page.objects.filter(slug=SLUG).first()
    spec = next((s for s in specs(2) if s['slug'] == SLUG), None)
    if p and spec and 'uzswlu.uz/xalqaro-hamkorlik' in str(p.body):
        p.body = spec['body']
        p.showcase = {'blocks': spec['showcase']}
        p.save(update_fields=['body', 'showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0038_activity_images')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
