"""Sahifa: kartali bloklar (showcase) — matndagi [[kartalar-N]] joyida: kirish gapi, raqamlar, ustunlar (raqamli yoki belgili
bandlar), xulosa gapi. Yoshlar ittifoqi sahifasidagi ro'yxatli bo'limlar (4 tilda) bloklarga o'tkaziladi:
1) tarkib (1 yetakchi, 7 yo'nalish, 10 fakultet koordinatori), 2) maqsad va vazifalar, 3) klublar / loyihalar,
4) «Yoshlar festivali-2023», 5) «Yoshlar festivali-2024». Ruscha matndagi begona «Портфолио, [13.06.2024 16:19]» qatori va
takror band («Mening universitetim» tanlovi) olib tashlanadi. Faqat bloklar hali bo'sh bo'lsa; admin o'zgartirgan matnga tegilmaydi."""
import re

from django.db import migrations, models

PAGE = 'yoshlar-ittifoqi-boshlangich-tashkiloti'
PARA = re.compile(r'<p\b[^>]*>.*?</p>', re.S)
ITEM = re.compile(r'^\s*(?:[-–—]|\d+\.)\s*')
JUNK = re.compile(r'^Портфолио, \[')
TAIL = re.compile(r'(?:,?\s*(?:va hokazo|и др|и т\.\s*д|etc)\.?|等)\s*$', re.I)


def T(uz, ru, en, zh):
    return {'uz': uz, 'ru': ru, 'en': en, 'zh': zh}


# (kalit so'z — kirish paragrafida, bandlar: 'list' | son (ketma-ket paragraflar) | 0, xulosa paragrafi bormi)
SPECS = [
    {   # 1. Tarkib — raqamlar
        'key': T('koordinatorlari mavjud', 'координаторы 7 направлений', '7 direction and 10 faculty coordinators', '7个工作方向协调员'),
        'items': 0,
        'block': {'stats': T(
            '1 | Universitet yoşlar yetakçisi\n7 | Yönaliş koordinatorlari\n10 | Fakultet koordinatorlari',
            '1 | Молодёжный лидер университета\n7 | Координаторов направлений\n10 | Координаторов факультетов',
            '1 | University youth leader\n7 | Area coordinators\n10 | Faculty coordinators',
            '1 | 大学青年领导人\n7 | 工作方向协调员\n10 | 学院协调员')},
    },
    {   # 2. Maqsad va vazifalar — belgili bandlar
        'key': T('asosiy maqsad va vazifalari', 'Основные задачи Союза', 'The main goals and tasks', '主要目标和任务如下'),
        'items': {'ru': 6},
        'column': {'title': T('Asosiy vazifalar', 'Основные задачи', 'Main tasks', '主要任务'), 'icon': 'target', 'style': 'checks'},
    },
    {   # 3. Klublar / loyihalar — nomlar tanlab yozilgan
        'key': T('loyihalarni amalga oşirib kelmoqda', 'реализует ряд полезных проектов', 'number of projects useful for the social life',
                 '一系列有益于大学社会生活的项目'),
        'items': 'list', 'keep_items': False,
        'block': {'columns': [
            {'title': T('Klublar', 'Клубы', 'Clubs', '俱乐部'), 'icon': 'users-round', 'style': 'numbers', 'items': T(
                'Amaliy san’at ustalari\nYoş kitobxon\nZakovat — intellektual klub',
                'Мастера прикладного искусства\nЮный читатель\nЗаковат — интеллектуальный клуб',
                'Masters of Applied Arts\nYoung Reader\nZakovat — intellectual club',
                '实用艺术大师\n青年读者\nZakovat — 智力俱乐部')},
            {'title': T('Loyihalar', 'Проекты', 'Projects', '项目'), 'icon': 'rocket', 'style': 'numbers', 'items': T(
                'Özbekiston böylab sayohat\nÖzbekiston yoşlar forumi\nYoşlar festivali\nTEDxUzSWLU',
                'Путешествие по Узбекистану\nМолодёжный форум Узбекистана\nМолодёжный фестиваль\nTEDxUzSWLU',
                'Travel across Uzbekistan\nYouth Forum of Uzbekistan\nYouth Festival\nTEDxUzSWLU',
                '乌兹别克斯坦之旅\n乌兹别克斯坦青年论坛\n青年节\nTEDxUzSWLU')},
        ]},
    },
    {   # 4. Yoshlar festivali-2023
        'key': T('2023-2024-yillarda bir qator loyihalar', 'В 2023-2024 годах', 'In 2023-2024', '2023—2024年'),
        'items': 'list', 'outro': True,
        'column': {'title': T('Festival dasturi', 'Программа фестиваля', 'Festival programme', '节日活动'), 'icon': 'party-popper', 'style': 'numbers'},
    },
    {   # 5. Yoshlar festivali-2024
        'key': T('taşkil etildi. Uşbu festival', 'В феврале 2024 года', 'In February 2024', '2024年2月'),
        'items': 'list', 'outro': True,
        'column': {'title': T('Festival dasturi', 'Программа фестиваля', 'Festival programme', '节日活动'), 'icon': 'trophy', 'style': 'numbers'},
    },
]


