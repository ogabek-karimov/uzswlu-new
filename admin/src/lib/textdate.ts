// Post matnidan sanani topish — nashr vaqti uçun (PostEditPage → «Matndagi sana»).
// Tillar: özbekça (lotin, kirill), ruscha, inglizça, xitoyça va raqamli yozuvlar (20.10.2026, 2026-10-20, 20/10/26).
// Ma'lumot yetmasa — töldiriladi: yil yöq → joriy yil (kelajakka tuşsa — ötgan yil), vaqt yöq → 09:00, kun yöq → 1-kun.
// Hammasi Toshkent vaqti (UTC+5).

export type TextDate = {
  /** ISO (UTC) — API uçun */
  iso: string
  /** <input type="date"> / <input type="time"> qiymatlari */
  date: string
  time: string
  /** Matndagi asl parça, masalan «2026-yil 20-oktabr» */
  snippet: string
  /** Matnda bölmagan va taxmin qilingan qismlar */
  guessed: ('year' | 'day' | 'time')[]
  lang: 'uz' | 'ru' | 'en' | 'zh'
}

type Field = Partial<Record<'uz' | 'ru' | 'en' | 'zh', string | null>>
type Source = { title?: Field; excerpt?: Field; body?: Field }

// Oy nomlari — boşi (ildizi) bilan: «oktabr», «oktyabr», «октября», «October», «Oct.» …
const MONTH_STEMS: [string, number][] = [
  ['yanv', 1], ['fevr', 2], ['mart', 3], ['aprel', 4], ['may', 5], ['iyun', 6], ['iyul', 7], ['avgust', 8], ['sent', 9], ['okt', 10], ['noya', 11], ['dek', 12],
  ['янв', 1], ['фев', 2], ['мар', 3], ['апр', 4], ['ма[йя]', 5], ['июн', 6], ['июл', 7], ['авг', 8], ['сен', 9], ['окт', 10], ['ноя', 11], ['дек', 12],
  ['jan', 1], ['feb', 2], ['mar', 3], ['apr', 4], ['jun', 6], ['jul', 7], ['aug', 8], ['sep', 9], ['oct', 10], ['nov', 11], ['dec', 12],
]
const MONTH = `(${MONTH_STEMS.map(([s]) => s).join('|')})\\p{L}*\\.?`
const monthOf = (word: string) => {
  const w = word.toLowerCase()
  for (const [stem, n] of MONTH_STEMS) if (new RegExp(`^${stem}`, 'u').test(w)) return n
  return 0
}

const NOT_DIGIT_BEFORE = '(?<![\\d\\p{L}])'
const DAY = `${NOT_DIGIT_BEFORE}(\\d{1,2})`
const YEAR_WORD = `(?:\\s*-?\\s*(?:yil\\p{L}*|йил\\p{L}*|г(?:ода|од)?\\.?|year))?`

type Hit = { index: number; end: number; y?: number; m: number; d?: number; score: number }

// Har bir qolip: regex va topilgan guruhlardan {y, m, d}
const PATTERNS: { re: RegExp; read: (g: RegExpExecArray) => Omit<Hit, 'index' | 'end' | 'score'> | null }[] = [
  // 2026-yil 20-oktabr · 2026 йил 20 октябр · 2026 г. 20 октября
  { re: new RegExp(`${NOT_DIGIT_BEFORE}(\\d{4})${YEAR_WORD}[,\\s]*${DAY}\\s*-?\\s*(?:chi\\s*)?${MONTH}`, 'giu'), read: g => ({ y: +g[1]!, d: +g[2]!, m: monthOf(g[3]!) }) },
  // 20-oktabr 2026 · 20 октября 2026 г. · 20 October 2026 · 20-oktabr
  { re: new RegExp(`${DAY}\\s*[-.]?\\s*(?:chi\\s*|th\\s+|st\\s+|nd\\s+|rd\\s+)?(?:of\\s+)?${MONTH}(?:[,\\s]+(\\d{4})(?!\\d))?`, 'giu'), read: g => ({ d: +g[1]!, m: monthOf(g[2]!), y: g[3] ? +g[3] : undefined }) },
  // October 20, 2026 · oktabrning 20-kuni · Oct 20
  { re: new RegExp(`(?<![\\p{L}])${MONTH}\\s+(\\d{1,2})(?!\\d)(?:-?(?:kuni|st|nd|rd|th))?(?:,?\\s+(\\d{4})(?!\\d))?`, 'giu'), read: g => ({ m: monthOf(g[1]!), d: +g[2]!, y: g[3] ? +g[3] : undefined }) },
  // 2026年10月20日 · 10月20日
  { re: /(?:(\d{4})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]/gu, read: g => ({ y: g[1] ? +g[1] : undefined, m: +g[2]!, d: +g[3]! }) },
  // 2026-10-20 · 2026.10.20
  { re: /(?<!\d)(\d{4})[-./](\d{1,2})[-./](\d{1,2})(?!\d)/gu, read: g => ({ y: +g[1]!, m: +g[2]!, d: +g[3]! }) },
  // 20.10.2026 · 20/10/2026 · 20.10.26
  { re: /(?<![\d.])(\d{1,2})[./](\d{1,2})[./](\d{4}|\d{2})(?![\d.]\d)/gu, read: g => ({ d: +g[1]!, m: +g[2]!, y: g[3]!.length === 2 ? 2000 + +g[3]! : +g[3]! }) },
  // oktabr 2026 · 2026-yil oktabr (kun yöq)
  { re: new RegExp(`(?<![\\p{L}\\d])${MONTH}\\s+(\\d{4})(?!\\d)`, 'giu'), read: g => ({ m: monthOf(g[1]!), y: +g[2]! }) },
  { re: new RegExp(`${NOT_DIGIT_BEFORE}(\\d{4})${YEAR_WORD}\\s+${MONTH}`, 'giu'), read: g => ({ y: +g[1]!, m: monthOf(g[2]!) }) },
]

