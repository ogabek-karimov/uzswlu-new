import type { StaffCabinet } from '#shared/types/api'

// Xodim kabineti (dashboard). Kesh yo'q — shaxsiy va tez-tez o'zgaradi.
export default defineEventHandler(async (event): Promise<StaffCabinet> => {
  const lang = normalizeLocale(getQuery(event).lang)
  const { apiBase } = useRuntimeConfig(event)

  if (!apiBase) return getMockCabinet(lang)

  return backendUserFetch<StaffCabinet>(event, '/me', { query: { lang } })
})
