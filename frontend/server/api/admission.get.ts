import type { Admission } from '#shared/types/api'

// Qabul sahifasi: sanalar, yo'nalishlar, hujjatlar, savol-javob.
export default defineCachedEventHandler(
  async (event): Promise<Admission> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase } = useRuntimeConfig(event)

    if (!apiBase) return getMockAdmission(lang)

    return backendFetch<Admission>(event, '/admission', { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `admission:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
