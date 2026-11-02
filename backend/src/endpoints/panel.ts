import type { Endpoint, Where } from 'payload'
import { isSuper } from '../lib/access'

// Admin panel (Vue) uchun yig'ma ma'lumotlar. Faqat kirgan adminlar.
const json = (data: unknown, status = 200) => Response.json(data, { status })

/** GET /api/panel/overview — boshqaruv paneli raqamlari */
const overview: Endpoint = {
  path: '/panel/overview',
  method: 'get',
  handler: async (req) => {
    if (!req.user) return json({ message: 'Unauthorized' }, 401)
    const p = req.payload
    const now = new Date()
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString()
    const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
    const dayAgo = new Date(now.getTime() - 24 * 3600 * 1000).toISOString()
    const nowIso = now.toISOString()
    const count = (collection: 'posts' | 'login-events', where: Where) => p.count({ collection, where, overrideAccess: true }).then(r => r.totalDocs)
    const published: Where = { status: { equals: 'published' } }

    const [news, announcements, events, drafts, scheduled, hidden, total] = await Promise.all([
      count('posts', { and: [published, { type: { equals: 'news' } }, { publishedAt: { greater_than_equal: monthStart } }, { publishedAt: { less_than_equal: nowIso } }] }),
      count('posts', { and: [published, { type: { equals: 'announcements' } }, { publishedAt: { greater_than_equal: monthStart } }, { publishedAt: { less_than_equal: nowIso } }] }),
      count('posts', { and: [published, { type: { equals: 'events' } }, { publishedAt: { greater_than_equal: monthStart } }, { publishedAt: { less_than_equal: nowIso } }] }),
      count('posts', { status: { equals: 'draft' } }),
      count('posts', { and: [published, { publishedAt: { greater_than: nowIso } }] }),
      count('posts', { hidden: { equals: true } }),
      count('posts', {}),
    ])

    const recent = await p.find({ collection: 'posts', sort: '-updatedAt', limit: 6, depth: 1, overrideAccess: true })
    const result: Record<string, unknown> = {
      posts: { month: { news, announcements, events }, drafts, scheduled, hidden, total },
      recent: recent.docs.map(d => ({
        id: d.id,
        type: d.type,
        title: d.title?.uz ?? '',
        sdg: d.sdg ?? 0,
        status: d.status,
        hidden: !!d.hidden,
        publishedAt: d.publishedAt ?? null,
        author: d.author && typeof d.author === 'object' ? d.author.name : null,
      })),
    }

    if (isSuper(req.user as { role?: string })) {
      const [loginsToday, failed24h, activity] = await Promise.all([
        count('login-events', { and: [{ result: { equals: 'success' } }, { createdAt: { greater_than_equal: dayStart } }] }),
        count('login-events', { and: [{ result: { not_equals: 'success' } }, { createdAt: { greater_than_equal: dayAgo } }] }),
        p.find({ collection: 'activity', sort: '-createdAt', limit: 6, overrideAccess: true }),
      ])
      result.logins = { today: loginsToday, failed24h }
      result.activity = activity.docs.map(a => ({ id: a.id, who: a.userName, action: a.action, label: a.label, at: a.createdAt }))
    }
    return json(result)
  },
}

export const panelEndpoints: Endpoint[] = [overview]
