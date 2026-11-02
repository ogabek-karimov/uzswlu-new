import type { PostList, SdgOverview } from '#shared/types/api'

// BRM bosh sahifasi: GreenMetric, THE Impact natijalari, hisobotlar, yashil universitet yangiliklari.
export default defineCachedEventHandler(
  async (event): Promise<SdgOverview> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    const overview = apiBase ? await backendFetch<SdgOverview>(event, '/sdg', { lang }) : getMockSdgOverview(lang)
    if (!cmsBase) return overview

    // 17 maqsad nomlari va THE Impact natijalari — admin paneldagi BRM bo'limidan; yashil universitet yangiliklari — CMS'dan
    const [cms, news] = await Promise.all([
      cmsFetch<{ impactYear: number | null; goals: SdgOverview['goals'] }>(event, '/sdg-goals', { lang }).catch(() => null),
      cmsFetch<PostList>(event, '/posts', { lang, type: 'news', sdg: 13, perPage: 3 }).then(r => r.items).catch(() => overview.news),
    ])
    return { ...overview, goals: cms?.goals.length ? cms.goals : overview.goals, impactYear: cms?.impactYear ?? overview.impactYear, news }
  },
  {
    maxAge: 60 * 5,
    getKey: event => `sdg:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
