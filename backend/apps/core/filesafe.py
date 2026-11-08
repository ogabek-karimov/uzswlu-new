"""Yuklangan fayllarni chuqur tekshirish va tozalash — faqat Python (Pillow + standart kutubxona).

Tashqi dastur (antivirus, ImageMagick va h.k.) kerak emas. Printsip: «tekshirib o'tkazish» emas, imkon qadar
**qayta qurish** — rasm piksellaridan yangi fayl yasaladi (metadata, ilova qilingan ma'lumot yo'qoladi);
PDF/Office fayllarda esa faol kontent (skript, makro, ichki fayl, tashqi havola) bo'lsa rad etiladi.

  clean_upload(file, exts, max_bytes) → (ContentFile, ext)   — kabinet hujjati, murojaat fayli
  inspect_pdf / inspect_ooxml / inspect_ole                  — turga xos tekshiruvlar
  reencode_image                                              — JPEG/PNG/WEBP/GIF → tozalangan nusxa
  random_name(ext)                                            — mijoz bergan nom hech qachon saqlanmaydi

Xato bo'lsa `ValidationError` (matni foydalanuvchiga ko'rsatilishi mumkin).
"""
import io
import os
import re
import uuid
import zipfile
import zlib

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

# Rasm o'lchami (piksel) chegarasi: kichik fayl, lekin ochilganda gigabaytlab xotira oladigan «bomba»dan himoya
MAX_PIXELS = 40_000_000
MAX_SIDE = 12_000
# PDF ichidagi siqilgan oqimlarni ochishdagi chegaralar
PDF_MAX_STREAM = 16 * 1024 * 1024
PDF_MAX_TOTAL = 64 * 1024 * 1024
# OOXML (docx/pptx) zip chegaralari
ZIP_MAX_ENTRIES = 4000
ZIP_MAX_TOTAL = 300 * 1024 * 1024
ZIP_MAX_RATIO = 200
XML_READ_CAP = 2 * 1024 * 1024

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
_FORMAT_FOR_EXT = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP', '.gif': 'GIF'}

_OLE_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
MAGIC = {
    '.pdf': (b'%PDF-',),
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.png': (b'\x89PNG\r\n\x1a\n',),
    '.gif': (b'GIF87a', b'GIF89a'),
    '.webp': (b'RIFF',),
    '.doc': (_OLE_MAGIC,),
    '.ppt': (_OLE_MAGIC,),
    '.docx': (b'PK\x03\x04',),
    '.pptx': (b'PK\x03\x04',),
    '.mp3': (b'ID3', b'\xff'),
}


def fail(message: str):
    raise ValidationError(message)


def random_name(ext: str) -> str:
    """Mijoz bergan fayl nomi saqlanmaydi: tasodifiy nom (path traversal, belgilar, taxmin qilinadigan manzil yo'q)."""
    return f"{uuid.uuid4().hex}{ext.lower()}"


def ext_of(name: str | None) -> str:
    base = os.path.basename((name or '').replace('\\', '/'))
    return os.path.splitext(base)[1].lower()


# ───────────────────────────── Rasm ─────────────────────────────

def open_image(data: bytes) -> Image.Image:
    """Rasmni xavfsiz ochadi: format, o'lcham chegarasi va butunlik tekshiriladi. Piksellar yuklangan holda qaytadi."""
    try:
        probe = Image.open(io.BytesIO(data))
        fmt, (w, h) = probe.format, probe.size
        if fmt not in _FORMAT_FOR_EXT.values():
            fail('Faqat JPG, PNG, WEBP yoki GIF rasm qabul qilinadi')
        if w < 1 or h < 1 or w > MAX_SIDE or h > MAX_SIDE or w * h > MAX_PIXELS:
            fail('Rasm o‘lchami juda katta')
        probe.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
        return img
    except ValidationError:
        raise
    except Exception as exc:  # noqa: BLE001 — buzilgan, kesilgan yoki «bomba» rasm
        raise ValidationError('Rasm buzilgan yoki o‘qib bo‘lmadi') from exc


