"""Online translatsiya: eski saytdagi 4 ta onlayn kamera (rtsp.ru). Matnda «Nomi | havola» qatorlari — saytda 2 ustunli setka
(builders_site.cameras_html). Faqat namunaviy matndagi sahifa yangilanadi."""
from django.db import migrations

CAMS = [('A-411', '0PTXP9QewJ7LjblZ'), ('A-412', 'MpwO9lhgrdPmcUzO'), ('A-415', 'HCrgQtKT3mSBudko'), ('A-417', 'YG9hlYrJMhAZE1Pt')]
INTRO = {
    'uz': 'Auditoriyalardagi darslar va tadbirlarni onlayn kuzatiş. Kamerani töliq ekranda köriş uçun videodagi tugmani bosing.',
    'ru': 'Онлайн-трансляция занятий и мероприятий из аудиторий. Чтобы открыть камеру на весь экран, нажмите кнопку в видео.',
    'en': 'Live broadcast of classes and events from the lecture rooms. Use the button in the video to open a camera in full screen.',
    'zh': '教室课程与活动在线直播。点击视频中的按钮可全屏观看。',
}


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug='online-translatsiya').first()
    if not p or 'admin panel orqali kiritiladi' not in str((p.body or {}).get('uz', '')):
        return
    lines = ''.join(f'<p>{n} | https://rtsp.ru/embed/{k}/</p>' for n, k in CAMS)
    p.body = {lang: f'<p>{text}</p>{lines}' for lang, text in INTRO.items()}
    p.save(update_fields=['body'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0041_brm_from_old_site')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
