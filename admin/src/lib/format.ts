// Sana va vaqt — har doim Toshkent vaqti (UTC+5), 24 soatlik formatda

const MONTHS = ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr']

function tashkent(iso: string | Date) {
  const d = new Date(iso)
  return new Date(d.getTime() + 5 * 3600 * 1000)
}

const pad = (n: number) => String(n).padStart(2, '0')

/** 23.10.2026 · 19:00 */
export function dateTime(iso?: string | null) {
  if (!iso) return '—'
  const t = tashkent(iso)
  return `${pad(t.getUTCDate())}.${pad(t.getUTCMonth() + 1)}.${t.getUTCFullYear()} · ${pad(t.getUTCHours())}:${pad(t.getUTCMinutes())}`
}

/** 23-oktabr, 2026 · 19:00 (saytdagidek) */
export function longDateTime(iso?: string | null) {
  if (!iso) return '—'
  const t = tashkent(iso)
  return `${t.getUTCDate()}-${MONTHS[t.getUTCMonth()]}, ${t.getUTCFullYear()} · ${pad(t.getUTCHours())}:${pad(t.getUTCMinutes())}`
}

/** "Bugun · 19:02", "Keça · 15:12" yoki to'liq sana */
export function relative(iso?: string | null) {
  if (!iso) return '—'
  const t = tashkent(iso)
  const now = tashkent(new Date())
  const day = (x: Date) => Date.UTC(x.getUTCFullYear(), x.getUTCMonth(), x.getUTCDate())
  const diff = (day(now) - day(t)) / 86400000
  const time = `${pad(t.getUTCHours())}:${pad(t.getUTCMinutes())}`
  if (diff === 0) return `Bugun · ${time}`
  if (diff === 1) return `Keça · ${time}`
  return dateTime(iso)
}

/** <input type="date"> va <input type="time"> uchun qiymatlar (Toshkent vaqti) */
export function toInputs(iso?: string | null) {
  const t = tashkent(iso ?? new Date())
  return { date: `${t.getUTCFullYear()}-${pad(t.getUTCMonth() + 1)}-${pad(t.getUTCDate())}`, time: `${pad(t.getUTCHours())}:${pad(t.getUTCMinutes())}` }
}

export function fromInputs(date: string, time: string) {
  if (!date) return null
  return new Date(`${date}T${time || '00:00'}:00+05:00`).toISOString()
}

export function fileSize(bytes?: number | null) {
  if (!bytes) return ''
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}
