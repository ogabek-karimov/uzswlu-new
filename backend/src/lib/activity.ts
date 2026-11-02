import type { PayloadRequest } from 'payload'
import { clientIp } from './request'

export type ActivityAction = 'create' | 'edit' | 'publish' | 'hide' | 'show' | 'delete' | 'restore' | 'role' | 'settings'

/** Faollik jurnaliga yozuv. Xato bo'lsa ham asosiy amalni to'xtatmaydi. */
export async function logActivity(req: PayloadRequest, entry: {
  action: ActivityAction
  entity: string
  entityId?: string | number
  label?: string | null
  changes?: Record<string, { before: unknown; after: unknown }>
}) {
  try {
    const user = req.user as { id?: number | string; name?: string | null; username?: string | null } | null
    await req.payload.create({
      collection: 'activity',
      overrideAccess: true,
      req,
      data: {
        user: user?.id as number | undefined,
        userName: user?.name ?? user?.username ?? 'tizim',
        action: entry.action,
        entity: entry.entity,
        entityId: entry.entityId != null ? String(entry.entityId) : undefined,
        label: entry.label?.slice(0, 300) ?? undefined,
        changes: entry.changes ?? {},
        ip: clientIp(req),
      },
    })
  }
  catch (error) {
    req.payload.logger.error({ err: error, msg: 'activity log failed' })
  }
}

/** Saytning keshini yangilash (Nuxt): o'zgargan kontent darhol ko'rinsin */
export async function purgeSiteCache(tags: string[]) {
  const url = process.env.SITE_PURGE_URL
  if (!url) return
  try {
    await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${process.env.SITE_PURGE_TOKEN ?? ''}` },
      body: JSON.stringify({ tags }),
      signal: AbortSignal.timeout(3000),
    })
  }
  catch {
    // sayt o'chiq bo'lsa ham saqlash davom etadi
  }
}
