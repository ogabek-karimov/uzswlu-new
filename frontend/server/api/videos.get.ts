import type { VideoList } from '#shared/types/api'

// Video darsliklar va onlayn translatsiya holati.
export default defineCachedEventHandler(
  async (event): Promise<VideoList> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Admin panelda boshqariladi (o'zimizning CMS)
    if (cmsBase) return cmsFetch<VideoList>(event, '/videos', { lang })

    if (!apiBase) return getMockVideos(lang)

    return backendFetch<VideoList>(event, '/videos', { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `videos:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
