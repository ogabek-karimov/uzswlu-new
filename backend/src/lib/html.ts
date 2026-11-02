import sanitizeHtml from 'sanitize-html'

// Ruxsat etilgan inline uslublar: faqat tekislash, rang, shrift va o'lcham (muharrir panelidagilar)
const COLOR = [/^#[0-9a-f]{3,8}$/i, /^rgba?\([\d\s.,%]+\)$/i]
const STYLES = {
  'text-align': [/^(left|right|center|justify)$/],
  color: COLOR,
  'background-color': COLOR,
  'font-size': [/^\d{1,2}(\.\d+)?(px|em|rem|%)$/],
  'font-family': [/^[\w\s,'"-]{1,80}$/],
}

/** Admin muharriridan kelgan HTML'ni tozalash: faqat ruxsat etilgan teglar (XSS'dan himoya) */
export function cleanHtml(html: string | null | undefined): string {
  if (!html) return ''
  return sanitizeHtml(html, {
    allowedTags: ['p', 'h2', 'h3', 'h4', 'strong', 'b', 'em', 'i', 'u', 's', 'sub', 'sup', 'a', 'ul', 'ol', 'li', 'blockquote', 'br', 'hr', 'img', 'figure', 'figcaption', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'colgroup', 'col', 'iframe', 'span', 'div'],
    allowedAttributes: {
      a: ['href', 'target', 'rel'],
      img: ['src', 'alt', 'width', 'height'],
      iframe: ['src', 'width', 'height', 'allow', 'allowfullscreen', 'title'],
      div: ['data-youtube-video'],
      td: ['colspan', 'rowspan', 'style'],
      th: ['colspan', 'rowspan', 'style'],
      col: ['style'],
      p: ['style'],
      h2: ['style'],
      h3: ['style'],
      h4: ['style'],
      span: ['style'],
    },
    allowedStyles: { '*': STYLES },
    allowedIframeHostnames: ['www.youtube.com', 'www.youtube-nocookie.com'],
    allowedSchemes: ['http', 'https', 'mailto', 'tel'],
    transformTags: {
      a: (tagName, attribs) => ({
        tagName,
        attribs: { ...attribs, rel: 'noopener noreferrer', ...(attribs.target && attribs.target !== '_blank' ? { target: '_blank' } : {}) },
      }),
    },
  })
}

/** HTML'dan sof matn (so'z sanash, qisqa tavsif uchun) */
export function textOf(html: string | null | undefined): string {
  return sanitizeHtml(html ?? '', { allowedTags: [], allowedAttributes: {} }).replace(/\s+/g, ' ').trim()
}

/** O'zbekcha sarlavhadan manzil (slug): yangi alifbo harflari ham lotinga o'giriladi */
export function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[‘’ʻʼ`']/g, '')
    .replace(/ö/g, 'o').replace(/ğ/g, 'g').replace(/ş/g, 'sh').replace(/ç/g, 'ch')
    .normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80)
    .replace(/-+$/g, '') || 'post'
}
