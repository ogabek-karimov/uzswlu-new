import type { Endpoint, Where } from 'payload'
import { textOf } from '../lib/html'
import { type Lang, pick } from '../lib/i18n'
import { imageOf, json, langOf, type MediaDoc, publicUrl } from '../lib/public'

// Sayt (Nuxt) uchun ochiq API — shared/types/api.ts dagi shartnoma bo'yicha.
// Faqat nashr qilingan, yashirilmagan va vaqti kelgan postlar.

type PostType = 'news' | 'announcements' | 'events'
const TYPES: PostType[] = ['news', 'announcements', 'events']

type Doc = Record<string, any>

export function visibleWhere(lang: Lang, extra: Where[] = []): Where {
  return {
    and: [
      { status: { equals: 'published' } },
      { hidden: { not_equals: true } },
      { publishedAt: { less_than_equal: new Date().toISOString() } },
      { [`title.${lang}`]: { exists: true } },
      { [`title.${lang}`]: { not_equals: '' } },
      ...extra,
    ],
  }
}

function coverFor(doc: Doc, lang: Lang, size: 'card' | 'hero' = 'card') {
  const own = lang !== 'uz' ? doc.coverByLang?.[lang] : null
  return imageOf(own && typeof own === 'object' ? own : doc.cover, size)
}

export function summary(doc: Doc, lang: Lang) {
  return {
    id: String(doc.id),
    slug: doc.slug,
    type: doc.type as PostType,
    title: pick(doc.title, lang) ?? '',
    category: pick(doc.category?.name, lang) ?? '',
    date: doc.type === 'events' && doc.startsAt ? doc.startsAt : doc.publishedAt,
    image: coverFor(doc, lang),
    excerpt: pick(doc.excerpt, lang),
  }
}

function eventItem(doc: Doc, lang: Lang) {
  return {
    id: String(doc.id),
    slug: doc.slug,
    title: pick(doc.title, lang) ?? '',
    category: pick(doc.category?.name, lang) ?? '',
    startsAt: doc.startsAt ?? doc.publishedAt,
    endsAt: doc.endsAt ?? null,
    location: pick(doc.location, lang) ?? '',
    image: coverFor(doc, lang),
  }
}

/** GET /api/site/posts?lang=&type=&q=&month=&sdg=&page=&perPage= */
const list: Endpoint = {
  path: '/site/posts',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const sp = req.searchParams
    const type = (TYPES.includes(sp.get('type') as PostType) ? sp.get('type') : 'news') as PostType
    const page = Math.max(1, Number(sp.get('page')) || 1)
    const perPage = Math.min(48, Math.max(1, Number(sp.get('perPage')) || 12))
    const q = sp.get('q')?.trim().slice(0, 100)
    const month = sp.get('month')
    const sdg = Number(sp.get('sdg'))

    const filters: Where[] = []
    if (q) filters.push({ [`title.${lang}`]: { like: q } })
    if (sdg >= 1 && sdg <= 17) filters.push({ sdg: { equals: sdg } })
    if (month && /^\d{4}-\d{2}$/.test(month)) {
      const start = new Date(`${month}-01T00:00:00+05:00`)
      const end = new Date(start)
      end.setMonth(end.getMonth() + 1)
      filters.push({ publishedAt: { greater_than_equal: start.toISOString() } }, { publishedAt: { less_than: end.toISOString() } })
    }

    const base = visibleWhere(lang, filters)
    const [result, ...counts] = await Promise.all([
      req.payload.find({ collection: 'posts', where: { and: [base, { type: { equals: type } }] }, sort: '-publishedAt', page, limit: perPage, depth: 1, overrideAccess: true }),
      ...TYPES.map(t => req.payload.count({ collection: 'posts', where: { and: [base, { type: { equals: t } }] }, overrideAccess: true })),
    ])
    const monthsSrc = await req.payload.find({
      collection: 'posts',
      where: { and: [visibleWhere(lang), { type: { equals: type } }] },
      select: { publishedAt: true },
      limit: 2000,
      pagination: false,
      overrideAccess: true,
    })
    const months = [...new Set(monthsSrc.docs.map(d => String(d.publishedAt ?? '').slice(0, 7)).filter(Boolean))].sort().reverse()

    return json({
      items: result.docs.map(d => summary(d, lang)),
      total: result.totalDocs,
      page: result.page ?? page,
      perPage,
      counts: { news: counts[0]!.totalDocs, announcements: counts[1]!.totalDocs, events: counts[2]!.totalDocs },
      months,
    })
  },
}

