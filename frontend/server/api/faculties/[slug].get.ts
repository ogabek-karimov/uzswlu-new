import type { FacultyDetail } from '#shared/types/api'

// Fakultet sahifasi: dekan, yo'nalishlar, kafedralar, dekanat (HEMIS), yangiliklar.
export default defineCachedEventHandler(
  async (event): Promise<FacultyDetail> => {
    const slug = getRouterParam(event, 'slug') ?? ''
    if (!/^[a-z0-9-]{1,80}$/.test(slug)) throw createError({ statusCode: 404, statusMessage: 'Faculty not found' })

    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Matn, logo va aloqa — admin panelda; dekan, kafedralar, sonlar — HEMIS'dan (backend birlashtiradi)
    if (cmsBase) {
      return cmsFetch<FacultyDetail>(event, `/faculties/${slug}`, { lang }).catch((error) => {
        if ((error as { statusCode?: number }).statusCode === 404) throw createError({ statusCode: 404, statusMessage: 'Faculty not found' })
        throw error
      })
    }

    if (!apiBase) {
      const faculty = getMockFaculty(lang, slug)
      if (!faculty) throw createError({ statusCode: 404, statusMessage: 'Faculty not found' })
      return faculty
    }

    return backendFetch<FacultyDetail>(event, `/faculties/${slug}`, { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `faculty:${getRouterParam(event, 'slug')}:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
