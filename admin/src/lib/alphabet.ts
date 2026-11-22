// O'zbek lotin yozuvini yangi alifboga o'girish (qonun bo'yicha): Oʻ→Ö, Gʻ→Ğ, Sh→Ş, Ch→Ç.
// backend/apps/core/alphabet.py bilan bir xil qoidalar: tutuq (ʼ) va boshqa harflar o'zgarmaydi; HTML teglar, HTML belgilar
// (&shy;), havolalar, e-pochtalar, {…} o'zgaruvchilar va xorijiy so'zlar (Dashboard, British, workshop…) tegilmaydi.
const APOS = "[‘ʻ'’`ʼ]"
const RULES: [RegExp, string][] = [
  [new RegExp(`O${APOS}`, 'g'), 'Ö'], [new RegExp(`o${APOS}`, 'g'), 'ö'],
  [new RegExp(`G${APOS}`, 'g'), 'Ğ'], [new RegExp(`g${APOS}`, 'g'), 'ğ'],
  [/SH/g, 'Ş'], [/Sh/g, 'Ş'], [/sh/g, 'ş'],
  [/CH/g, 'Ç'], [/Ch/g, 'Ç'], [/ch/g, 'ç'],
]
const NEEDS = new RegExp(`[OoGg]${APOS}|[Ss][Hh]|[Cc][Hh]`)
const FOREIGN = /[wW{}]|sch|ph|th|ck|ee|oo|\/|https?:|www\.|@|\.(?:uz|com|org|net|ru)\b/i
const KEEP = [
  'british', 'english', 'chrome', 'scholar', 'shanghai', 'washington', 'cambridge', 'michigan', 'manchester',
  'chicago', 'deutsch', 'charles', 'chinese', 'teacher', 'research', 'school', 'scheme', 'tech', 'fresh',
  'approach', 'coaching', 'marshall', 'chevening', 'erasmus', 'church', 'speech', 'channel', 'chat', 'match',
  'sketch', 'dashboard', 'flash', 'push', 'hash', 'cache', 'touch', 'mesh',
]
const SKIP_PARTS = /(<[^>]+>|&#?\w+;)/
const WORD = /[^\s<>"(),;:!?«»“”]+/g

function word(w: string): string {
  const bare = w.replace(/^[.\-–]+|[.\-–]+$/g, '').toLowerCase()
  if (!NEEDS.test(w) || FOREIGN.test(w) || KEEP.some(k => bare.startsWith(k))) return w
  return RULES.reduce((s, [rx, rep]) => s.replace(rx, rep), w)
}

/** Matn yoki HTML: faqat teglar orasidagi matn o'giriladi. Takror ishlatilsa ham xavfsiz. */
export function toNewAlphabet(text: string): string {
  if (!text || !NEEDS.test(text)) return text
  return text.split(SKIP_PARTS).map((part, i) => (i % 2 ? part : part.replace(WORD, word))).join('')
}

/** Eski alifbo harflari bormi (tugmani ko'rsatish uchun) */
export function hasOldLetters(text: string | null | undefined): boolean {
  return !!text && toNewAlphabet(text) !== text
}

/** Ob'ekt ichidagi barcha {uz: '…'} qiymatlarini o'giradi (forma: sarlavha, matn, teglar…). Nechta maydon o'zgardi — qaytaradi. */
export function convertUzDeep(value: unknown): number {
  let changed = 0
  const walk = (v: unknown) => {
    if (Array.isArray(v)) { v.forEach(walk); return }
    if (!v || typeof v !== 'object') return
    const o = v as Record<string, unknown>
    for (const [k, x] of Object.entries(o)) {
      if (k === 'uz' && typeof x === 'string') {
        const n = toNewAlphabet(x)
        if (n !== x) { o[k] = n; changed++ }
      }
      else walk(x)
    }
  }
  walk(value)
  return changed
}
