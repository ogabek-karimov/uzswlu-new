import type { ContentPage } from '#shared/types/api'

// Matnli sahifa (Universitet haqida, Tuzilma, Stipendiyalar …) — slug menyudagi manzildan.
export default defineCachedEventHandler(
  async (event): Promise<ContentPage> => {
    const slug = getRouterParam(event, 'slug') ?? ''
    if (!/^[a-z0-9-]{1,120}$/.test(slug)) throw createError({ statusCode: 404, statusMessage: 'Page not found' })

    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    // Matnli sahifalar — admin paneldagi "Sahifalar" daraxtidan
    if (cmsBase) {
      return cmsFetch<ContentPage>(event, `/pages/${slug}`, { lang }).catch((error) => {
        if ((error as { statusCode?: number }).statusCode === 404) throw createError({ statusCode: 404, statusMessage: 'Page not found' })
        throw error
      })
    }

    if (!apiBase) {
      const page = getMockContentPage(lang, slug)
      if (!page) throw createError({ statusCode: 404, statusMessage: 'Page not found' })
      return page
    }

    return backendFetch<ContentPage>(event, `/pages/${slug}`, { lang })
  },
  {
    maxAge: 60 * 5,
    getKey: event => `page:${getRouterParam(event, 'slug')}:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
