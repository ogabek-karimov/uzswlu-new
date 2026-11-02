import type { Endpoint } from 'payload'
import { type I18n, type Lang, pick } from '../lib/i18n'
import { fileOf, json, langOf, sizeLabel } from '../lib/public'

// Sayt menyusi va matnli sahifalar — admin paneldagi "Sahifalar" daraxtidan

type Doc = Record<string, any>
const tr = (value: I18n | null | undefined, lang: Lang) => pick(value, lang) ?? pick(value, 'uz') ?? ''
const idOf = (v: unknown) => (v && typeof v === 'object' ? (v as Doc).id : v)

/** Sahifaning saytdagi manzili */
export function pageUrl(p: Doc): string {
  if (p.template === 'text') return `/${p.slug}`
  if (p.template === 'link') return fileOf(p.file) ?? p.url ?? '#'
  return p.url ?? (p.slug ? `/${p.slug}` : '#')
}

/** GET /api/site/menu?lang= — asosiy menyu (bo'limlar va ularning sahifalari, ichma-ich sahifalar ham) */
const menu: Endpoint = {
  path: '/site/menu',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const res = await req.payload.find({ collection: 'pages', where: { and: [{ published: { equals: true } }, { inMenu: { equals: true } }] }, sort: 'order', pagination: false, depth: 1, overrideAccess: true })
    const all = res.docs as Doc[]
    const kids = (id: unknown) => all.filter(p => idOf(p.parent) === id)
    const flatten = (id: unknown): Doc[] => kids(id).flatMap(p => [p, ...flatten(p.id)])
    return json(all.filter(p => !p.parent && p.template === 'group').map(g => ({
      id: g.groupKey || g.slug || String(g.id),
      title: tr(g.title, lang),
      description: pick(g.description, lang) ?? pick(g.description, 'uz'),
      url: g.url || null,
      overview: g.overview || null,
      links: flatten(g.id).filter(p => p.template !== 'group').map((p) => {
        const url = pageUrl(p)
        return {
          title: tr(p.title, lang),
          url,
          file: (p.template === 'link' && (fileOf(p.file) || /\.pdf($|\?)/i.test(url))) ? 'pdf' : null,
          highlight: !!p.highlight,
          sdg: p.sdg || null,
        }
      }),
    })))
  },
}

/** GET /api/site/pages/:slug?lang= — matnli sahifa */
const page: Endpoint = {
  path: '/site/pages/:slug',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const res = await req.payload.find({
      collection: 'pages',
      where: { and: [{ slug: { equals: String(req.routeParams?.slug ?? '') } }, { template: { equals: 'text' } }, { published: { equals: true } }] },
      limit: 1, depth: 1, overrideAccess: true,
    })
    const p = res.docs[0] as Doc | undefined
    if (!p) return json({ message: 'Not found' }, 404)
    return json({
      slug: p.slug,
      title: tr(p.title, lang),
      lead: pick(p.lead, lang) ?? pick(p.lead, 'uz'),
      facts: (p.facts ?? []).map((f: Doc) => ({ value: f.value, label: tr(f.label, lang) })),
      body: (pick(p.body, lang) ?? pick(p.body, 'uz') ?? '').replace(/<p>\s*\[\[timeline\]\]\s*<\/p>/g, '<!-- timeline -->'),
      timeline: (p.timeline ?? []).map((t: Doc) => ({ label: tr(t.label, lang), text: tr(t.text, lang), highlight: !!t.highlight })),
      attachments: (p.attachments ?? []).map((a: Doc) => {
        const file = a.file && typeof a.file === 'object' ? a.file : null
        const url = fileOf(file) ?? a.url
        if (!url) return null
        const isPdf = !!file || /\.pdf($|\?)/i.test(url)
        return {
          title: tr(a.title, lang) || file?.filename || '',
          url,
          kind: isPdf ? 'pdf' : 'link',
          meta: pick(a.meta, lang) ?? pick(a.meta, 'uz') ?? (file ? ['PDF', sizeLabel(file.filesize)].filter(Boolean).join(' · ') : null),
          display: file ? a.display ?? 'open' : null,
          height: file && a.display === 'embed' ? a.height ?? 680 : null,
        }
      }).filter(Boolean),
      updatedAt: p.updatedAt,
    })
  },
}

export const pageEndpoints: Endpoint[] = [menu, page]