const TIME = /(?:soat|соат|в|at|кун(?:и)?\s+соат)?\s*(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?![\d.:/]?\d)/iu

const pad = (n: number) => String(n).padStart(2, '0')

/** HTML → oddiy matn */
export function plainText(html: string) {
  return html.replace(/<(br|\/p|\/div|\/li|\/h\d)[^>]*>/gi, '\n').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&[a-z]+;/gi, ' ').replace(/[ \t]+/g, ' ')
}

function valid(y: number, m: number, d: number) {
  if (y < 1990 || y > 2100 || m < 1 || m > 12 || d < 1 || d > 31) return false
  const dt = new Date(Date.UTC(y, m - 1, d))
  return dt.getUTCMonth() === m - 1
}

/** Bitta matndan eng birinçi (tölaroq) sanani topadi */
export function findDate(text: string, now = new Date()): Omit<TextDate, 'lang'> | null {
  const hits: Hit[] = []
  for (const { re, read } of PATTERNS) {
    re.lastIndex = 0
    for (let g = re.exec(text); g; g = re.exec(text)) {
      const r = read(g)
      if (!r || !r.m) continue
      hits.push({ ...r, index: g.index, end: g.index + g[0].length, score: (r.y ? 2 : 0) + (r.d ? 2 : 0) })
    }
  }
  // Ustma-ust tuşganlardan — tölarog'i (yil+kun), keyin matnda birinçisi
  hits.sort((a, b) => a.index - b.index || b.score - a.score)
  const picked = hits.filter(h => !hits.some(o => o !== h && o.index <= h.index && o.end >= h.end && o.score > h.score))
  const nowT = new Date(now.getTime() + 5 * 3600 * 1000) // Toshkent «devor soati»
  for (const h of picked.filter(x => x.d).concat(picked.filter(x => !x.d))) {
    const guessed: TextDate['guessed'] = []
    const d = h.d ?? 1
    if (!h.d) guessed.push('day')
    let y = h.y
    if (!y) {
      guessed.push('year')
      y = nowT.getUTCFullYear()
      // Yil yozilmagan sana kelajakka tuşsa — bu ötgan yilgi voqea
      if (Date.UTC(y, h.m - 1, d) > Date.UTC(nowT.getUTCFullYear(), nowT.getUTCMonth(), nowT.getUTCDate() + 1)) y -= 1
    }
    if (!valid(y, h.m, d)) continue
    const tm = TIME.exec(text.slice(h.end, h.end + 60)) ?? TIME.exec(text.slice(Math.max(0, h.index - 25), h.index))
    const time = tm ? `${pad(+tm[1]!)}:${tm[2]}` : '09:00'
    if (!tm) guessed.push('time')
    const date = `${y}-${pad(h.m)}-${pad(d)}`
    return { iso: new Date(`${date}T${time}:00+05:00`).toISOString(), date, time, snippet: text.slice(h.index, h.end).trim(), guessed }
  }
  return null
}

/** Post: avval özbekça (matn → qisqa tavsif → sarlavha), keyin rus, ingliz, xitoy */
export function detectPostDate(p: Source, now = new Date()): TextDate | null {
  for (const lang of ['uz', 'ru', 'en', 'zh'] as const) {
    for (const field of [p.body, p.excerpt, p.title]) {
      const raw = field?.[lang]
      if (!raw?.trim()) continue
      const hit = findDate(plainText(raw), now)
      if (hit) return { ...hit, lang }
    }
  }
  return null
}
