import type { CabinetPatch, StaffCabinet, StaffContactType, StaffNetwork, StaffScienceNetwork } from '#shared/types/api'

const CONTACTS: StaffContactType[] = ['email', 'telegram', 'whatsapp', 'mobile', 'phone', 'office']
const NETWORKS: StaffNetwork[] = ['instagram', 'threads', 'facebook', 'linkedin', 'x', 'youtube']
const SCIENCE: StaffScienceNetwork[] = ['orcid', 'scholar', 'scopus', 'researchgate']

const httpsUrl = (v: unknown) => typeof v === 'string' && /^https:\/\/[^\s<>"']+$/i.test(v.trim()) && v.length <= 500
const text = (v: unknown, max: number) => typeof v === 'string' && v.length <= max

// Kabinetdagi o'zgarishlar: Xodim haqida (4 til), aloqa, tarmoqlar, ilmiy profillar, hujjatlar ko'rinishi.
// Server tomonda ham tekshiriladi: havolalar faqat https (javascript: kabi sxemalar o'tmaydi).
export default defineEventHandler(async (event): Promise<StaffCabinet> => {
  const lang = normalizeLocale(getQuery(event).lang)
  const patch = await readBody<CabinetPatch>(event)
  const bad = (field: string) => createError({ statusCode: 422, statusMessage: `Invalid ${field}` })

  if (patch.about && !(['uz', 'ru', 'en', 'zh'] as const).every(l => text(patch.about![l], 2000))) throw bad('about')
  if (patch.contacts && !patch.contacts.every(c => CONTACTS.includes(c.type) && text(c.value, 300) && c.value.trim())) throw bad('contacts')
  if (patch.contacts?.some(c => c.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.value.trim()))) throw bad('email')
  if (patch.socials && !patch.socials.every(s => NETWORKS.includes(s.network) && httpsUrl(s.url))) throw bad('socials')
  if (patch.science && !patch.science.every(s => SCIENCE.includes(s.network) && httpsUrl(s.url))) throw bad('science')

  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) {
    patchMockCabinet(patch)
    return getMockCabinet(lang)
  }
  return backendUserFetch<StaffCabinet>(event, '/me', { method: 'PATCH', query: { lang }, body: patch as Record<string, unknown> })
})
