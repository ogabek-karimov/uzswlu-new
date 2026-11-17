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
    maxAge: 5,
    swr: false,   // eskirgan nusxa BERILMAYDI: admin saqlagach kesh tozalash o'tmay qolsa ham eng ko'pi 5 soniya (backend o'z keshi bilan himoyalaydi)
    getKey: event => `admission:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
