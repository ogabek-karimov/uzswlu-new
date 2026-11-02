import type { SdgGoal } from '#shared/types/api'

// BRM maqsad sahifasi (1–17): bo'limlar va hujjatlar. Faoliyat — /api/posts?sdg=n
export default defineCachedEventHandler(
  async (event): Promise<SdgGoal> => {
    const n = Number(getRouterParam(event, 'n'))
    if (!Number.isInteger(n) || n < 1 || n > 17) throw createError({ statusCode: 404, statusMessage: 'Goal not found' })

    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Tavsif, ichki bo'limlar va hisobotlar — admin paneldagi BRM bo'limidan
    if (cmsBase) {
      return cmsFetch<SdgGoal>(event, `/sdg/${n}`, { lang }).catch((error) => {
        if ((error as { statusCode?: number }).statusCode === 404) throw createError({ statusCode: 404, statusMessage: 'Goal not found' })
        throw error
      })
    }

    if (!apiBase) {
      const goal = getMockSdgGoal(lang, n)
      if (!goal) throw createError({ statusCode: 404, statusMessage: 'Goal not found' })
      return goal
    }

    return backendFetch<SdgGoal>(event, `/sdg/${n}`, { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `sdg-goal:${getRouterParam(event, 'n')}:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
