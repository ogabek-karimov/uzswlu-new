import type { Endpoint } from 'payload'
import { isEditor } from '../lib/access'
import { type I18n, type Lang, pick } from '../lib/i18n'
import { fileOf, imageOf, json, langOf, sizeLabel } from '../lib/public'

// BRM sahifalari uchun ochiq API va admin panel uchun postlar soni

type Doc = Record<string, any>
const tr = (value: I18n | null | undefined, lang: Lang) => pick(value, lang) ?? pick(value, 'uz') ?? ''

const summaryOf = (g: Doc, lang: Lang) => ({ n: g.n, url: g.url, title: tr(g.title, lang), rank: g.impactRank || null, score: g.impactScore || null })

/** GET /api/site/sdg-goals?lang= — 17 maqsad (BRM bosh sahifasidagi g'ildirak va jadval) */
const goals: Endpoint = {
  path: '/site/sdg-goals',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const [res, page] = await Promise.all([
      req.payload.find({ collection: 'sdg-goals', sort: 'n', limit: 17, depth: 0, overrideAccess: true, select: { n: true, url: true, title: true, impactRank: true, impactScore: true } }),
      req.payload.findGlobal({ slug: 'sdg-page', overrideAccess: true }) as Promise<Doc>,
    ])
    return json({ impactYear: page.impactYear ?? null, goals: (res.docs as Doc[]).map(g => summaryOf(g, lang)) })
  },
}

/** GET /api/site/sdg/:n?lang= — maqsad sahifasi (faoliyat — /site/posts?sdg=n) */
const goal: Endpoint = {
  path: '/site/sdg/:n',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const n = Number(req.routeParams?.n)
    const res = await req.payload.find({ collection: 'sdg-goals', where: { n: { equals: n } }, limit: 1, depth: 1, overrideAccess: true })
    const g = res.docs[0] as Doc | undefined
    if (!g) return json({ message: 'Not found' }, 404)
    const value = g.highlight?.value ? pick(g.highlight.value, lang) ?? pick(g.highlight.value, 'uz') : null
    return json({
      ...summaryOf(g, lang),
      subtitle: tr(g.subtitle, lang),
      highlight: g.highlight?.label && value ? { label: g.highlight.label, value } : null,
      sections: (g.sections ?? []).map((s: Doc, i: number) => ({
        id: s.key || `s${i + 1}`,
        title: tr(s.title, lang),
        body: pick(s.body, lang) ?? pick(s.body, 'uz') ?? '',
        images: (s.images ?? []).map((m: Doc) => imageOf(m, 'card')).filter(Boolean),
      })),
      documents: (g.reports ?? []).map((r: Doc) => {
        const file = r.file && typeof r.file === 'object' ? r.file : null
        const url = fileOf(file) ?? r.url
        if (!url) return null
        return {
          title: tr(r.title, lang) || file?.filename || '',
          url,
          kind: file ? 'pdf' : 'link',
          meta: [r.meta, file ? ['PDF', sizeLabel(file.filesize)].filter(Boolean).join(' · ') : null].filter(Boolean).join(' · ') || null,
          display: file ? r.display ?? 'open' : null,
          height: file && r.display === 'embed' ? r.height ?? 680 : null,
        }
      }).filter(Boolean),
    })
  },
}

/** GET /api/panel/sdg-counts — har bir maqsadga bog'langan postlar soni */
const counts: Endpoint = {
  path: '/panel/sdg-counts',
  method: 'get',
  handler: async (req) => {
    if (!isEditor(req.user as never)) return json({ message: 'Unauthorized' }, 401)
    const res = await req.payload.find({ collection: 'posts', where: { sdg: { greater_than: 0 } }, pagination: false, depth: 0, overrideAccess: true, select: { sdg: true } })
    const out: Record<number, number> = {}
    for (const p of res.docs as Doc[]) out[p.sdg] = (out[p.sdg] ?? 0) + 1
    return json(out)
  },
}

export const sdgEndpoints: Endpoint[] = [goals, goal, counts]
