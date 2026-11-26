from importlib import import_module

from django.test import SimpleTestCase

from apps.api.builders_site import link_buttons


class LinkButtonsTests(SimpleTestCase):
    def test_row_of_links_becomes_buttons(self):
        html = ('<p><a href="tel:+998712301342">+998 71 230-13-42</a> '
                '<a href="https://t.me/x" target="_blank">Telegram</a> '
                '<a href="mailto:a@b.uz">a@b.uz</a> <a href="/ariza-shakli">Ariza</a></p>')
        out = link_buttons(html)
        self.assertIn('<p class="link-btns">', out)
        for kind in ('tel', 'tg', 'mail', 'web'):
            self.assertIn(f'class="link-btn link-btn--{kind}"', out)

    def test_single_phone_or_mail_link_is_button(self):
        self.assertIn('link-btn--tel', link_buttons('<p><a href="tel:+998711">+998 71 1</a></p>'))

    def test_other_paragraphs_untouched(self):
        for html in ('<p><a href="https://t.me/x/1">Batafsil...</a></p>',          # bitta oddiy havola
                     '<p>Matn <a href="/a">a</a> va <a href="/b">b</a></p>',       # matn ichidagi havolalar
                     '<p><a href="/a"><strong>a</strong></a> <a href="/b">b</a></p>'):
            self.assertEqual(link_buttons(html), html)


class ContactButtonsMigrationTests(SimpleTestCase):
    m = import_module('apps.pages.migrations.0049_contact_buttons')

    def test_anti_corruption_contacts(self):
        html = ('<ul><li>x</li></ul> <p><strong>Boğlaniş:</strong></p> <p><strong>Işçi tel:</strong> +99871-230-13-42 </p> '
                '<p><strong><a href="https://t.me/uzdjtu_antikorrupsiya" target="_blank" rel="noopener">Telegram</a></strong></p>'
                '<p>[[kartalar-1]]</p>')
        out = self.m._anti(html, 'uz')
        self.assertIn('<p><strong>Boğlaniş:</strong></p><p><a href="tel:+998712301342">', out)
        self.assertNotIn('Işçi tel', out)
        self.assertIn('link-btns', link_buttons(out))

    def test_international_links_and_contacts(self):
        html = ('<p>Röyxatdan öting! <a href="/ariza-shakli">/ariza-shakli</a> va '
                '<a href="https://studyin-uzbekistan.uz/universities/35/" target="_blank">https://studyin…</a></p> '
                '<p>Matn.<br>Qöşimça ma’lumot oliş uçun biz bilanboğlaning:<br> Телефон: +998761 230 12 89 '
                'Телеграм: +998 97 449 09 67<br> Email: international@uzswlu.uz</p><p>[[kartalar-1]]</p>')
        out = self.m._intl(html, 'uz')
        self.assertEqual(out.count('<p'), out.count('</p>'))
        self.assertIn('Röyxatdan öting!</p><p><a href="/ariza-shakli">', out)
        self.assertIn('<p>Matn.</p><p><strong>Qöşimça ma’lumot oliş uçun biz bilan boğlaning:</strong></p>', out)
        self.assertIn('href="tel:+998712301289"', out)
        self.assertIn('href="mailto:international@uzswlu.uz"', out)
        self.assertEqual(link_buttons(out).count('class="link-btns"'), 2)
