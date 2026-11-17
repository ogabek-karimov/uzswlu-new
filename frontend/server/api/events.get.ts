import type { EventMonth } from '#shared/types/api'

// Tadbirlar taqvimi: bitta oy (?month=YYYY-MM, bo'lmasa joriy oy — Toshkent vaqti).
export default defineCachedEventHandler(
  async (event): Promise<EventMonth> => {
    const { lang, month } = readEventQuery(event)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    if (cmsBase) return cmsFetch<EventMonth>(event, '/events', { lang, month })
    if (!apiBase) return getMockEventMonth(lang, month)

    return backendFetch<EventMonth>(event, '/events', { lang, month })
  },
  {
    maxAge: 5,
    swr: false,   // eskirgan nusxa BERILMAYDI: admin saqlagach kesh tozalash o'tmay qolsa ham eng ko'pi 5 soniya (backend o'z keshi bilan himoyalaydi)
    getKey: (event) => {
      const q = readEventQuery(event)
      return `events:${q.lang}:${q.month}`
    },
    shouldBypassCache: () => import.meta.dev,
  },
)

function readEventQuery(event: Parameters<typeof getQuery>[0]) {
  const raw = getQuery(event)
  const valid = typeof raw.month === 'string' && /^\d{4}-(0[1-9]|1[0-2])$/.test(raw.month)
  const tashkent = new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString().slice(0, 7)
  return { lang: normalizeLocale(raw.lang), month: valid ? (raw.month as string) : tashkent }
}
