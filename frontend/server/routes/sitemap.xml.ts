import type { FacultyList, PostList, PostType, SiteData, StaffList } from '#shared/types/api'
import { buildSitemapXml, menuPaths, prefixedPath, type SitemapEntry } from '#shared/utils/seo'

// sitemap.xml (XML yig‘ish — shared/utils/seo.ts): 4 tilning hammasi uchun statik sahifalar (menyudan), fakultetlar, yangilik/e'lon/tadbirlar, xodimlar.
// Ma'lumot saytning o'z `/api/*` marshrutlaridan olinadi (ular keshlangan; backend o'chsa — oxirgi yaxshi nusxa).
// Natija 1 soat keshlanadi. Bir manba xato bersa, qolganlari baribir chiqadi.

const POST_TYPES: PostType[] = ['news', 'announcements', 'events']
const MAX_PAGES = 40 // har bir ro'yxat uchun xavfsizlik chegarasi (40 × 48)
const FIXED = ['/', '/yangiliklar', '/events', '/fakultetlar-va-kafedralar', '/staff', '/rektorat', '/aloqa', '/video-darsliklar', '/brm', '/bakalavriat', '/magistratura']

interface Entry { path: string; lastmod?: string }

const isoDay = (v?: string | null) => (v && /^\d{4}-\d{2}-\d{2}/.test(v) ? v.slice(0, 10) : undefined)

async function allPages<T extends { items: unknown[]; total: number }>(load: (page: number) => Promise<T>): Promise<T['items']> {
  const items: T['items'] = []
  for (let page = 1; page <= MAX_PAGES; page++) {
    const res = await load(page)
    items.push(...res.items)
    if (!res.items.length || items.length >= res.total) break
  }
  return items
}

async function collect(lang: string): Promise<Entry[]> {
  const q = (query: Record<string, unknown> = {}) => ({ query: { lang, ...query } })
  const safe = <T>(p: Promise<T>, fallback: T) => p.catch((e) => { console.error(`[sitemap] ${lang}: ${(e as Error).message}`); return fallback })

  const [site, faculties] = await Promise.all([
    safe($fetch<SiteData>('/api/site', q()), null),
    safe($fetch<FacultyList>('/api/faculties', q()), null),
  ])
  const entries: Entry[] = [...FIXED, ...(site ? menuPaths(site.menu) : [])].map(path => ({ path }))
  for (const f of faculties?.items ?? []) entries.push({ path: `/faculty/${f.slug}` })

  for (const type of POST_TYPES) {
    const posts = await safe(allPages<PostList>(page => $fetch<PostList>('/api/posts', q({ type, page, perPage: 48 }))), [])
    for (const p of posts as PostList['items']) {
      entries.push({ path: `/${type}/${p.slug}`, lastmod: isoDay(p.date ?? (p as { startsAt?: string }).startsAt) })
    }
  }

  // Xodimlar tilga bog'liq emas (ismlar HEMIS'dan) — faqat o'zbekcha ro'yxatda ko'rsatamiz, hajm oshib ketmasin
  if (lang === 'uz') {
    const staff = await safe(allPages<StaffList>(page => $fetch<StaffList>('/api/staff', q({ page, perPage: 48 }))), [])
    for (const s of staff as StaffList['items']) entries.push({ path: `/teacher/${s.id}` })
  }
  return entries
}

export default defineCachedEventHandler(
  async (event) => {
    const origin = siteOrigin(event)
    const entries: SitemapEntry[] = []
    for (const lang of LOCALES) {
      for (const e of await collect(lang)) entries.push({ loc: origin + prefixedPath(lang, e.path), lastmod: e.lastmod })
    }
    setResponseHeader(event, 'content-type', 'application/xml; charset=utf-8')
    return buildSitemapXml(entries)
  },
  {
    maxAge: 60 * 60,
    swr: true,
    // Domen so'rovdan olinishi mumkin — kesh kalitiga kiradi
    getKey: event => `sitemap:${siteOrigin(event)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
