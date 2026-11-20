from django.test import TestCase

from apps.api.text_quality import is_meaningful_text

GOOD = [
    'Assalomu alaykum, BRM böyiça hisobotni qayerdan topsam böladi?',
    'Prošu predostavitʼ spravku ob obučenii dlja IELTS i PhD programmy.',
    'Здравствуйте, прошу выдать справку об обучении для посольства.',
    'Hello, I would like to ask about the PhD admission deadline in 2026.',
    'Hurmatli rektor, AKT kafedrasi DTM natijalari haqida ma’lumot bering.',
    'PhD, DSc va DsC dasturlari haqida.',
    'phd va dsc dasturlariga qabul qachon?',
    'bugun kechga vaqt bo‘ladimi? bugun ertalab bora olmadim',
    'Hujjat va diplom va transkript va ma’lumotnoma kerak',
    'Xizmatingiz juda juda yaxshi, katta rahmat sizga',
    'Kotibiyat va sikl jadvali haqida ma’lumot bering',
    'Dickens asarlari bo‘yicha seminar qachon bo‘ladi?',
    'Talabaning xuy-atvori va odobi haqida tavsifnoma kerak',
    'Hujjatlar jadvali uyda qoldi, suyak shikastlanishi bo‘yicha javob kerak',
    'Hujjat topshirish muddati va huquqiy asoslar haqida',
    'Thanks, the spring grants and student rights are strong this month',
    'Мой запрос по проложить маршрут и фильтр скрыть не работает',
    'Прошу выделить средств для поездки на конференцию',
    'Suhbat jadvali va kafedra mudiri haqida ma’lumot bering',
    'MSc BSc PhD DSc böyiça qabul qaçon boşlanadi?',
    '您好，我想咨询一下硕士研究生的入学申请材料。',
    'Mening strengths va weaknesses haqida test natijam https://example.com/a dagi faylda.',
]
BAD = [
    'asdfgh jklqwe rtyzxc',
    'фывапр олджэё йцукен',
    'aaaaaaaaaaaaaaa',
    'salom salom salom salom salom salom salom',
    '!!!! ???? 12345 ....',
    'ok ok',
    'Siz ahmoqsiz, javob bermadingiz hali ham',
    'Вы просто идиот, ответа нет до сих пор',
    'This is bullshit, nobody answered my question',
    'Bu sh1t nima degani ekan endi',
    'Blyad nega javob yo‘q hali ham',
    'Ну это просто pizdec какой-то, ответа нет',
    'Idi nahuy s takim otvetom pozhaluysta',
    '你们都是混蛋，没有人回答我的问题',
    'bugun kechga boraman bugun bugun bugun  bugun',
    'iltimos yordam bering bering bering',
    'bugun kechga boraman shunday shunday qanday qanday ibora ibora nega nega xayr xayr',
    'PhD DSc BRM AKT',
    'qwrtpsdfg mnbvcxz lkjhgfd prstv',
]


class TextQualityTests(TestCase):   # haqoratli so‘zlar bazadan (migratsiya ro‘yxati)
    def test_real_text_passes(self):
        for t in GOOD:
            self.assertTrue(is_meaningful_text(t), t)

    def test_gibberish_rejected(self):
        for t in BAD:
            self.assertFalse(is_meaningful_text(t), t)


class RudeWordsAdminTests(TestCase):
    """Admin → Haqoratli so‘zlar: qo‘shilgan so‘z darhol ishlaydi, o‘chirib qo‘yilgani — yo‘q; /contact ro‘yxatni beradi."""

    def setUp(self):
        from apps.accounts.models import User
        from tests.support import PASSWORD, jwt_for, loose
        User.objects.create_user('rw_root', password=PASSWORD, role='superadmin', name='RW')
        with loose():
            self.h = jwt_for('rw_root')

    def test_admin_word_blocks_and_toggle(self):
        from apps.api.text_quality import is_meaningful_text
        from tests.support import api
        text = 'Bu kafedrada zumbalak degan gap aytildi'
        self.assertTrue(is_meaningful_text(text))
        r = api('post', '/api/cms/rude-words', self.h, {'word': 'Zumbalak*', 'lang': 'uz'})
        self.assertIn(r.status_code, (200, 201), r.content)
        doc = r.json().get('doc', r.json())
        self.assertEqual(doc['word'], 'zumbalak*')
        self.assertFalse(is_meaningful_text(text))
        self.assertIn('zumbalak*', self.client.get('/api/contact').json()['rudeWords'])
        api('patch', f"/api/cms/rude-words/{doc['id']}", self.h, {'active': False})
        self.assertTrue(is_meaningful_text(text))
        self.assertEqual(api('post', '/api/cms/rude-words', self.h, {'word': 'ahmoq*', 'lang': 'uz'}).status_code // 100, 4)   # takror
        self.assertEqual(api('post', '/api/cms/rude-words', self.h, {'word': 'a', 'lang': 'uz'}).status_code // 100, 4)        # qisqa
