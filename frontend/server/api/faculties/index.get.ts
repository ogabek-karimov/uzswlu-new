import type { FacultyList } from '#shared/types/api'

// Fakultetlar ro'yxati (kafedra va yo'nalishlar soni bilan).
export default defineCachedEventHandler(
  async (event): Promise<FacultyList> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Nomi, logo va tartibi — admin panelda; kafedra va yo'nalishlar soni — HEMIS'dan
    if (cmsBase) return cmsFetch<FacultyList>(event, '/faculties', { lang })

    if (!apiBase) return getMockFaculties(lang)

    return backendFetch<FacultyList>(event, '/faculties', { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `faculties:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
