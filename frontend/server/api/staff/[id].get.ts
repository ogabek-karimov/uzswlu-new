import type { StaffProfile } from '#shared/types/api'

// Bitta xodim profili (uzswlu.uz/teacher/:id ga mos).
// Nuxt serverida keshlanmaydi: xodim dashboard'da o'zgartirgan narsa Staff sahifasida darrov ko'rinishi kerak
// (oldingi saytdagidek). HEMIS ma'lumotini backend o'zi keshlaydi.
export default defineEventHandler(async (event): Promise<StaffProfile> => {
  const id = getRouterParam(event, 'id') ?? ''
  if (!/^\d{1,10}$/.test(id)) throw createError({ statusCode: 404, statusMessage: 'Staff member not found' })

  const lang = normalizeLocale(getQuery(event).lang)
  const { apiBase, cmsBase } = useRuntimeConfig(event)

  if (!apiBase) {
    const profile = getMockStaffProfile(lang, id)
    if (!profile) throw createError({ statusCode: 404, statusMessage: 'Staff member not found' })
    if (!cmsBase) return profile
    // Admin panelda to'ldirilgan bio va ilmiy profillar; yashirilgan xodim — 404
    const own = await cmsFetch<{ hidden: boolean; about: string | null; science: StaffProfile['science'] }>(event, `/staff/${id}`, { lang }).catch(() => null)
    if (own?.hidden) throw createError({ statusCode: 404, statusMessage: 'Staff member not found' })
    return own ? { ...profile, about: own.about ?? profile.about, science: own.science.length ? own.science : profile.science } : profile
  }

  return backendFetch<StaffProfile>(event, `/staff/${id}`, { lang })
})
