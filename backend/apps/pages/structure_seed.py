"""«Tuzilma» sahifasi eski saytdan (uzswlu.uz/tuzilma): kirish matni (4 tilda) va 2 ta PDF — sayt ichida («Ichi ko'rinadi»).

Fayllar: seed_data/files/structure/. Matn — faqat sahifa hali namunaviy/bo'sh bo'lsa; hujjat — sahifada shu nomli hujjat bo'lmasa
(takror ishlatish xavfsiz: `python manage.py seed_admission` buni ham bajaradi).
"""
from pathlib import Path

from django.core.files import File

from apps.core.alphabet import to_new_alphabet as N

FILES = Path(__file__).resolve().parents[2] / 'seed_data' / 'files' / 'structure'
PLACEHOLDER = ('namunaviy', 'примерный', 'sample text', '示例')

BODY = {
    'uz': N('<p>O‘zbekiston davlat jahon tillari universitetining tashkiliy tuzilmasi: universitetni rektor boshqaradi; '
            'Universitet kengashi va Kuzatuv kengashi faoliyat yuritadi. Yoshlar masalalari va ma’naviy-ma’rifiy ishlar, o‘quv ishlari, '
            'ilmiy ishlar va innovatsiyalar, moliya-iqtisod ishlari hamda xalqaro hamkorlik bo‘yicha prorektorlar tegishli boshqarma, '
            'bo‘lim va markazlarni muvofiqlashtiradi. Universitetda 10 ta fakultet va ularga qarashli kafedralar mavjud.</p>'
            '<p>Quyidagi hujjatlardan birini tanlang — u shu sahifaning o‘zida ochiladi. Rahbariyat haqida — '
            '<a href="/rektorat">Rektorat</a>, fakultetlar va kafedralar — <a href="/fakultetlar-va-kafedralar">Fakultetlar va kafedralar</a> sahifasida.</p>'),
    'ru': ('<p>Организационная структура Узбекского государственного университета мировых языков: университетом руководит ректор; '
           'действуют Совет университета и Наблюдательный совет. Проректоры по делам молодёжи и духовно-просветительской работе, '
           'учебной работе, научной работе и инновациям, финансово-экономическим вопросам и международному сотрудничеству '
           'координируют соответствующие управления, отделы и центры. В университете 10 факультетов и относящиеся к ним кафедры.</p>'
           '<p>Выберите документ — он откроется прямо на этой странице. О руководстве — на странице <a href="/ru/rektorat">Ректорат</a>, '
           'о факультетах и кафедрах — на странице <a href="/ru/fakultetlar-va-kafedralar">Факультеты и кафедры</a>.</p>'),
    'en': ('<p>The organisational structure of the Uzbekistan State University of World Languages: the university is headed by the rector; '
           'the University Council and the Supervisory Board operate. Vice-rectors for youth affairs and spiritual and educational work, '
           'academic affairs, research and innovation, finance and economics, and international cooperation coordinate the relevant '
           'departments, divisions and centres. The university has 10 faculties and their departments.</p>'
           '<p>Choose a document — it opens right on this page. See the <a href="/en/rektorat">Rectorate</a> page for the leadership and '
           '<a href="/en/fakultetlar-va-kafedralar">Faculties and departments</a> for the faculties.</p>'),
    'zh': ('<p>乌兹别克斯坦国立世界语言大学组织结构：大学由校长领导，设有大学委员会和监事会。主管青年事务与思想教育工作、教学工作、'
           '科研与创新、财务经济以及国际合作的副校长分别协调相应的处、科和中心。大学共有10个学院及其下属教研室。</p>'
           '<p>选择文件即可在本页直接打开。领导信息见<a href="/zh/rektorat">校长办公室</a>页面，学院和教研室见'
           '<a href="/zh/fakultetlar-va-kafedralar">学院与教研室</a>页面。</p>'),
}
DOCS = [
    ('17526609667676.pdf', {
        'uz': N('Universitet tuzilmasi (Kuzatuv kengashi tomonidan tasdiqlangan, 2025)'),
        'ru': 'Структура университета (утверждена Наблюдательным советом, 2025)',
        'en': 'University structure (approved by the Supervisory Board, 2025)',
        'zh': '大学组织结构（经监事会批准，2025）'}),
    ('17526617997056.pdf', {
        'uz': N('Rahbariyat va fakultetlar tuzilmasi (F.I.Sh. va lavozimlar)'),
        'ru': 'Структура руководства и факультетов (Ф.И.О. и должности)',
        'en': 'Leadership and faculty structure (names and positions)',
        'zh': '领导层与学院结构（姓名与职务）'}),
]


def seed_structure(Page, PageAttachment, Media) -> int:
    p = Page.objects.filter(slug='tuzilma', template='text').first()
    if not p:
        return 0
    uz = (p.body or {}).get('uz') or ''
    if len(uz) < 200 or any(w in uz for w in PLACEHOLDER):
        p.body = BODY
        p.save(update_fields=['body', 'updated_at'])
    have = {(a.title or {}).get('uz') for a in PageAttachment.objects.filter(page=p)}
    added = 0
    for n, (name, title) in enumerate(DOCS, start=1):
        src = FILES / name
        if title['uz'] in have or not src.exists():
            continue
        with src.open('rb') as fh:
            size = src.stat().st_size
            media = Media(folder='docs', kind='pdf', filesize=size, original_size=size, alt={}, sizes={})
            media.file.save(f'tuzilma-{n}.pdf', File(fh, name=f'tuzilma-{n}.pdf'), save=False)
            media.save()
        PageAttachment.objects.create(page=p, file=media, url='', title=title, meta={}, display='embed', order=n)
        added += 1
    return added