def reencode_image(data: bytes, ext: str) -> bytes:
    """Rasmni piksellaridan qayta quradi: EXIF/GPS, ICC, matn bo'laklari va fayl oxiriga yopishtirilgan
    qo'shimcha ma'lumot (polyglot) tashlab yuboriladi. Format kengaytmaga mos bo'lishi shart."""
    img = open_image(data)
    expected = _FORMAT_FOR_EXT.get(ext)
    if expected is None or img.format != expected:
        fail('Fayl tarkibi kengaytmasiga mos emas')
    img = ImageOps.exif_transpose(img)
    out = io.BytesIO()
    if expected == 'JPEG':
        img.convert('RGB').save(out, format='JPEG', quality=88, optimize=True)
    elif expected == 'PNG':
        has_alpha = 'A' in img.mode or 'transparency' in img.info
        img.convert('RGBA' if has_alpha else 'RGB').save(out, format='PNG', optimize=True)
    elif expected == 'WEBP':
        has_alpha = 'A' in img.mode or 'transparency' in img.info
        img.convert('RGBA' if has_alpha else 'RGB').save(out, format='WEBP', quality=85)
    else:  # GIF — birinchi kadr
        img.convert('P', palette=Image.ADAPTIVE).save(out, format='GIF')
    return out.getvalue()


# ───────────────────────────── PDF ─────────────────────────────

# Faol/xavfli PDF nomlari (kichik harfda). Skript, avtomatik harakat, ichki fayl, tashqi yuborish.
_PDF_BAD_NAMES = {
    'javascript', 'js', 'launch', 'embeddedfile', 'embeddedfiles', 'richmedia', 'xfa', 'submitform',
    'importdata', 'gotor', 'gotoe', 'rendition', 'encrypt',
}
_NAME_RE = re.compile(rb'/([A-Za-z0-9#_.\-]{1,64})')
_HEX_ESC = re.compile(rb'#([0-9A-Fa-f]{2})')
# `(?<!end)` — oldingi obyektning `endstream` so'zi yangi oqim boshi deb olinmasligi uchun
_STREAM_RE = re.compile(rb'(?<!end)stream\r?\n.*?endstream', re.DOTALL)
_OBJSTM_STREAM_RE = re.compile(rb'(?<!end)stream\r?\n(.*?)\r?\n?endstream', re.DOTALL)


def _pdf_names(blob: bytes) -> set[str]:
    """PDF nomlari: `/J#61vaScript` kabi yashirilgan yozuvlar ochiladi (#xx → belgi)."""
    found = set()
    for raw in _NAME_RE.findall(blob):
        if b'#' in raw:
            raw = _HEX_ESC.sub(lambda m: bytes([int(m.group(1), 16)]), raw)
        found.add(raw.decode('latin-1').lower())
    return found


def inspect_pdf(data: bytes) -> None:
    """PDF'ni tekshiradi: skript, avto-harakat, ichki fayl, parol, buzilgan tuzilma bo'lsa rad etadi.

    Skanerlash ikki joyda: (1) oqimlardan tashqari matn qismi; (2) `/ObjStm` (ichma-ich obyektlar) oqimlari
    ochilgandan keyin — skript shu yerda yashirilishi mumkin. Rasm va boshqa binar oqimlar skanerlanmaydi
    (tasodifiy baytlar yolg'on signal berardi)."""
    if not data.startswith(b'%PDF-'):
        fail('PDF fayl buzilgan')
    eof = data.rfind(b'%%EOF')
    if eof < 0 or data[eof + 5:].strip(b' \t\r\n\0'):
        # %%EOF dan keyin bo'shliqdan boshqa narsa bo'lmasligi kerak (polyglot: PDF + zip/html yuklama)
        fail('PDF fayl oxiri buzilgan yoki unga qo‘shimcha ma’lumot yopishtirilgan')

    outside = _STREAM_RE.sub(b'', data)
    bad = _pdf_names(outside) & _PDF_BAD_NAMES
    total = 0
    for m in _OBJSTM_STREAM_RE.finditer(data):
        # Faqat obyekt oqimlari: lug'at oqimdan oldingi 600 baytda `/ObjStm` bilan keladi
        head = _pdf_names(data[max(0, m.start() - 600):m.start()])
        if 'objstm' not in head:
            continue
        body = m.group(1)
        if body[:1] != b'\x78':  # zlib sarlavhasi; boshqa filtrlar (ASCII85 va h.k.) — qo'llab-quvvatlanmaydi
            fail('PDF ichki tuzilmasi qo‘llab-quvvatlanmaydi')
        try:
            d = zlib.decompressobj()
            plain = d.decompress(body, PDF_MAX_STREAM)
            if d.unconsumed_tail:
                fail('PDF juda murakkab yoki «bomba»')
        except zlib.error:
            fail('PDF ichki oqimi buzilgan')
        total += len(plain)
        if total > PDF_MAX_TOTAL:
            fail('PDF juda murakkab yoki «bomba»')
        bad |= _pdf_names(plain) & _PDF_BAD_NAMES
    if bad:
        if 'encrypt' in bad:
            fail('Parol bilan himoyalangan PDF qabul qilinmaydi')
        fail('PDF ichida skript yoki ichki fayl bor — qabul qilinmaydi')