def _plain(html: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


def _item(text: str) -> str:
    text = TAIL.sub('', ITEM.sub('', text)).strip().rstrip(';.,；。').strip()
    # ‘‘Students` party’’ → “Students’ party”
    text = text.replace('‘‘', '“').replace('’’', '”').replace('`', '’')
    return text[:1].upper() + text[1:]


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for x in items:
        key = re.sub(r'^(a|the)\s+', '', re.sub(r'[^\w ]', '', x.lower())).strip()
        if key not in seen:
            seen.add(key)
            out.append(x)
    return out


def _cut(paras: list[str], lang: str, spec: dict):
    """Kirish paragrafi indeksi, oxirgi (o'chiriladigan) paragraf indeksi, bandlar, xulosa."""
    key = spec['key'][lang]
    start = next((i for i, p in enumerate(paras) if key in _plain(p)), None)
    if start is None:
        return None
    end, items, mode = start, [], spec['items']
    count = mode.get(lang) if isinstance(mode, dict) else None
    j = start + 1
    while j < len(paras) and (mode == 'list' or isinstance(mode, dict)):
        text = _plain(paras[j])
        if JUNK.match(text):
            end = j
            j += 1
            continue
        if count is not None:
            if len(items) >= count:
                break
        elif not ITEM.match(text):
            break
        items.append(_item(text))
        end = j
        j += 1
    outro = None
    if spec.get('outro') and end + 1 < len(paras) and not ITEM.match(_plain(paras[end + 1])):
        end += 1
        outro = _plain(paras[end])
    return start, end, _dedupe(items), outro


def forward(apps, schema_editor):
    Page = apps.get_model('pages', 'Page')
    p = Page.objects.filter(slug=PAGE).first()
    if not p or p.showcase:
        return
    body = dict(p.body or {})
    blocks = [{'intro': {}, 'stats': {}, 'columns': [], 'outro': {}} for _ in SPECS]
    for n, spec in enumerate(SPECS):
        block = blocks[n]
        block.update({k: v for k, v in spec.get('block', {}).items()})
        if 'column' in spec:
            block['columns'] = [{**spec['column'], 'items': {}}]
    for lang in ('uz', 'ru', 'en', 'zh'):
        html = body.get(lang) or ''
        spans = [m.span() for m in PARA.finditer(html)]
        paras = [html[a:b] for a, b in spans]
        if not paras:
            continue
        cuts = []
        for n, spec in enumerate(SPECS):
            cut = _cut(paras, lang, spec)
            if not cut:
                continue
            start, end, items, outro = cut
            blocks[n]['intro'][lang] = _plain(paras[start])
            if outro:
                blocks[n]['outro'][lang] = outro
            if 'column' in spec and items:
                blocks[n]['columns'][0]['items'][lang] = '\n'.join(items)
            cuts.append((start, end, n + 1))
        # Asl matndagi joylari bo'yicha (paragraf bo'lmagan qismlarga tegilmaydi), oxiridan boshlab
        for start, end, n in sorted(cuts, reverse=True):
            html = html[:spans[start][0]] + f'<p>[[kartalar-{n}]]</p>' + html[spans[end][1]:]
        body[lang] = html
    p.body = body
    p.showcase = {'blocks': blocks}
    p.save(update_fields=['body', 'showcase', 'updated_at'])


class Migration(migrations.Migration):
    dependencies = [('pages', '0018_youth_clubs')]
    operations = [
        migrations.AddField(
            model_name='page',
            name='showcase',
            field=models.JSONField(blank=True, default=dict, help_text='{intro: {uz…}, columns: [{title: {uz…}, icon, items: {uz: "qator\nqator"}}]} — matndagi [[kartalar]] joyida', verbose_name='Kartali ro‘yxat bloki'),
        ),
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
