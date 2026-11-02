import type { DocumentList } from '#shared/types/api'

// Me'yoriy hujjatlar — ro'yxat to'liq keladi (qidiruv va toifa frontend'da).
export default defineCachedEventHandler(
  async (event): Promise<DocumentList> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Admin panelda boshqariladi (o'zimizning CMS)
    if (cmsBase) return cmsFetch<DocumentList>(event, '/documents', { lang })

    if (!apiBase) return getMockDocuments(lang)

    return backendFetch<DocumentList>(event, '/documents', { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `documents:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