/** GET /api/site/posts/:type/:slug?lang= */
const one: Endpoint = {
  path: '/site/posts/:type/:slug',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const type = req.routeParams?.type as PostType
    const slug = String(req.routeParams?.slug ?? '')
    if (!TYPES.includes(type)) return json({ message: 'Not found' }, 404)

    const found = await req.payload.find({
      collection: 'posts',
      where: visibleWhere(lang, [{ type: { equals: type } }, { slug: { equals: slug } }]),
      limit: 1,
      depth: 2,
      overrideAccess: true,
    })
    const doc = found.docs[0]
    if (!doc) return json({ message: 'Not found' }, 404)

    const body = pick(doc.body, lang) ?? ''
    const words = textOf(body).split(' ').filter(Boolean).length
    const chars = textOf(body).length
    const readingMinutes = Math.max(1, Math.round(lang === 'zh' ? chars / 400 : words / 180))
    const author = doc.author && typeof doc.author === 'object'
      ? { name: doc.author.name, role: doc.author.position ?? null, avatar: imageOf(doc.author.avatar, 'thumb') }
      : null

    const [related, latest] = await Promise.all([
      req.payload.find({ collection: 'posts', where: visibleWhere(lang, [{ type: { equals: type } }, { id: { not_equals: doc.id } }]), sort: '-publishedAt', limit: 3, depth: 1, overrideAccess: true }),
      req.payload.find({ collection: 'posts', where: visibleWhere(lang, [{ type: { equals: 'news' } }, { id: { not_equals: doc.id } }]), sort: '-publishedAt', limit: 4, depth: 1, overrideAccess: true }),
    ])

    return json({
      ...summary(doc, lang),
      image: coverFor(doc, lang, 'hero'),
      body,
      author,
      publishedAt: doc.publishedAt,
      gallery: (doc.gallery ?? []).map((m: MediaDoc | number) => imageOf(m, 'hero')).filter(Boolean),
      tags: doc.tags?.[lang] ?? [],
      readingMinutes,
      startsAt: doc.type === 'events' ? doc.startsAt ?? null : null,
      endsAt: doc.type === 'events' ? doc.endsAt ?? null : null,
      location: pick(doc.location, lang),
      attachments: (doc.attachments ?? []).filter((a: Doc) => a.file && typeof a.file === 'object').map((a: Doc) => ({
        title: pick(a.title, lang) ?? a.file.filename,
        url: publicUrl(a.file.url),
        kind: 'pdf',
        meta: !a.file.filesize ? 'PDF'
          : a.file.filesize < 1024 * 1024 ? `PDF · ${Math.max(1, Math.round(a.file.filesize / 1024))} KB`
            : `PDF · ${(a.file.filesize / 1024 / 1024).toFixed(1).replace('.', ',')} MB`,
        display: a.display ?? 'open',
        height: a.height ?? 680,
      })),
      related: related.docs.map(d => summary(d, lang)),
      latest: latest.docs.map(d => summary(d, lang)),
    })
  },
}

