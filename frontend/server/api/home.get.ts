import type { FacultyList, HomeData } from '#shared/types/api'

// Bosh sahifa uchun barcha ma'lumot bitta so'rovda.
// NUXT_API_BASE berilgan bo'lsa — haqiqiy backend, aks holda — mock.
export default defineCachedEventHandler(
  async (event): Promise<HomeData> => {
    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    const home = apiBase ? await backendFetch<HomeData>(event, '/home', { lang }) : getMockHome(lang)
    if (!cmsBase) return home

    // Karusel, yangiliklar, e'lonlar va tadbirlar — o'zimizning CMS'dan. CMS vaqtincha javob bermasa,
    // bosh sahifa baribir ochiladi (karusel — oldingi bannerlar, qolgan bloklar bo'sh turadi).
    const [latest, slides] = await Promise.all([
      cmsFetch<Pick<HomeData, 'news' | 'announcements' | 'events'>>(event, '/latest', { lang })
        .catch((error) => {
          console.error('[home] CMS javob bermadi:', (error as Error).message)
          return { news: [], announcements: [], events: [] }
        }),
      cmsFetch<HomeData['slides']>(event, '/slides', { lang }).catch(() => home.slides),
    ])
    const faculties = await cmsFetch<FacultyList>(event, '/faculties', { lang })
      .then(r => r.items.map(({ id, slug, name, logo }) => ({ id, slug, name, logo })))
      .catch(() => home.faculties)
    return { ...home, ...latest, slides, faculties }
  },
  {
    // HEMIS'ga ortiqcha yuk tushmasligi uchun javob 5 daqiqa keshda turadi
    maxAge: 60 * 5,
    getKey: event => `home:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
