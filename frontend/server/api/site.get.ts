import type { MenuGroup, SiteData, StateSymbol } from '#shared/types/api'

// Footer va kontaktlar uchun umumiy ma'lumot.
export default defineCachedEventHandler(
  async (event): Promise<SiteData> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    const site = apiBase ? await backendFetch<SiteData>(event, '/site', { lang }) : getMockSite(lang)
    if (!cmsBase) return site

    // Menyu — admin paneldagi "Sahifalar" daraxtidan; davlat ramzlari — "Ramzlar" bo'limidan.
    // CMS javob bermasa — oldingi menyu
    const [menu, symbols] = await Promise.all([
      cmsFetch<MenuGroup[]>(event, '/menu', { lang }).catch(() => null),
      cmsFetch<StateSymbol[]>(event, '/symbols', { lang }).catch(() => null),
    ])
    return { ...site, ...(menu?.length ? { menu } : {}), ...(symbols ? { symbols } : {}) }
  },
  {
    maxAge: 60 * 60,
    getKey: event => `site:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
