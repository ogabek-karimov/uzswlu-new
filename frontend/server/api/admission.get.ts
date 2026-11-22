import type { Admission } from '#shared/types/api'

// Qabul sahifasi: sanalar, yo'nalishlar, hujjatlar, savol-javob. ?year=2025-2026 — arxiv yili.
const admissionYearParam = (v: unknown) => (typeof v === 'string' && /^\d{4}-\d{4}$/.test(v) ? v : '')
export default defineCachedEventHandler(
  async (event): Promise<Admission> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const year = admissionYearParam(getQuery(event).year)
    const { apiBase } = useRuntimeConfig(event)

    if (!apiBase) {
      if (year) throw createError({ statusCode: 404, statusMessage: 'Admission year not found' })
      return getMockAdmission(lang)
    }

    return backendFetch<Admission>(event, '/admission', year ? { lang, year } : { lang })
  },
  {
    maxAge: 5,
    swr: false,   // eskirgan nusxa BERILMAYDI: admin saqlagach kesh tozalash o'tmay qolsa ham eng ko'pi 5 soniya (backend o'z keshi bilan himoyalaydi)
    getKey: event => `admission:${normalizeLocale(getQuery(event).lang)}:${admissionYearParam(getQuery(event).year) || 'active'}`,
    // Arxiv yili (?year=) keshdan o'tmaydi: aks holda «yo'q» (404) javobi 200 bo'lib qaytardi; backend o'zi keshlaydi
    shouldBypassCache: event => import.meta.dev || !!admissionYearParam(getQuery(event).year),
  },
)
