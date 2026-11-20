"""Murojaat matni «haqiqiy matn»mi: tasodifiy harflar, bir so'zni takrorlash va belgilar to'plamini rad etadi.
frontend/shared/utils/text-quality.ts bilan bir xil qoidalar. Qisqartmalar (BRM, AKT, PhD), raqamli so'zlar, havola/e-pochta hisobga olinmaydi."""
import re

VOWELS = re.compile(r'[aeiouyöüıаеёиоуыэюяўіїє]', re.I)
CONSONANT_RUN = re.compile(r'[bcdfghjklmnpqrstvwxzğşçбвгджзйклмнпрстфхцчшщқғҳ]{5,}', re.I)
ROWS = ('qwertyuiop', 'asdfghjkl', 'zxcvbnm', 'йцукенгшщзхъ', 'фывапролджэ', 'ячсмитьбю')
ABBR = {'phd', 'dsc', 'msc', 'bsc', 'mba', 'llm', 'md', 'ielts', 'toefl', 'sat', 'gpa', 'cefr', 'brm', 'akt', 'dtm', 'otm', 'hemis'}
LEET = {'@': 'a', '0': 'o', '1': 'i', '$': 's', '3': 'e', '4': 'a'}
LAT2CYR = dict(zip('aeopcxykmthb', 'аеорсхукмтнв'))
# Kirill → lotin «skelet»: rus so'zi lotincha yozilsa ham ushlanadi (blyad, nahuy, pizda). «x» → «h» QILINMAYDI (o'zbekcha «xuy-atvor»)
CYR2LAT = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm',
           'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '',
           'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'iu', 'я': 'ia', 'ў': 'o', 'қ': 'q', 'ғ': 'g', 'ҳ': 'h'}
LAT_SKELETON = (('sch', 'sh'), ('shch', 'sh'), ('kh', 'h'), ('zh', 'j'), ('ya', 'ia'), ('ja', 'ia'), ('yu', 'iu'), ('ju', 'iu'), ('yo', 'e'),
                ('ye', 'e'), ('ts', 'c'), ('tz', 'c'), ('y', 'i'), ('w', 'v'))   # «j→i» yo'q: o'zbekcha «hujjat» ≠ «хуй»
CYRILLIC = re.compile(r'[а-яёўқғҳ]')


def cyr_skeleton(w):
    return ''.join(CYR2LAT.get(c, c) for c in w)


def lat_skeleton(w):
    for x, y in LAT_SKELETON:
        w = w.replace(x, y)
    return w


def rude_key(token):
    w = re.sub(r"[‘’ʻʼ`']", '', token.lower().replace('ё', 'е'))
    w = ''.join(LEET.get(c, c) for c in w)
    w = re.sub(r'^[\W\d_]+|[\W\d_]+$', '', w)
    if CYRILLIC.search(w):
        w = ''.join(LAT2CYR.get(c, c) for c in w)
    return w


class RudeMatcher:
    """Haqoratli so'zlar: «*» bilan tugasa — so'z boshi, ichida «*» — namuna, aks holda — aynan so'z; xitoycha — matn ichida.
    Kirillcha yozuvlar lotin «skeleti» bilan ham solishtiriladi (lotin harflarda yozilgan rus so'zi)."""

    def __init__(self, words):
        self.exact, self.prefix, self.cjk, self.pattern = set(), [], [], []
        self.lat_exact, self.lat_prefix = set(), []
        for raw in words:
            w = (raw or '').strip().lower().replace('ё', 'е')
            if not w:
                continue
            if re.search(r'[\u3400-\u9FFF]', w):
                self.cjk.append(w)
            elif '*' in w[:-1]:
                self.pattern.append(re.compile('^' + re.escape(w).replace(r'\*', '.*')))
            elif w.endswith('*'):
                self.prefix.append(w[:-1])
                if CYRILLIC.search(w):
                    self.lat_prefix.append(cyr_skeleton(w[:-1]))
            else:
                self.exact.add(w)
                if CYRILLIC.search(w):
                    self.lat_exact.add(cyr_skeleton(w))

    def __call__(self, token):
        if any(r in token for r in self.cjk):
            return True
        w = rude_key(token)
        if len(w) < 2:
            return False
        if w in self.exact or any(w.startswith(p) for p in self.prefix) or any(r.match(w) for r in self.pattern):
            return True
        if re.fullmatch(r'[a-z]+', w):
            sk = lat_skeleton(w)
            return sk in self.lat_exact or any(sk.startswith(p) for p in self.lat_prefix)
        return False


