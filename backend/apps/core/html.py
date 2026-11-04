"""Admin muharriridan kelgan HTML'ni tozalash (XSS'dan himoya) va manzil (slug) yasash."""
import re
import unicodedata
from html import unescape
from urllib.parse import urlparse

import nh3

ALLOWED_TAGS = {
    'p', 'h2', 'h3', 'h4', 'strong', 'b', 'em', 'i', 'u', 's', 'sub', 'sup', 'a', 'ul', 'ol', 'li',
    'blockquote', 'br', 'hr', 'img', 'figure', 'figcaption', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'colgroup', 'col', 'iframe', 'span', 'div',
}
ALLOWED_ATTRS = {
    'a': {'href', 'target'},
    'img': {'src', 'alt', 'width', 'height'},
    'iframe': {'src', 'width', 'height', 'allow', 'allowfullscreen', 'title'},
    'div': {'data-youtube-video'},
    'td': {'colspan', 'rowspan', 'style'},
    'th': {'colspan', 'rowspan', 'style'},
    'col': {'style'},
    'p': {'style'},
    'h2': {'style'},
    'h3': {'style'},
    'h4': {'style'},
    'span': {'style'},
}
IFRAME_HOSTS = {'www.youtube.com', 'www.youtube-nocookie.com'}

_COLOR = re.compile(r'^(#[0-9a-f]{3,8}|rgba?\([\d\s.,%]+\))$', re.I)
_STYLE_RULES = {
    'text-align': re.compile(r'^(left|right|center|justify)$'),
    'color': _COLOR,
    'background-color': _COLOR,
    'font-size': re.compile(r'^\d{1,2}(\.\d+)?(px|em|rem|%)$'),
    'font-family': re.compile(r'^[\w\s,\'"-]{1,80}$'),
}


def _clean_style(value: str) -> str | None:
    kept = []
    for decl in value.split(';'):
        if ':' not in decl:
            continue
        prop, _, val = decl.partition(':')
        prop, val = prop.strip().lower(), val.strip()
        rule = _STYLE_RULES.get(prop)
        if rule and rule.match(val):
            kept.append(f'{prop}: {val}')
    return '; '.join(kept) or None


def _attribute_filter(element: str, attribute: str, value: str):
    if attribute == 'style':
        return _clean_style(value)
    if element == 'iframe' and attribute == 'src':
        u = urlparse(value)
        return value if u.scheme == 'https' and u.hostname in IFRAME_HOSTS else None
    if element == 'a' and attribute == 'target':
        return '_blank' if value else None
    return value


def clean_html(html: str | None) -> str:
    if not html:
        return ''
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes={'http', 'https', 'mailto', 'tel'},
        link_rel='noopener noreferrer',
        attribute_filter=_attribute_filter,
    )


_BLOCK_END = re.compile(r'</(p|li|h[1-6]|div|tr|td|th|blockquote|figcaption)>|<br\s*/?>', re.I)


def text_of(html: str | None) -> str:
    """HTML'dan sof matn (so'z sanash, qidiruv va qisqa tavsif uchun)."""
    if not html:
        return ''
    spaced = _BLOCK_END.sub(' ', html)
    return re.sub(r'\s+', ' ', unescape(nh3.clean(spaced, tags=set(), attributes={}))).strip()


TIMELINE_MARK = '<!-- timeline -->'
TIMELINE_SAFE = '<p>[[timeline]]</p>'


def clean_page_html(html: str | None) -> str:
    """Matnli sahifa: `<!-- timeline -->` belgisi tozalashda yo'qolmasin."""
    if not html:
        return ''
    return clean_html(re.sub(r'<!--\s*timeline\s*-->', TIMELINE_SAFE, html))


def restore_timeline(html: str) -> str:
    return re.sub(r'<p>\s*\[\[timeline\]\]\s*</p>', TIMELINE_MARK, html)


def slugify(value: str) -> str:
    """O'zbekcha sarlavhadan manzil: yangi alifbo harflari ham lotinga o'giriladi."""
    s = (value or '').lower()
    s = re.sub(r"[‘’ʻʼ`']", '', s)
    s = s.replace('ö', 'o').replace('ğ', 'g').replace('ş', 'sh').replace('ç', 'ch')
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[̀-ͯ]', '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:80].rstrip('-')
    return s or 'post'
