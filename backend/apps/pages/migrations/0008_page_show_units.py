"""Matnli sahifaga «bo'limlar kartalari» (admin → Bo'limlar). /bolimlar sahifasida yoqiladi."""
from django.db import migrations, models


TEXT = {
    'uz': '<p>Bu sahifada universitetning bo‘lim va markazlari hamda ularning rahbarlari ko‘rsatiladi. Ma’lumotlar HEMIS tizimidan olinadi: xodim saytga HEMIS profili orqali kirganida u o‘z bo‘limida avtomatik chiqadi. Bo‘lim kartasini bossangiz, shu bo‘lim xodimlari ochiladi.</p>',
    'ru': '<p>На этой странице представлены отделы и центры университета и их руководители. Данные берутся из системы HEMIS: когда сотрудник входит на сайт через профиль HEMIS, он автоматически появляется в своём отделе. Нажмите на карточку отдела, чтобы увидеть его сотрудников.</p>',
    'en': '<p>This page lists the university’s departments and centres and their heads. The data comes from the HEMIS system: when a staff member signs in to the website with their HEMIS profile, they appear in their department automatically. Click a department card to see its staff.</p>',
    'zh': '<p>本页面展示大学各部门和中心及其负责人。数据来自HEMIS系统：员工通过HEMIS账户登录网站后，会自动显示在其所在部门。点击部门卡片可查看该部门员工。</p>',
}


def enable(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='bolimlar').first()
    if not p:
        return
    p.show_units = True
    body = dict(p.body or {})
    # Faqat namunaviy matn (yoki bo'sh) bo'lsa — admin yozgan matnga tegilmaydi
    if 'namunaviy matn' in (body.get('uz') or '') or not (body.get('uz') or '').strip():
        p.body = TEXT
    p.save(update_fields=['show_units', 'body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0007_page_doc_style')]
    operations = [
        migrations.AddField(model_name='page', name='show_units', field=models.BooleanField(default=False, help_text='admin → Bo‘limlar ro‘yxati (surat, F.I.Sh., lavozim, telefon)', verbose_name='Matndan keyin bo‘limlar kartalari')),
        migrations.RunPython(enable, migrations.RunPython.noop),
    ]
