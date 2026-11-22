"""«Tezkor xizmatlar» kartalari: ruxsat etilgan ikonkalar va havolani tekshirish.

Ikonkalar ro'yxati ataylab cheklangan: sayt ikonkalarni yig'ish vaqtida (`@nuxt/icon` scan) paketga qo'shadi, shuning uchun
bazadagi ixtiyoriy nom brauzerda ko'rinmay qolmasligi kerak. Ro'yxat `frontend/shared/quick-icons.ts` va admin paneldagi
`QuickLinksPage.vue` bilan bir xil bo'lishi shart (test tekshiradi).
"""
import re

ICONS = (
    ('lucide:message-square-text', 'Murojaat (xabar)'),
    ('lucide:graduation-cap', 'Talaba (bosh kiyim)'),
    ('lucide:database', 'Ma’lumotlar bazasi'),
    ('lucide:mail', 'Poçta'),
    ('lucide:briefcase-business', 'Karyera (portfel)'),
    ('lucide:sprout', 'Maysa'),
    ('lucide:book-a', 'Luğat (kitob)'),
    ('app:akt-lugat', 'AKT luğati logosi (rasm)'),   # rasm-belgi: frontend public/images/quick/akt-lugat.webp
    ('lucide:smartphone', 'Mobil ilova'),
    ('lucide:globe', 'Veb-sayt'),
    ('lucide:calendar-days', 'Taqvim'),
    ('lucide:file-text', 'Hujjat'),
    ('lucide:library', 'Kutubxona'),
    ('lucide:phone', 'Telefon'),
    ('lucide:users', 'Odamlar'),
    ('lucide:video', 'Video'),
    ('lucide:map-pin', 'Manzil'),
    ('lucide:award', 'Mukofot'),
    ('lucide:life-buoy', 'Yordam'),
)
ICON_NAMES = tuple(name for name, _ in ICONS)

PATH = re.compile(r'^/(?!/)[\w\-./?=&%#]*$')
EXTERNAL = re.compile(r'^https?://[^\s]+$', re.I)


def valid_url(url: str) -> bool:
    """Sayt ichidagi yo'l (`/career`) yoki tashqi `https://…` havola; `javascript:` va boshqalar rad etiladi."""
    return bool(PATH.match(url) or EXTERNAL.match(url))
