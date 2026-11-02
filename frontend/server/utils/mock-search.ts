import type { SearchKind, SearchResults } from '#shared/types/api'

// VAQTINCHALIK — qidiruv mock ma'lumotlar ustida (menyu sahifalari, postlar, hujjatlar).
// Haqiqiy qidiruvni backend qiladi (to'liq matn bo'yicha).

const fold = (v: string) => v.toLocaleLowerCase().replace(/[‘’ʻʼ`']/g, '\'')

/** Qidiruv uchun post (CMS'dan yoki mock'dan) */
export type PostIndexItem = { type: string; slug: string; title: string; text: string; category: string; date: string }

export function getMockSearch(lang: Locale, query: { q: string; type?: SearchKind; page: number; perPage: number }, postIndex?: PostIndexItem[]): SearchResults {
  const terms = fold(query.q).split(/\s+/).filter(Boolean)
  const match = (...texts: (string | null | undefined)[]) => {
    const hay = fold(texts.filter(Boolean).join(' '))
    return terms.length > 0 && terms.every(t => hay.includes(t))
  }

  const pages = getMockMenu(lang).flatMap(g => g.links.map(l => ({ ...l, group: g.title })))
    .filter(l => !l.file && l.url.startsWith('/') && match(l.title))
    .map(l => ({ kind: 'pages' as const, title: l.title, url: l.url, excerpt: null, meta: l.group, date: null }))

  const news = (postIndex ?? getMockPostIndex(lang))
    .filter(p => match(p.title, p.text))
    .map(p => ({ kind: 'news' as const, title: p.title, url: `/${p.type}/${p.slug}`, excerpt: p.text || null, meta: p.category, date: p.date }))

  const documents = getMockDocuments(lang).items
    .filter(d => match(d.title))
    .map(d => ({ kind: 'documents' as const, title: d.title, url: d.url, excerpt: null, meta: d.kind === 'pdf' ? 'PDF' : 'URL', date: null }))

  const all = { pages, news, documents }
  const list = query.type ? all[query.type] : [...pages, ...news, ...documents]
  const start = (query.page - 1) * query.perPage
  const quick = pages[0]

  return {
    q: query.q,
    counts: { pages: pages.length, news: news.length, documents: documents.length },
    quick: quick ? { title: quick.title, text: quick.meta, url: quick.url } : null,
    items: list.slice(start, start + query.perPage),
    total: list.length,
    page: query.page,
    perPage: query.perPage,
  }
}