# ───────────────────────────── OOXML (docx / pptx) ─────────────────────────────

_REL_RE = re.compile(rb'<Relationship\b[^>]*>', re.IGNORECASE)
_BAD_ZIP_DIRS = ('vbaproject', '/activex/', '/macros/')
_BAD_ZIP_EXTS = ('.exe', '.dll', '.js', '.vbs', '.bat', '.cmd', '.ps1', '.html', '.htm', '.swf', '.jar', '.lnk', '.scr')
_OK_EMBEDDED = ('.xlsx', '.docx', '.pptx')  # diagramma/jadval uchun ichki hujjatlar


def inspect_ooxml(data: bytes, kind: str) -> None:
    """docx/pptx: zip «bomba», xavfli yo'l nomlari, makro, ActiveX, ichki OLE, tashqi (hyperlinkdan boshqa) ulanishlar."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        fail('Fayl buzilgan')
    with zf:
        infos = zf.infolist()
        if not infos or len(infos) > ZIP_MAX_ENTRIES:
            fail('Fayl tuzilmasi noto‘g‘ri')
        total = 0
        names: set[str] = set()
        for i in infos:
            n = i.filename
            parts = n.split('/')
            if n.startswith('/') or '\\' in n or '\0' in n or '..' in parts or ':' in parts[0]:
                fail('Faylda xavfli yo‘l nomi bor')
            if i.flag_bits & 0x1:
                fail('Parol bilan himoyalangan fayl qabul qilinmaydi')
            total += i.file_size
            if i.file_size > 100 * 1024 * 1024 or total > ZIP_MAX_TOTAL:
                fail('Fayl ichi juda katta («bomba»)')
            if i.compress_size and i.file_size > 1024 * 1024 and i.file_size / i.compress_size > ZIP_MAX_RATIO:
                fail('Fayl ichi juda zich siqilgan («bomba»)')
            names.add(n.lower())
        for n in names:
            path = f'/{n}'
            bad = any(d in path for d in _BAD_ZIP_DIRS) or n.endswith(_BAD_ZIP_EXTS)
            if '/embeddings/' in path and not n.endswith(_OK_EMBEDDED):
                bad = True
            if bad:
                fail('Faylda makro, ActiveX yoki ichki bajariladigan qism bor — qabul qilinmaydi')
        required = 'word/document.xml' if kind == 'docx' else 'ppt/presentation.xml'
        if '[content_types].xml' not in names or required not in names:
            fail('Fayl turi kengaytmasiga mos emas')

        def read(name: str) -> bytes:
            with zf.open(name) as fh:
                blob = fh.read(XML_READ_CAP + 1)
            if len(blob) > XML_READ_CAP:
                fail('Fayl ichidagi xml juda katta')
            return blob

        ctypes = next(i.filename for i in infos if i.filename.lower() == '[content_types].xml')
        ct = read(ctypes).lower()
        if b'macroenabled' in ct or b'vbaproject' in ct or b'oleobject' in ct:
            fail('Faylda makro yoki ichki ob’ekt bor — qabul qilinmaydi')
        for i in infos:
            if not i.filename.lower().endswith('.rels'):
                continue
            for rel in _REL_RE.findall(read(i.filename)):
                low = rel.lower()
                if b'targetmode="external"' not in low and b"targetmode='external'" not in low:
                    continue
                kind_ok = b'/hyperlink"' in low or b"/hyperlink'" in low
                if not kind_ok:
                    fail('Faylda tashqi manbaga ulanish bor (shablon/rasm/ob’ekt) — qabul qilinmaydi')
                target = re.search(rb'target\s*=\s*["\']([^"\']*)["\']', low)
                if not target or not target.group(1).startswith((b'http://', b'https://', b'mailto:', b'#')):
                    fail('Faylda xavfli havola bor')


# ───────────────────────────── OLE (doc / ppt) ─────────────────────────────

def _u16(s: str) -> bytes:
    return s.encode('utf-16-le')


_OLE_BAD = tuple(_u16(s) for s in ('_VBA_PROJECT', 'VBA', 'Macros', 'ObjectPool', 'Ole10Native', 'EncryptedPackage'))


def inspect_ole(data: bytes, kind: str) -> None:
    """Eski .doc/.ppt: makro (VBA), ichki ob'ekt va parollangan paket bo'lsa rad etiladi. Katalog nomlari UTF-16LE."""
    if not data.startswith(_OLE_MAGIC):
        fail('Fayl turi kengaytmasiga mos emas')
    needed = _u16('WordDocument' if kind == 'doc' else 'PowerPoint Document')
    if needed not in data:
        fail('Fayl turi kengaytmasiga mos emas')
    if any(marker in data for marker in _OLE_BAD):
        fail('Faylda makro yoki ichki ob’ekt bor — qabul qilinmaydi')


# ───────────────────────────── MP3 ─────────────────────────────

def inspect_mp3(head: bytes) -> None:
    ok = head.startswith(b'ID3') or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)
    if not ok:
        fail('MP3 fayl buzilgan')


# ───────────────────────────── Umumiy kirish nuqtasi ─────────────────────────────

def read_all(file, max_bytes: int) -> bytes:
    if getattr(file, 'size', 0) > max_bytes:
        fail(f'Fayl {max_bytes // 1024 // 1024} MB dan katta')
    file.seek(0)
    data = file.read(max_bytes + 1)
    file.seek(0)
    if len(data) > max_bytes:
        fail(f'Fayl {max_bytes // 1024 // 1024} MB dan katta')
    if not data:
        fail('Fayl bo‘sh')
    return data


def inspect_bytes(data: bytes, ext: str) -> None:
    """Turga qarab tegishli chuqur tekshiruv (rasmlar uchun — faqat ochib ko'rish)."""
    if ext == '.pdf':
        inspect_pdf(data)
    elif ext in ('.docx', '.pptx'):
        inspect_ooxml(data, ext[1:])
    elif ext in ('.doc', '.ppt'):
        inspect_ole(data, ext[1:])
    elif ext in IMAGE_EXTS:
        open_image(data)
    elif ext == '.mp3':
        inspect_mp3(data[:16])
    else:
        fail('Fayl turi ruxsat etilmagan')


def clean_upload(file, exts, max_bytes: int):
    """Faylni tekshiradi va **tozalangan nusxani** qaytaradi: `(ContentFile, ext)`.

    - kengaytma ruxsat ro'yxatida va tarkib (magic) unga mos bo'lishi shart;
    - rasm — piksellaridan qayta quriladi; PDF/Office — faol kontent bo'lsa rad etiladi;
    - nom har doim tasodifiy (mijoz nomi saqlanmaydi).
    """
    ext = ext_of(getattr(file, 'name', ''))
    if ext not in exts or ext not in MAGIC:
        fail('Fayl turi ruxsat etilmagan')
    data = read_all(file, max_bytes)
    if not any(data.startswith(m) for m in MAGIC[ext]):
        fail('Fayl tarkibi kengaytmasiga mos emas')
    if ext in IMAGE_EXTS:
        data = reencode_image(data, ext)
    else:
        inspect_bytes(data, ext)
    return ContentFile(data, name=random_name(ext)), ext
