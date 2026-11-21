import type { CabinetAdminLink } from '#shared/types/api'

// «Admin panel» tugmasi: backend xodimning admin hisobi borligini aytadi va 60 soniyalik bir martalik havola beradi. Keshlanmaydi.
export default defineEventHandler(async (event): Promise<CabinetAdminLink> => {
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) return { available: false, url: null }
  return backendUserFetch<CabinetAdminLink>(event, '/me/admin-link')
})
