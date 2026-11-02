import type { ContactPage, Leadership } from '#shared/types/api'

// Aloqa sahifasi: telefonlar, e-pochtalar, binolar, rahbariyat telefonlari.
export default defineCachedEventHandler(
  async (event): Promise<ContactPage> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    const page = apiBase ? await backendFetch<ContactPage>(event, '/contact', { lang }) : getMockContact(lang)
    if (!cmsBase) return page

    // "Kimga" ro'yxati va rahbarlar telefonlari — admin paneldagi Rahbariyat bo'limidan
    const cms = await cmsFetch<Leadership & { recipients: ContactPage['recipients'] }>(event, '/leadership', { lang }).catch(() => null)
    if (!cms) return page
    const others = page.recipients.filter(r => r.id === 'admission')
    return {
      ...page,
      leaders: cms.prorectors.filter(p => p.phone || p.ext).map(p => ({ name: p.name, role: p.role, ext: p.ext ?? '', phone: p.phone ?? '' })),
      recipients: [...cms.recipients, ...others],
    }
  },
  {
    maxAge: 60 * 5,
    getKey: event => `contact:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
