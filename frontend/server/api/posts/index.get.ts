import type { PostList, PostType } from '#shared/types/api'

const TYPES: PostType[] = ['news', 'announcements', 'events']

// Yangiliklar / e'lonlar / tadbirlar ro'yxati: tur, qidiruv, oy, BRM maqsadi va sahifa bo'yicha.
export default defineCachedEventHandler(
  async (event): Promise<PostList> => {
    const query = readPostQuery(event)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    if (cmsBase) return cmsFetch<PostList>(event, '/posts', query)
    if (!apiBase) return getMockPostList(query.lang, query)

    return backendFetch<PostList>(event, '/posts', query)
  },
  {
    maxAge: 60,
    getKey: (event) => {
      const q = readPostQuery(event)
      return `posts:${q.lang}:${q.type}:${q.month ?? ''}:${q.sdg ?? ''}:${q.page}:${q.perPage}:${q.q ?? ''}`
    },
    shouldBypassCache: () => import.meta.dev,
  },
)

function readPostQuery(event: Parameters<typeof getQuery>[0]) {
  const raw = getQuery(event)
  const int = (v: unknown, fallback: number, max: number) => Math.min(max, Math.max(1, Number.parseInt(String(v), 10) || fallback))
  const q = typeof raw.q === 'string' && raw.q.trim() ? raw.q.trim().slice(0, 100) : undefined
  const month = typeof raw.month === 'string' && /^\d{4}-(0[1-9]|1[0-2])$/.test(raw.month) ? raw.month : undefined
  const sdg = Number.parseInt(String(raw.sdg), 10)

  return {
    lang: normalizeLocale(raw.lang),
    type: TYPES.includes(raw.type as PostType) ? (raw.type as PostType) : 'news',
    q,
    month,
    sdg: sdg >= 1 && sdg <= 17 ? sdg : undefined,
    page: int(raw.page, 1, 10_000),
    perPage: int(raw.perPage, 12, 48),
  }
}
