"""Office hujjatlari (Word, Excel, PowerPoint) sahifa hujjati sifatida, tugmali menyu (tab) va akkreditatsiya importi."""
import io
import shutil
import tempfile
import zipfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from apps.core import filesafe
from apps.core.models import Media, validate_upload
from apps.pages.models import Page, PageAttachment


def xlsx(extra: dict | None = None, workbook: bool = True) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        if workbook:
            z.writestr('xl/workbook.xml', '<workbook/>')
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return out.getvalue()


def docx() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('word/document.xml', '<doc/>')
    return out.getvalue()


def xls(extra: str = '') -> bytes:
    return filesafe._OLE_MAGIC + b'\0' * 64 + 'Workbook'.encode('utf-16-le') + extra.encode('utf-16-le') + b'\0' * 64


class OfficeFileSafetyTests(SimpleTestCase):
    def test_excel_accepted(self):
        filesafe.inspect_bytes(xlsx(), '.xlsx')
        filesafe.inspect_bytes(xls(), '.xls')
        validate_upload(SimpleUploadedFile('jadval.xlsx', xlsx()))
        validate_upload(SimpleUploadedFile('hisobot.docx', docx()))

    def test_excel_with_macro_or_wrong_type_rejected(self):
        for data, ext in ((xlsx({'xl/vbaProject.bin': 'x'}), '.xlsx'), (xlsx(workbook=False), '.xlsx'),
                          (xls('Macros'), '.xls'), (docx(), '.xlsx')):
            with self.assertRaises(ValidationError, msg=ext):
                filesafe.inspect_bytes(data, ext)

    def test_other_types_still_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(SimpleUploadedFile('arxiv.zip', b'PK\x03\x04' + b'\0' * 30))


class _MediaRoot(TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.media = override_settings(MEDIA_ROOT=self.tmp)
        self.media.enable()

    def tearDown(self):
        self.media.disable()
        shutil.rmtree(self.tmp, ignore_errors=True)


class OfficeAttachmentTests(_MediaRoot):
    def test_docx_attachment_is_download_card(self):
        from apps.api.builders_site import page_out
        m = Media(folder='docs', alt={}, file=SimpleUploadedFile('Reja 2023.docx', docx()))
        m.save()
        self.assertEqual(m.kind, 'doc')
        p = Page.objects.create(slug='doc-test', title={'uz': 'D'}, template='text')
        PageAttachment.objects.create(page=p, file=m, title={'uz': 'Reja'}, meta={}, display='embed')
        att = page_out(p, 'uz')['attachments'][0]
        self.assertEqual((att['kind'], att['ext'], att['display'], att['height']), ('doc', 'DOCX', 'download', None))
        self.assertTrue(att['meta'].startswith('DOCX · '))


class PageTabsTests(TestCase):
    def test_tabs_flag_and_subpages(self):
        from apps.api.builders_site import page_out
        top = Page.objects.create(slug='akk-test', title={'uz': 'Akk'}, template='text', children_tabs=True)
        Page.objects.create(slug='b-2', title={'uz': 'Ikki'}, template='text', parent=top, order=2)
        Page.objects.create(slug='b-1', title={'uz': 'Bir'}, template='text', parent=top, order=1, icon='book')
        Page.objects.create(slug='b-yopiq', title={'uz': 'Yopiq'}, template='text', parent=top, published=False)
        out = page_out(top, 'uz')
        self.assertTrue(out['tabs'])
        self.assertEqual(out['subpages'], [{'slug': 'b-1', 'title': 'Bir', 'icon': 'book', 'url': '/b-1'},
                                           {'slug': 'b-2', 'title': 'Ikki', 'icon': None, 'url': '/b-2'}])
        self.assertFalse(page_out(Page.objects.get(slug='b-1'), 'uz')['tabs'])


OLD_PAGE = '''<div class="col-lg-9 col-md-12"><div class="notify-item"><h6 class="text-center">
 {title} </h6></div><div class="col-md-3"><a href="/{lang}/../backend/web/uploads/pagepdf/icon/{name}" class="btn">Yuklab</a></div>
<div class="notify-item"><h6>{title2}</h6><a href="/../backend/web/uploads/pagepdf/icon/404.pdf">x</a></div></div>'''


class ImportAccreditationTests(_MediaRoot):
    def test_mirror_import_is_idempotent(self):
        from apps.pages.management.commands.import_accreditation import mirror_name
        top = Page.objects.create(slug='xalqaro-akkreditatsiya', title={'uz': 'Akk'}, template='text')
        child = Page.objects.create(slug='curriculum', title={'uz': 'Curriculum'}, template='text', parent=top)
        mirror = Path(self.tmp) / 'mirror'
        mirror.mkdir()
        names = {'uz': ("O'quv reja", 'Yoq fayl'), 'ru': ('Учебный план', 'Нет'), 'en': ('Curriculum', 'Missing')}
        for lang, (t1, t2) in names.items():
            html = OLD_PAGE.format(title=t1, title2=t2, lang=lang, name='111.xlsx')
            (mirror / mirror_name(f'https://uzswlu.uz/{lang}/curriculum')).write_text(html, encoding='utf-8')
        (mirror / mirror_name('https://uzswlu.uz/backend/web/uploads/pagepdf/icon/111.xlsx')).write_bytes(xlsx())
        for _ in range(2):
            call_command('import_accreditation', mirror=str(mirror), stdout=io.StringIO())
        atts = list(child.attachments.select_related('file'))
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0].title, {'uz': 'Öquv reja', 'ru': 'Учебный план', 'en': 'Curriculum', 'zh': 'Curriculum'})
        self.assertEqual(atts[0].file.kind, 'doc')
