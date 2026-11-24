"""«Xalqaro talabalar va o'qituvchilar uchun»: eski saytdagidek 10 ta karta (rasm + nom), har biri o'z sahifasiga olib boradi —
bizda bor sahifalar (Universitet haqida, Bakalavriat, Magistratura, PhD dasturlari, Qabul) va hali yo'qlari (Viza, Summer camp,
Til o'qitish markazi) — eski saytdagi sahifasiga. Nomlar 4 tilda. Rasmlar seed_data/files/applicants-img/xalqaro-…/ .
Faqat sahifada hali karta bo'lmasa (oldingi slayder — kartalarga almashtiriladi)."""
from pathlib import Path

from django.core.files import File
from django.db import migrations

FOLDER = Path(__file__).resolve().parents[3] / 'seed_data' / 'files' / 'applicants-img' / 'xalqaro-talabalar-va-oqituvchilar-uchun'
SLUG = 'xalqaro-talabalar-va-oqituvchilar-uchun'
OLD = 'https://uzswlu.uz'
CARDS = [
    ('/universitet-haqida', {'uz': 'Universitet haqida', 'ru': 'Об университете', 'en': 'About the University', 'zh': '大学概况'}),
    (f'{OLD}/bakalavriat-talim-yonalishlari', {'uz': 'Bakalavriat ta’lim yönalişlari', 'ru': 'Направления бакалавриата', 'en': 'Bachelor’s degree programmes', 'zh': '本科专业'}),
    (f'{OLD}/magistratura-mutaxassisliklari1', {'uz': 'Magistratura mutaxassisliklari', 'ru': 'Специальности магистратуры', 'en': 'Master’s degree programmes', 'zh': '硕士专业'}),
    (f'{OLD}/doktorantura', {'uz': 'Doktorantura', 'ru': 'Докторантура', 'en': 'Doctoral programmes', 'zh': '博士项目'}),
    (f'{OLD}/mustaqil-izlanuvchi', {'uz': 'Mustaqil izlanuvçi', 'ru': 'Самостоятельный соискатель', 'en': 'Independent researcher', 'zh': '独立研究者'}),
    (f'{OLD}/qabul-shartlari', {'uz': 'Qabul şartlari', 'ru': 'Условия приёма', 'en': 'Admission requirements', 'zh': '招生条件'}),
    (f'{OLD}/ariza-shakli', {'uz': 'Ariza şakli', 'ru': 'Подача заявления (анкета)', 'en': 'Application form', 'zh': '申请表'}),
    (f'{OLD}/viza-rasmiylashtirish-va-vaqtincha-royxatga-olish', {'uz': 'Viza rasmiylaştiriş va vaqtinça röyxatga oliş', 'ru': 'Оформление визы и временная регистрация',
                                                                  'en': 'Visa and temporary registration', 'zh': '签证办理与临时登记'}),
    (f'{OLD}/summer-camp', {'uz': 'Summer camp', 'ru': 'Summer camp', 'en': 'Summer camp', 'zh': '夏令营'}),
    (f'{OLD}/til-oqitish-markazi', {'uz': 'Til öqitiş markazi', 'ru': 'Центр языковой подготовки', 'en': 'Language training centre', 'zh': '语言培训中心'}),
]


def forward(apps, schema_editor):
    from apps.core.models import Media  # rasm — WebP + o'lchamlar
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug=SLUG, template='text').first()
    if not p:
        return
    blocks = (p.showcase or {}).get('blocks') or []
    if any(b.get('cards') for b in blocks if isinstance(b, dict)):
        return
    # Oldingi slayderdagi rasmlar (bo'lsa) qayta ishlatiladi, yo'qsa — seed'dan yuklanadi
    old = (blocks[0].get('photos') if blocks and isinstance(blocks[0], dict) else None) or []
    files = sorted(FOLDER.glob('*.jpg')) if FOLDER.exists() else []
    cards = []
    for n, (url, title) in enumerate(CARDS):
        photo = old[n] if n < len(old) else None
        if photo is None and n < len(files):
            with files[n].open('rb') as fh:
                m = Media(folder='posts', alt=title, file=File(fh, name=f'{SLUG}-{files[n].name}'))
                m.save()
            photo = m.pk
        cards.append({'title': title, 'url': url, 'photo': None})  # logotipli rasmlar kerak emas
    p.showcase = {'blocks': [{'intro': {}, 'stats': {}, 'columns': [], 'outro': {}, 'photos': [], 'cards': cards}]}
    uz = (p.body or {}).get('uz') or ''
    if '[[kartalar' not in uz:
        p.body = {k: '<p>[[kartalar-1]]</p>' for k in ('uz', 'ru', 'en', 'zh')}
    p.save(update_fields=['showcase', 'body', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0030_applicants_text'), ('core', '0007_uz_new_alphabet')]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
