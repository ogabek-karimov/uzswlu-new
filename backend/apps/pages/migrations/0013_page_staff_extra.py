"""Sahifa: admin HEMIS ro'yxatidan qo'lda qo'shadigan xodimlar (zaxira joy)."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pages', '0012_page_staff_department')]
    operations = [
        migrations.AddField('page', 'staff_extra', models.JSONField(
            'Qo‘shimcha xodimlar (HEMIS ID)', default=list, blank=True,
            help_text='Zaxira: admin HEMIS ro‘yxatidan qo‘lda qo‘shgan xodimlar — bo‘lim xodimlaridan keyin chiqadi')),
    ]
