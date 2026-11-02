import type { Endpoint } from 'payload'
import { type I18n, type Lang, pick } from '../lib/i18n'
import { recordHit } from '../lib/analytics'
import { fileOf, imageOf, json, langOf, type MediaDoc, sizeLabel } from '../lib/public'

// Sayt (Nuxt) uchun ochiq API: karusel, rektorat, hujjatlar, video darsliklar, davlat ramzlari.
// Javoblar shared/types/api.ts dagi shartnoma bo'yicha.

type Doc = Record<string, any>

/** Tanlangan til, bo'lmasa o'zbekchasi */
const tr = (value: I18n | null | undefined, lang: Lang) => pick(value, lang) ?? pick(value, 'uz') ?? ''

/** GET /api/site/slides?lang= — hozir ko'rsatiladigan slaydlar (bosh sahifa va xodim sahifalari pastida) */
const slides: Endpoint = {
  path: '/site/slides',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const now = new Date().toISOString()
    const res = await req.payload.find({
      collection: 'slides',
      where: {
        and: [
          { or: [{ startsAt: { exists: false } }, { startsAt: { less_than_equal: now } }] },
          { or: [{ endsAt: { exists: false } }, { endsAt: { greater_than: now } }] },
        ],
      },
      sort: 'order',
      limit: 50,
      depth: 1,
      overrideAccess: true,
    })
    return json(res.docs.map((d: Doc) => ({
      id: String(d.id),
      image: imageOf(d.image, 'hero'),
      alt: tr(d.alt, lang),
      link: d.link || null,
    })).filter(s => s.image))
  },
}

const leaderOf = (d: Doc, lang: Lang) => ({
  staffId: d.staffId || null,
  name: d.name,
  role: tr(d.role, lang),
  photo: imageOf(d.photo, 'thumb'),
  hours: pick(d.hours, lang) ?? pick(d.hours, 'uz'),
  phone: d.phone || null,
  ext: d.ext || null,
  email: d.email || null,
})

/** GET /api/site/leadership?lang= — rektorat (+ virtual qabulxona uchun "Kimga" ro'yxati) */
const leadership: Endpoint = {
  path: '/site/leadership',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const res = await req.payload.find({ collection: 'leaders', sort: 'order', limit: 100, depth: 1, overrideAccess: true })
    const docs = res.docs as Doc[]
    const rector = docs.find(d => d.kind === 'rector')
    const press = docs.find(d => d.kind === 'press')
    return json({
      rector: rector ? leaderOf(rector, lang) : null,
      prorectors: docs.filter(d => d.kind === 'prorector').map(d => leaderOf(d, lang)),
      press: press ? leaderOf(press, lang) : null,
      recipients: docs.filter(d => d.reception).map(d => ({ id: `leader-${d.id}`, title: tr(d.role, lang) })),
    })
  },
}

/** GET /api/site/documents?lang=&page= — me'yoriy hujjatlar (page berilsa — faqat shu sahifaga biriktirilganlari) */
const documents: Endpoint = {
  path: '/site/documents',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const page = req.searchParams.get('page')
    const [cats, docs] = await Promise.all([
      req.payload.find({ collection: 'doc-categories', sort: 'order', limit: 200, depth: 0, overrideAccess: true }),
      req.payload.find({ collection: 'documents', where: page ? { pages: { contains: page } } : undefined, sort: 'order', limit: 1000, depth: 1, overrideAccess: true }),
    ])
    const base = (process.env.PUBLIC_SERVER_URL ?? '').replace(/\/$/, '')
    return json({
      categories: cats.docs.map((c: Doc) => ({ id: String(c.id), title: tr(c.title, lang) })),
      items: (docs.docs as Doc[]).map((d) => {
        const file: MediaDoc = d.files?.[lang] && typeof d.files[lang] === 'object' ? d.files[lang] : d.files?.uz
        const isFile = !!(file && typeof file === 'object')
        return {
          id: String(d.id),
          category: String(typeof d.category === 'object' ? d.category?.id : d.category),
          title: tr(d.title, lang),
          // PDF manzili o'zgarmaydi: yangi versiya yuklansa ham shu havola yangisini beradi
          url: isFile ? `${base}/api/site/documents/${d.id}/file?lang=${lang}` : d.url || '',
          kind: isFile ? 'pdf' : 'link',
          meta: [d.number, isFile ? ['PDF', sizeLabel(file?.filesize)].filter(Boolean).join(' · ') : null].filter(Boolean).join(' · ') || null,
          display: isFile ? d.display ?? 'open' : null,
          height: isFile && d.display === 'embed' ? d.height ?? 680 : null,
        }
      }).filter(d => d.url),
    })
  },
}

