import type { Payload } from 'payload'
import data from './pages-seed.json' with { type: 'json' }

// Sahifalar daraxti — saytdagi hozirgi menyudan (bo'limlar, tartib va manzillar o'zgarmaydi)
type L = { uz: string; ru: string; en: string; zh: string }
type Link = { t: L; url: string; file?: 'pdf'; highlight?: boolean; sdg?: number }
type Group = { id: string; t: L; d?: L; url?: string; overview?: string; links: Link[] }
type Content = { lead?: L; body: L; facts?: [string, L][]; timeline?: [L, L, boolean?][]; attachments?: { title: L; url: string; meta: L }[] }

// Saytda o'z sahifasi (Nuxt) bor bo'limlar — mazmuni admin panelning boshqa bo'limida
const SPECIAL = /^\/(aloqa|bakalavriat|brm|brm-[\w-]+|fakultetlar-va-kafedralar|magistratura|meyoriy-hujjatlar|qabul-20262027|rektorat|staff|video-darsliklar|yangiliklar|news|announcements|events)$/

export async function seedPages(payload: Payload) {
  if ((await payload.count({ collection: 'pages', overrideAccess: true })).totalDocs) return
  const ctx = { seed: true }
  const contents = data.pages as Record<string, Content>
  const sample = data.sample as L
  const seen = new Set<string>()
  for (const [gi, g] of (data.menu as Group[]).entries()) {
    const group = await payload.create({
      collection: 'pages', overrideAccess: true, context: ctx,
      data: { template: 'group', title: g.t, groupKey: g.id, description: g.d, url: g.url, overview: g.overview, order: gi + 1 },
    })
    for (const [li, l] of g.links.entries()) {
      const external = /^https?:/.test(l.url)
      const slug = l.url.replace(/^\//, '')
      const base = { title: l.t, parent: group.id, order: li + 1, highlight: !!l.highlight, sdg: l.sdg ?? undefined }
      let page: Record<string, unknown>
      if (external) page = { ...base, template: 'link', url: l.url }
      else if (SPECIAL.test(l.url) || seen.has(slug)) page = { ...base, template: 'special', url: l.url }
      else {
        seen.add(slug)
        const c = contents[slug]
        page = {
          ...base, template: 'text', slug,
          lead: c?.lead, body: c?.body ?? sample,
          facts: c?.facts?.map(([value, label]) => ({ value, label })),
          timeline: c?.timeline?.map(([label, text, highlight]) => ({ label, text, highlight: !!highlight })),
          attachments: c?.attachments?.map(a => ({ url: a.url, title: a.title, meta: a.meta, display: 'open' })),
        }
      }
      await payload.create({ collection: 'pages', overrideAccess: true, context: ctx, data: page as never })
    }
  }
  payload.logger.info('Sahifalar daraxti yuklandi')
}
