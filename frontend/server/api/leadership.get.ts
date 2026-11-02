import type { Leadership } from '#shared/types/api'

// Rektorat: rektor, prorektorlar va matbuot kotibi.
export default defineCachedEventHandler(
  async (event): Promise<Leadership> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Admin panelda boshqariladi (o'zimizning CMS)
    if (cmsBase) return cmsFetch<Leadership>(event, '/leadership', { lang })

    if (!apiBase) return getMockLeadership(lang)

    return backendFetch<Leadership>(event, '/leadership', { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `leadership:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
