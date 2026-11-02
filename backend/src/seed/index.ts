import type { Payload } from 'payload'
import { seedContent } from './content'
import { seedPages } from './pages'
import data from './posts-seed.json' with { type: 'json' }

type L = { uz: string; ru: string; en: string; zh: string }
type SeedPost = {
  type: 'news' | 'announcements' | 'events'
  slug: string
  date: string
  category: L
  title: L
  excerpt?: L
  body?: Record<keyof L, string[]>
  tags?: Record<keyof L, string[]>
  location?: L
  sdg?: number
}

const ctx = { seed: true }

/** Birinchi ishga tushishda: superadmin, kategoriyalar, saytdagi namunaviy postlar, sozlamalarning asl holati */
export async function seed(payload: Payload) {
  const users = await payload.count({ collection: 'users', overrideAccess: true })
  if (!users.totalDocs) {
    const username = process.env.SUPERADMIN_USERNAME || 'superadmin'
    const password = process.env.SUPERADMIN_PASSWORD
    if (!password) {
      payload.logger.warn('SUPERADMIN_PASSWORD .env faylida yo‘q — superadmin yaratilmadi')
    }
    else {
      await payload.create({
        collection: 'users',
        overrideAccess: true,
        context: ctx,
        data: { username, password, name: process.env.SUPERADMIN_NAME || 'Superadmin', role: 'superadmin', status: 'active' },
      })
      payload.logger.info(`Superadmin yaratildi: ${username}`)
    }
  }

  const cats = await payload.count({ collection: 'categories', overrideAccess: true })
  const catIds: Record<string, number> = {}
  if (!cats.totalDocs) {
    for (const [key, name] of Object.entries(data.cats as Record<string, L>)) {
      const doc = await payload.create({ collection: 'categories', overrideAccess: true, context: ctx, data: { key, name } })
      catIds[name.uz] = doc.id as number
    }
  }

  const posts = await payload.count({ collection: 'posts', overrideAccess: true })
  if (!posts.totalDocs) {
    const italian = (data as { italianBody: Record<keyof L, string[]> }).italianBody
    const seeds = data.posts as SeedPost[]
    for (const [i, s] of seeds.entries()) {
      const at = s.date.includes('T') ? s.date : `${s.date}T${String(9 + (i * 7) % 10).padStart(2, '0')}:${String((i * 23) % 60).padStart(2, '0')}:00+05:00`
      const paragraphs = s.body ?? (s.slug === 'italyan-tili-anjumani' ? italian : undefined)
      const body = paragraphs
        ? Object.fromEntries((['uz', 'ru', 'en', 'zh'] as const).map(l => [l, (paragraphs[l] ?? []).map(p => `<p>${p}</p>`).join('')]))
        : undefined
      await payload.create({
        collection: 'posts',
        overrideAccess: true,
        context: ctx,
        data: {
          type: s.type,
          slug: s.slug,
          title: s.title,
          excerpt: s.excerpt,
          body,
          tags: s.tags,
          location: s.location,
          category: catIds[s.category.uz],
          sdg: s.sdg ?? 0,
          status: 'published',
          // tadbir e'loni bir hafta oldin chiqqan (lekin kelajakda emas)
          publishedAt: s.type === 'events'
            ? new Date(Math.min(new Date(at).getTime() - 7 * 24 * 3600 * 1000, Date.now() - 3600 * 1000)).toISOString()
            : new Date(at).toISOString(),
          startsAt: s.type === 'events' ? new Date(at).toISOString() : undefined,
        },
      })
    }
    payload.logger.info(`Namunaviy postlar yuklandi: ${seeds.length}`)
  }

  // Sozlamalarning "asl holati" — birinchi versiya bo'lib saqlanadi
  const versions = await payload.findGlobalVersions({ slug: 'settings', limit: 1, overrideAccess: true })
  if (!versions.totalDocs) {
    const current = await payload.findGlobal({ slug: 'settings', overrideAccess: true })
    await payload.updateGlobal({ slug: 'settings', overrideAccess: true, context: ctx, data: current })
    payload.logger.info('Sozlamalarning asl holati saqlandi')
  }

  await seedContent(payload)
  await seedPages(payload)
}
