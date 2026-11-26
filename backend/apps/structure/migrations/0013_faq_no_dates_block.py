"""Qabul sahifasidan «Muhim sanalar» bloki olib tashlandi — savol-javobdagi «yuqoridagi “Muhim sanalar” blokida»
havolasi to'g'rilanadi. Faqat aynan shu gap bor javoblar o'zgaradi (admin tahrir qilgan matnga tegilmaydi)."""
from django.db import migrations

FIX = {
    'uz': ('Aniq muddatlar yuqoridagi “Muhim sanalar” blokida e’lon qilinadi.',
           'Aniq muddatlar my.uzbmb.uz platformasida va universitetning rasmiy kanallarida e’lon qilinadi.'),
    'ru': ('Точные сроки публикуются в блоке «Важные даты».',
           'Точные сроки публикуются на платформе my.uzbmb.uz и в официальных каналах университета.'),
    'en': ('Exact deadlines are published in the “Key dates” block above.',
           'Exact deadlines are announced on my.uzbmb.uz and the university’s official channels.'),
    'zh': ('具体时间见上方“重要日期”。', '具体时间在 my.uzbmb.uz 平台及大学官方渠道公布。'),
}


def forward(apps, schema_editor):
    Faq = apps.get_model('structure', 'AdmissionFaq')
    for f in Faq.objects.all():
        answer = dict(f.answer or {})
        changed = False
        for lang, (old, new) in FIX.items():
            if old in (answer.get(lang) or ''):
                answer[lang] = answer[lang].replace(old, new)
                changed = True
        if changed:
            f.answer = answer
            f.save(update_fields=['answer'])


class Migration(migrations.Migration):
    dependencies = [('structure', '0012_campus_exact_coords')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
