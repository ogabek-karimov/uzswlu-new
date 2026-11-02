import type { Post, PostType } from '#shared/types/api'

const TYPES: PostType[] = ['news', 'announcements', 'events']

// Bitta yangilik, e'lon yoki tadbir.
export default defineCachedEventHandler(
  async (event): Promise<Post> => {
    const type = getRouterParam(event, 'type') as PostType
    const slug = getRouterParam(event, 'slug') ?? ''
    if (!TYPES.includes(type) || !/^[\w-]{1,160}$/.test(slug)) throw createError({ statusCode: 404, statusMessage: 'Post not found' })

    const lang = normalizeLocale(getQuery(event).lang)
    const { apiBase, cmsBase } = useRuntimeConfig(event)

    if (cmsBase) {
      return cmsFetch<Post>(event, `/posts/${type}/${slug}`, { lang }).catch((error: { statusCode?: number }) => {
        throw createError({ statusCode: error.statusCode === 404 ? 404 : 502, statusMessage: 'Post not found' })
      })
    }
    if (!apiBase) {
      const post = getMockPost(lang, type, slug)
      if (!post) throw createError({ statusCode: 404, statusMessage: 'Post not found' })
      return post
    }

    return backendFetch<Post>(event, `/posts/${type}/${slug}`, { lang })
  },
  {
    maxAge: 60,
    getKey: event => `post:${getRouterParam(event, 'type')}:${getRouterParam(event, 'slug')}:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