/** GET /api/site/documents/:id/file?lang= — hujjat fayli (yuklab olishlar soni oshadi) */
const documentFile: Endpoint = {
  path: '/site/documents/:id/file',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const id = Number(req.routeParams?.id)
    if (!Number.isInteger(id)) return json({ message: 'Not found' }, 404)
    const doc = await req.payload.findByID({ collection: 'documents', id, depth: 1, overrideAccess: true, disableErrors: true }) as Doc | null
    const url = doc && (fileOf(doc.files?.[lang]) ?? fileOf(doc.files?.uz))
    if (!doc || !url) return json({ message: 'Not found' }, 404)
    await req.payload.update({ collection: 'documents', id, data: { downloads: (doc.downloads ?? 0) + 1 }, overrideAccess: true, context: { silent: true } }).catch(() => {})
    await recordHit(req, { kind: 'event', name: 'PDF yuklab olindi', value: String(id), lang }).catch(() => {})
    return Response.redirect(url, 302)
  },
}

/** GET /api/site/videos?lang= — video darsliklar va jonli efir */
const videos: Endpoint = {
  path: '/site/videos',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const [page, cats, items] = await Promise.all([
      req.payload.findGlobal({ slug: 'video-page', depth: 0, overrideAccess: true }) as Promise<Doc>,
      req.payload.find({ collection: 'video-categories', sort: 'order', limit: 100, depth: 0, overrideAccess: true }),
      req.payload.find({ collection: 'videos', sort: 'order', limit: 1000, depth: 1, overrideAccess: true }),
    ])
    const channelUrl = page.channelUrl || 'https://www.youtube.com'
    const nextTitle = pick(page.nextTitle, lang) ?? pick(page.nextTitle, 'uz')
    return json({
      live: {
        isLive: !!page.live,
        url: page.liveUrl || `${channelUrl.replace(/\/$/, '')}/live`,
        next: page.nextAt && new Date(page.nextAt).getTime() > Date.now() ? { title: nextTitle ?? '', startsAt: page.nextAt } : null,
      },
      channelUrl,
      categories: cats.docs.map((c: Doc) => ({ id: c.key, title: tr(c.title, lang), greeting: c.greeting ?? '', lang: c.key })),
      items: (items.docs as Doc[]).filter(v => v.category && typeof v.category === 'object').map(v => ({
        id: String(v.id),
        category: v.category.key,
        title: tr(v.title, lang),
        teacher: v.teacher || null,
        duration: v.duration || null,
        url: v.url,
        thumbnail: v.thumbnail || null,
      })),
    })
  },
}

/** GET /api/site/symbols?lang= — davlat ramzlari (gerb, bayroq, madhiya) */
const symbols: Endpoint = {
  path: '/site/symbols',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const g = await req.payload.findGlobal({ slug: 'symbols', depth: 1, overrideAccess: true }) as Doc
    return json((['flag', 'emblem', 'anthem'] as const).map(key => ({
      key,
      title: tr(g[key]?.title, lang),
      description: pick(g[key]?.description, lang) ?? pick(g[key]?.description, 'uz'),
      image: imageOf(g[key]?.image, 'thumb'),
      audio: key === 'anthem' ? fileOf(g[key]?.audio) : null,
      href: g[key]?.link || null,
      source: g[key]?.source || null,
    })))
  },
}

export const contentEndpoints: Endpoint[] = [slides, leadership, documents, documentFile, videos, symbols]