/** GET /api/site/latest?lang= — bosh sahifa uchun so'nggi postlar */
const latest: Endpoint = {
  path: '/site/latest',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const now = new Date().toISOString()
    const [news, announcements, events] = await Promise.all([
      req.payload.find({ collection: 'posts', where: visibleWhere(lang, [{ type: { equals: 'news' } }]), sort: '-publishedAt', limit: 4, depth: 1, overrideAccess: true }),
      req.payload.find({ collection: 'posts', where: visibleWhere(lang, [{ type: { equals: 'announcements' } }]), sort: '-publishedAt', limit: 5, depth: 1, overrideAccess: true }),
      req.payload.find({ collection: 'posts', where: visibleWhere(lang, [{ type: { equals: 'events' } }, { startsAt: { greater_than_equal: now } }]), sort: 'startsAt', limit: 3, depth: 1, overrideAccess: true }),
    ])
    return json({
      news: news.docs.map(d => { const s = summary(d, lang); return { id: s.id, slug: s.slug, title: s.title, category: s.category, date: s.date, image: s.image } }),
      announcements: announcements.docs.map(d => ({ id: String(d.id), slug: d.slug, title: pick(d.title, lang) ?? '', date: d.publishedAt })),
      events: events.docs.map(d => eventItem(d, lang)),
    })
  },
}

/** GET /api/site/events?lang=&month=YYYY-MM — tadbirlar taqvimi (bitta oy) */
const events: Endpoint = {
  path: '/site/events',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const raw = req.searchParams.get('month') ?? ''
    const month = /^\d{4}-(0[1-9]|1[0-2])$/.test(raw) ? raw : new Date(Date.now() + 5 * 3600 * 1000).toISOString().slice(0, 7)
    const start = new Date(`${month}-01T00:00:00+05:00`)
    const end = new Date(start)
    end.setMonth(end.getMonth() + 1)
    const [inMonth, upcoming] = await Promise.all([
      req.payload.find({
        collection: 'posts',
        where: visibleWhere(lang, [{ type: { equals: 'events' } }, { startsAt: { greater_than_equal: start.toISOString() } }, { startsAt: { less_than: end.toISOString() } }]),
        sort: 'startsAt',
        limit: 200,
        depth: 1,
        overrideAccess: true,
      }),
      req.payload.find({
        collection: 'posts',
        where: visibleWhere(lang, [{ type: { equals: 'events' } }, { startsAt: { greater_than_equal: new Date().toISOString() } }]),
        sort: 'startsAt',
        limit: 3,
        depth: 1,
        overrideAccess: true,
      }),
    ])
    return json({ month, items: inMonth.docs.map(d => eventItem(d, lang)), upcoming: upcoming.docs.map(d => eventItem(d, lang)) })
  },
}

/** GET /api/site/index?lang= — qidiruv uchun barcha ko'rinadigan postlar (yengil ro'yxat) */
const index: Endpoint = {
  path: '/site/index',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const res = await req.payload.find({
      collection: 'posts',
      where: visibleWhere(lang),
      sort: '-publishedAt',
      limit: 1000,
      pagination: false,
      depth: 1,
      select: { type: true, slug: true, title: true, excerpt: true, category: true, publishedAt: true },
      overrideAccess: true,
    })
    return json(res.docs.map(d => ({
      type: d.type,
      slug: d.slug,
      title: pick(d.title, lang) ?? '',
      text: pick(d.excerpt, lang) ?? '',
      category: pick((d.category as Doc | null)?.name, lang) ?? '',
      date: d.publishedAt,
    })))
  },
}

/** GET /api/site/settings — saytga kerakli ochiq sozlamalar */
const settings: Endpoint = {
  path: '/site/settings',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const s = await req.payload.findGlobal({ slug: 'settings', overrideAccess: true }) as Doc
    return json({
      support: {
        url: s.support?.telegram ?? null,
        text: pick(s.support?.text, lang),
        showOnSite: !!s.support?.showOnSite,
        pages: s.support?.pages ?? [],
        place: s.support?.place ?? 'float',
      },
      contact: { phone: s.contact?.phone ?? null, email: s.contact?.email ?? null, address: pick(s.contact?.address, lang) },
    })
  },
}

export const siteEndpoints: Endpoint[] = [list, one, latest, events, index, settings]
