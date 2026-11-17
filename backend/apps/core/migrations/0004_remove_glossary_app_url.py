from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_sitesettings_glossary_app_url'),
        ('content', '0006_seed_quick_links'),  # avval havola QuickLink'ga ko'chiriladi, keyin maydon o'chadi
    ]

    operations = [migrations.RemoveField(model_name='sitesettings', name='glossary_app_url')]
