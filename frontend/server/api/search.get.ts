import type { SearchKind, SearchResults } from '#shared/types/api'
import type { PostIndexItem } from '../utils/mock-search'

const KINDS: SearchKind[] = ['pages', 'news', 'documents']

// Sayt bo'yicha qidiruv. Natijalar keshlanmaydi (so'rovlar har xil).
export default defineEventHandler(async (event): Promise<SearchResults> => {
  const raw = getQuery(event)
  const lang = normalizeLocale(raw.lang)
  const q = typeof raw.q === 'string' ? raw.q.trim().slice(0, 100) : ''
  const type = KINDS.includes(raw.type as SearchKind) ? (raw.type as SearchKind) : undefined
  const page = Math.min(500, Math.max(1, Number.parseInt(String(raw.page), 10) || 1))
  const perPage = 10

  if (!q) return { q, counts: { pages: 0, news: 0, documents: 0 }, quick: null, items: [], total: 0, page, perPage }

  const { apiBase, cmsBase } = useRuntimeConfig(event)
  if (!apiBase) {
    // Postlar CMS'dan (berilgan bo'lsa), sahifa va hujjatlar hozircha mock'dan
    const posts = cmsBase ? await cmsFetch<PostIndexItem[]>(event, '/index', { lang }) : undefined
    return getMockSearch(lang, { q, type, page, perPage }, posts)
  }

  return backendFetch<SearchResults>(event, '/search', { lang, q, type, page, perPage })
})
