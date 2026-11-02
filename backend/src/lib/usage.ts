import type { Payload, PayloadRequest, Where } from 'payload'
import { LOCALES } from './i18n'

// Media fayli qayerda ishlatilgan: "Qayerda ishlatilgan" ro'yxati va ishlatilayotgan faylni o'chirishdan himoya.
// Yangi kolleksiyada rasm/PDF maydoni qo'shilsa — shu ro'yxatga ham qo'shiladi.
type Place = { collection: string; fields: string[]; label: (doc: Record<string, any>) => string }

const PLACES: Place[] = [
  { collection: 'posts', fields: ['cover', 'coverByLang.ru', 'coverByLang.en', 'coverByLang.zh', 'gallery', 'attachments.file'], label: d => `${{ news: 'Yangilik', announcements: 'E’lon', events: 'Tadbir' }[d.type as string] ?? 'Post'}: ${d.title?.uz ?? d.label ?? d.id}` },
  { collection: 'slides', fields: ['image'], label: d => `Boş sahifa karuseli: ${d.name}` },
  { collection: 'leaders', fields: ['photo'], label: d => `Rahbariyat: ${d.name}` },
  { collection: 'documents', fields: LOCALES.map(l => `files.${l}`), label: d => `Hujjat: ${d.title?.uz ?? d.id}` },
  { collection: 'users', fields: ['avatar'], label: d => `Foydalanuvçi: ${d.name ?? d.username}` },
  { collection: 'faculties', fields: ['logo', 'cover'], label: d => `Fakultet: ${d.name?.uz ?? d.slug}` },
  { collection: 'departments', fields: ['image'], label: d => `Kafedra: ${d.name?.uz ?? d.hemisId}` },
  { collection: 'pages', fields: ['file', 'attachments.file'], label: d => `Sahifa: ${d.title?.uz ?? d.slug}` },
  { collection: 'sdg-goals', fields: ['sections.images', 'reports.file'], label: d => `BRM ${d.n}: ${d.title?.uz ?? ''}` },
]

const GLOBALS: { slug: string; paths: string[]; label: string }[] = [
  { slug: 'symbols', paths: ['emblem.image', 'flag.image', 'anthem.image', 'anthem.audio'], label: 'Ramzlar' },
]

const idOf = (v: unknown) => (v && typeof v === 'object' ? (v as { id?: unknown }).id : v)
const get = (obj: any, path: string) => path.split('.').reduce((o, k) => o?.[k], obj)

/** Bitta fayl ishlatilgan joylar (o'qish uchun nomlar) */
export async function mediaUsage(payload: Payload, id: number | string, req?: PayloadRequest): Promise<string[]> {
  const out: string[] = []
  for (const place of PLACES) {
    const where: Where = { or: place.fields.map(f => ({ [f]: { equals: id } })) }
    const res = await payload.find({ collection: place.collection as 'posts', where, depth: 0, limit: 20, overrideAccess: true, req, trash: true } as Parameters<Payload['find']>[0])
    for (const doc of res.docs) out.push(place.label(doc as Record<string, any>))
  }
  for (const g of GLOBALS) {
    const doc = await payload.findGlobal({ slug: g.slug as 'symbols', depth: 0, overrideAccess: true, req })
    if (g.paths.some(p => String(idOf(get(doc, p))) === String(id))) out.push(g.label)
  }
  return out
}

/** Ishlatilayotgan barcha fayllar ID'lari ("Ishlatilmaganlar" filtri uchun) */
export async function usedMediaIds(payload: Payload): Promise<Set<string>> {
  const used = new Set<string>()
  const add = (v: unknown) => {
    if (Array.isArray(v)) v.forEach(add)
    else if (v != null && idOf(v) != null) used.add(String(idOf(v)))
  }
  for (const place of PLACES) {
    const res = await payload.find({ collection: place.collection as 'posts', depth: 0, pagination: false, overrideAccess: true, trash: true } as Parameters<Payload['find']>[0])
    for (const doc of res.docs) {
      for (const f of place.fields) {
        const [head, tail] = f.split('.')
        const value = (doc as Record<string, any>)[head!]
        if (tail && Array.isArray(value)) value.forEach(item => add(item?.[tail]))
        else add(tail ? value?.[tail] : value)
      }
    }
  }
  for (const g of GLOBALS) {
    const doc = await payload.findGlobal({ slug: g.slug as 'symbols', depth: 0, overrideAccess: true })
    g.paths.forEach(p => add(get(doc, p)))
  }
  return used
}
