import type { H3Event } from 'h3'
import type { Post, PostTranslation, PostType } from '#shared/types/api'

const TYPES: PostType[] = ['news', 'announcements', 'events']

/** Postni bitta tilda olish; shu tilda yo'q bo'lsa — null */
async function loadPost(event: H3Event, type: PostType, slug: string, lang: Locale): Promise<Post | null> {
  const { apiBase, cmsBase } = useRuntimeConfig(event)
  const notFound = (error: { statusCode?: number }) => {
    if (error.statusCode === 404) return null
    throw error
  }
  if (cmsBase) return cmsFetch<Post>(event, `/posts/${type}/${slug}`, { lang }).catch(notFound)
  if (!apiBase) return getMockPost(lang, type, slug)
  return backendFetch<Post>(event, `/posts/${type}/${slug}`, { lang }).catch(notFound)
}

// Post qaysi tillarda bor (Telegram'da 4 tildagi havola bilan ulashish uchun) va har tildagi asosiy surat
const loadTranslations = defineCachedFunction(
  async (event: H3Event, type: PostType, slug: string): Promise<PostTranslation[]> => {
    const posts = await Promise.all(LOCALES.map(lang => loadPost(event, type, slug, lang).catch(() => null)))
    return LOCALES.flatMap((lang, i) => (posts[i] ? [{ lang, image: posts[i].image ?? null }] : []))
  },
  { name: 'post-translations', maxAge: 300, getKey: (_event: H3Event, type: string, slug: string) => `${type}:${slug}` },
)

// Asosiy surat tik yoki yotiqligini sahifa oldindan bilsin (backend o'lchamni bermasa — fayldan aniqlanadi)
async function withImageSize(event: H3Event, post: Post): Promise<Post> {
  if (!post.image || (post.imageWidth && post.imageHeight)) return post
  const size = await imageSize(new URL(post.image, getRequestURL(event).origin).href).catch(() => null)
  return size ? { ...post, imageWidth: size.width, imageHeight: size.height } : post
}

// Bitta yangilik, e'lon yoki tadbir.
export default defineCachedEventHandler(
  async (event): Promise<Post> => {
    const type = getRouterParam(event, 'type') as PostType
    const slug = getRouterParam(event, 'slug') ?? ''
    if (!TYPES.includes(type) || !/^[\w-]{1,160}$/.test(slug)) throw createError({ statusCode: 404, statusMessage: 'Post not found' })

    const lang = normalizeLocale(getQuery(event).lang)
    const post = await loadPost(event, type, slug, lang).catch(() => {
      throw createError({ statusCode: 502, statusMessage: 'Post not found' })
    })
    if (!post) throw createError({ statusCode: 404, statusMessage: 'Post not found' })

    const [sized, translations] = await Promise.all([
      withImageSize(event, post),
      post.translations ? post.translations : loadTranslations(event, type, slug).catch(() => undefined),
    ])
    return { ...sized, translations }
  },
  {
    maxAge: 60,
    getKey: event => `post:${getRouterParam(event, 'type')}:${getRouterParam(event, 'slug')}:${normalizeLocale(getQuery(event).lang)}`,
    shouldBypassCache: () => import.meta.dev,
  },
)
