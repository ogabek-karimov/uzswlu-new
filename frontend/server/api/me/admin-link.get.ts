import type { CabinetAdminLink } from '#shared/types/api'

// «Admin panel» tugmasi va profil menyusidagi «Mening bo'limlarim»: backend xodimning admin hisobi/rolini aytadi.
// `?list=1` — faqat ro'yxat (havolasiz); `?next=<bo'lim kaliti>` — 60 soniyalik bir martalik havola shu bo'limga olib boradi. Keshlanmaydi.
// Kirmagan mehmon uchun xato emas, shunchaki `available: false` (menyu har ochilganda so'raydi).
const NONE: CabinetAdminLink = { available: false, url: null, role: null, sections: [] }

export default defineEventHandler(async (event): Promise<CabinetAdminLink> => {
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) return NONE
  const q = getQuery(event)
  const query: Record<string, string> = {}
  if (q.list) query.list = '1'
  if (typeof q.next === 'string' && /^[a-z-]{1,30}$/.test(q.next)) query.next = q.next
  try {
    return await backendUserFetch<CabinetAdminLink>(event, '/me/admin-link', { query })
  }
  catch (e) {
    const status = (e as { statusCode?: number, status?: number }).statusCode ?? (e as { status?: number }).status
    if (status === 401 || status === 403) return NONE
    throw e
  }
})
