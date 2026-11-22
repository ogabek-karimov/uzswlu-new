"""Yangi alifboga o'girish (apps.core.alphabet) va alifbodan mustaqil qidiruv (fold)."""
from django.test import SimpleTestCase

from apps.api.builders_staff import fold
from apps.core.alphabet import to_new_alphabet


class NewAlphabetTests(SimpleTestCase):
    def test_letters(self):
        self.assertEqual(to_new_alphabet('O‘zbekiston, Toshkent, o‘qituvchi, Sog‘lik, CHET'), 'Özbekiston, Toşkent, öqituvçi, Soğlik, ÇET')
        self.assertEqual(to_new_alphabet("bo'lim boʻyicha jamoatchilik"), 'bölim böyiça jamoatçilik')

    def test_tutuq_and_other_letters_unchanged(self):
        self.assertEqual(to_new_alphabet('ta’lim ma’naviyat yangi'), 'ta’lim ma’naviyat yangi')

    def test_html_links_and_foreign_words_kept(self):
        html = '<a href="https://t.me/shop" class="chip">Toshkent</a> British workshoplar info@uzswlu.uz'
        self.assertEqual(to_new_alphabet(html), '<a href="https://t.me/shop" class="chip">Toşkent</a> British workshoplar info@uzswlu.uz')

    def test_placeholders_and_foreign_suffixes_kept(self):
        self.assertEqual(to_new_alphabet('«{ch}» harfini qo‘shish, Faqat dashboard’da'), '«{ch}» harfini qöşiş, Faqat dashboard’da')

    def test_html_entities_kept(self):
        self.assertEqual(to_new_alphabet('a&shy;b Toshkent&nbsp;shahri <b>x</b>&ch'), 'a&shy;b Toşkent&nbsp;şahri <b>x</b>&ç')

    def test_idempotent(self):
        once = to_new_alphabet('Sharqshunoslik bo‘limi')
        self.assertEqual(to_new_alphabet(once), once)

    def test_fold_matches_both_alphabets(self):
        self.assertEqual(fold('Yöldoşev Çet tillar bölimi'), fold("Yo'ldoshev Chet tillar bo‘limi"))
