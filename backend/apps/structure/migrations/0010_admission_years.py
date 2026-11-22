"""Qabul sozlamalari (bitta yozuv) → Qabul yillari: mavjud yozuv «faol» yil bo'ladi, sanalar va savol-javob unga bog'liq qoladi."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('structure', '0009_merge_campus_faculty')]
    operations = [
        migrations.RenameModel('AdmissionSettings', 'AdmissionYear'),
        migrations.AlterModelOptions(name='admissionyear', options={'ordering': ['-year'], 'verbose_name': 'Qabul yili', 'verbose_name_plural': 'Qabul yillari'}),
        migrations.AddField(model_name='admissionyear', name='status', field=models.CharField(choices=[('draft', 'Qoralama'), ('active', 'Faol'), ('archive', 'Arxiv')], db_index=True, default='active', max_length=8, verbose_name='Holati')),
        migrations.AlterField(model_name='admissionyear', name='status', field=models.CharField(choices=[('draft', 'Qoralama'), ('active', 'Faol'), ('archive', 'Arxiv')], db_index=True, default='draft', max_length=8, verbose_name='Holati')),
        migrations.AddField(model_name='admissionyear', name='public', field=models.BooleanField(default=True, verbose_name='Arxivda saytda ko‘rinadi')),
        migrations.AddField(model_name='admissionyear', name='programs_snapshot', field=models.JSONField(blank=True, default=list, verbose_name='Yo‘nalishlar (arxiv nusxasi)')),
        migrations.AlterField(model_name='admissionyear', name='year', field=models.CharField(default='2026/2027', help_text='Masalan 2027/2028', max_length=9, unique=True, verbose_name='O‘quv yili')),
    ]
