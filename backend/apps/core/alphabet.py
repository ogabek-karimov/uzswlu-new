"""O'zbek lotin yozuvini yangi alifboga o'girish (qonun bo'yicha): Oʻ→Ö, Gʻ→Ğ, Sh→Ş, Ch→Ç.

Tutuq (ʼ), «ng» va boshqa harflar o'zgarmaydi. HTML teglar (atributlari bilan), havolalar, e-pochtalar va xorijiy
so'zlar (w, th, ph, sch… harf birikmalari bor yoki KEEP ro'yxatidagi) tegilmaydi. Takror ishlatilsa ham xavfsiz.
"""
import re

APOS = "[‘ʻ'’`ʼ]"
RULES = [
    (re.compile('O' + APOS), 'Ö'), (re.compile('o' + APOS), 'ö'),
    (re.compile('G' + APOS), 'Ğ'), (re.compile('g' + APOS), 'ğ'),
    (re.compile('SH'), 'Ş'), (re.compile('Sh'), 'Ş'), (re.compile('sh'), 'ş'),
    (re.compile('CH'), 'Ç'), (re.compile('Ch'), 'Ç'), (re.compile('ch'), 'ç'),
]
NEEDS = re.compile(r'[OoGg]' + APOS + '|[Ss][Hh]|[Cc][Hh]')
# Xorijiy (inglizcha, nemischa…) so'z belgilari — o'zbekchada uchramaydi
# {…} — i18n o'zgaruvchilari ({ch}, {name}) kod qismi, tegilmaydi
FOREIGN = re.compile(r'[wW{}]|sch|ph|th|ck|ee|oo|/|https?:|www\.|@|\.(?:uz|com|org|net|ru)\b', re.I)
# Xorijiy so'zlar; qo'shimcha bilan kelsa ham («dashboard’da», «chatbotlar») tegilmaydi
KEEP = (
    'british', 'english', 'chrome', 'scholar', 'shanghai', 'washington', 'cambridge', 'michigan', 'manchester',
    'chicago', 'deutsch', 'charles', 'chinese', 'teacher', 'research', 'school', 'scheme', 'tech', 'fresh',
    'approach', 'coaching', 'marshall', 'chevening', 'erasmus', 'church', 'speech', 'channel', 'chat', 'match',
    'sketch', 'dashboard', 'flash', 'push', 'hash', 'cache', 'touch', 'mesh',
)
SKIP_PARTS = re.compile(r'(<[^>]+>|&#?\w+;)')
WORD = re.compile(r"[^\s<>\"(),;:!?«»“”]+")


def _word(match: re.Match) -> str:
    w = match.group(0)
    if not NEEDS.search(w) or FOREIGN.search(w) or w.strip('.-–').lower().startswith(KEEP):
        return w
    for rx, rep in RULES:
        w = rx.sub(rep, w)
    return w


def to_new_alphabet(text: str) -> str:
    """Matn yoki HTML: faqat teglar orasidagi matn o'giriladi."""
    if not text or not NEEDS.search(text):
        return text
    # Teglar va HTML belgilar (&shy; &nbsp;) o'zgarmaydi
    parts = SKIP_PARTS.split(text)  # toq indekslar — teg/belgi
    return ''.join(part if i % 2 else WORD.sub(_word, part) for i, part in enumerate(parts))
