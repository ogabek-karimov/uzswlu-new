import type { ProgramList } from '#shared/types/api'

// Ta'lim yo'nalishlari: ?level=bachelor|master
export default defineCachedEventHandler(
  async (event): Promise<ProgramList> => {
    const { lang, level } = readProgramQuery(event)
    const { apiBase } = useRuntimeConfig(event)

    if (!apiBase) return getMockPrograms(lang, level)

    return backendFetch<ProgramList>(event, '/programs', { lang, level })
  },
  {
    maxAge: 60 * 5,
    getKey: (event) => {
      const q = readProgramQuery(event)
      return `programs:${q.lang}:${q.level}`
    },
    shouldBypassCache: () => import.meta.dev,
  },
)

function readProgramQuery(event: Parameters<typeof getQuery>[0]) {
  const raw = getQuery(event)
  return { lang: normalizeLocale(raw.lang), level: raw.level === 'master' ? 'master' as const : 'bachelor' as const }
}