def rude_matcher():
    """Faol haqoratli so'zlar (admin → Haqoratli so'zlar)."""
    from apps.structure.models import RudeWord
    return RudeMatcher(RudeWord.objects.filter(active=True).values_list('word', flat=True))


CJK = re.compile(r'[㐀-鿿豈-﫿]')
EDGE = re.compile(r'^[\W\d_]+|[\W\d_]+$')


def keyboard_run(w):
    """Klaviatura qatori bo'yicha 5+ harf ketma-ket (asdfg, фывап); 4 bo'lsa «запрос» ham tushib qolardi."""
    lw = w.lower()
    return any(any(lw[i:i + 5] in r for r in ROWS) for i in range(len(lw) - 4))


def low_vowels(w):
    return len(w) >= 7 and len(VOWELS.findall(w)) / len(w) < 0.125   # spring, grants, strong, «средств» — o'tadi


def is_abbr(w):
    return w.lower() in ABBR or len(w) <= 8 and (any(c.isupper() for c in w[1:]) or (w == w.upper() and w != w.lower()))


OTHER_SCRIPT = re.compile(r'[\u3400-\u9FFF\uF900-\uFAFF\u0590-\u08FF]')


def is_junk_word(w):
    """Tasodifiy harflardan iborat so'z (frontend isJunkWord bilan bir xil asosiy qoida)."""
    if re.search(r'(.)\1{4,}', w):
        return True
    if OTHER_SCRIPT.search(w):   # xitoycha, arabcha/forscha — unli/undosh qoidalari tegishli emas
        return False
    return (len(w) >= 5 and not VOWELS.search(w)) or bool(CONSONANT_RUN.search(w)) or keyboard_run(w) or low_vowels(w) or len(w) > 30


def is_meaningful_text(raw: str, rude=None) -> bool:
    """rude — RudeMatcher (berilmasa bazadan olinadi)."""
    text = raw.strip()
    rude = rude or rude_matcher()
    if any(rude(t) for t in text.split()):
        return False
    if len(text) < 10:
        return False
    if re.search(r'(.)\1{4,}', re.sub(r'\s', '', text)):
        return False
    if len(CJK.findall(text)) >= 5:
        return True

    words = []
    for tok in text.split():
        if re.search(r'[/@]|\.\w', tok) or re.search(r'\d', tok):
            continue
        w = EDGE.sub('', tok)
        if len(w) < 2:
            continue
        words.append(w)
    if len(words) < 3:
        return False

    letters = sum(ch.isalpha() for ch in text)
    visible = len(re.sub(r'\s', '', text))
    if letters / visible < 0.6:
        return False

    # Qisqartmalar (BRM, AKT, PhD, DSc, DsC, MSc): so'z sifatida sanaladi, lekin shubhali deb baholanmaydi
    if sum(1 for w in words if not is_abbr(w)) < 2:   # faqat qisqartmalardan iborat matn emas
        return False
    junk = sum(1 for w in words if not is_abbr(w) and is_junk_word(w))
    if junk / len(words) > 0.25:
        return False

    lower = [w.lower() for w in words]
    if len(lower) >= 6 and len(set(lower)) / len(lower) < 0.35:
        return False
    return not has_repeats(lower)


def has_repeats(lower):
    """Bir so'z ketma-ket ikki marta 2+ joyda yoki 3+ marta ketma-ket, yoki bitta so'z matnning 40% dan ko'pi
    (kamida 3 marta, 5+ so'zda). Bitta «juda juda» — ruxsat."""
    if any(lower[i] == lower[i - 1] == lower[i - 2] for i in range(2, len(lower))):
        return True
    if sum(1 for i in range(1, len(lower)) if lower[i] == lower[i - 1]) >= 2:
        return True
    if len(lower) >= 5:
        top = max(lower.count(w) for w in set(lower))
        return top >= 3 and top / len(lower) > 0.4
    return False
