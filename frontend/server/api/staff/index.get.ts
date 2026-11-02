import type { StaffGroup, StaffList } from '#shared/types/api'

const GROUPS = ['all', 'lead', 'faculty', 'chair', 'unit'] as const

// Xodimlar ro'yxati: qidiruv, bo'lim, guruh va sahifa bo'yicha.
export default defineCachedEventHandler(
  async (event): Promise<StaffList> => {
    const query = readStaffQuery(event)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    if (!apiBase) {
      // Admin panelda "Saytda ko'rsatish" o'chirilgan xodimlar ro'yxatda chiqmaydi
      const hidden = cmsBase ? await cmsFetch<{ ids: string[] }>(event, '/staff-hidden').then(r => new Set(r.ids)).catch(() => undefined) : undefined
      return getMockStaffList(query.lang, { ...query, exclude: hidden })
    }

    return backendFetch<StaffList>(event, '/staff', query)
  },
  {
    // Qisqa kesh: xodim yangi rasm yuklasa ro'yxatda ham tez almashsin
    maxAge: 60,
    getKey: (event) => {
      const q = readStaffQuery(event)
      return `staff:${q.lang}:${q.group}:${q.department ?? ''}:${q.page}:${q.perPage}:${q.q ?? ''}`
    },
    shouldBypassCache: () => import.meta.dev,
  },
)

function readStaffQuery(event: Parameters<typeof getQuery>[0]) {
  const raw = getQuery(event)
  const str = (v: unknown) => (typeof v === 'string' && v.trim() ? v.trim().slice(0, 100) : undefined)
  const int = (v: unknown, fallback: number, max: number) => Math.min(max, Math.max(1, Number.parseInt(String(v), 10) || fallback))
  const group = GROUPS.includes(raw.group as never) ? (raw.group as StaffGroup | 'all') : 'all'

  return {
    lang: normalizeLocale(raw.lang),
    q: str(raw.q),
    department: str(raw.department),
    group,
    page: int(raw.page, 1, 10_000),
    perPage: int(raw.perPage, 24, 48),
  }
}
