import type { CollectionAfterChangeHook, CollectionAfterDeleteHook, GlobalAfterChangeHook } from 'payload'
import { logActivity, purgeSiteCache } from './activity'

type Doc = Record<string, any>

const same = (a: unknown, b: unknown) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null)
const short = (v: unknown) => {
  if (v && typeof v === 'object' && 'id' in (v as Doc)) return (v as Doc).filename ?? (v as Doc).id
  const s = typeof v === 'string' ? v : JSON.stringify(v ?? '')
  return s.length > 120 ? `${s.slice(0, 117)}…` : s
}

/** Kolleksiya o'zgarishini faollik jurnaliga yozish va sayt keshini yangilash (bir xil qolip) */
export function track(entity: string, opts: { label: (doc: Doc) => string | null | undefined; fields: string[]; tags: string[] }) {
  const afterChange: CollectionAfterChangeHook = async ({ req, doc, previousDoc, operation }) => {
    // seed — boshlang'ich ma'lumot, silent — hisoblagich (yuklab olishlar soni) o'zgarishi
    if (req.context?.seed || req.context?.silent) return doc
    const label = opts.label(doc)
    if (operation === 'create') {
      await logActivity(req, { action: 'create', entity, entityId: doc.id, label })
    }
    else if (previousDoc) {
      const changes: Record<string, { before: unknown; after: unknown }> = {}
      for (const key of opts.fields) {
        if (!same(previousDoc[key], doc[key])) changes[key] = { before: short(previousDoc[key]), after: short(doc[key]) }
      }
      if (Object.keys(changes).length) {
        const action = 'hidden' in changes ? (doc.hidden ? 'hide' : 'show') : 'edit'
        await logActivity(req, { action, entity, entityId: doc.id, label, changes })
      }
    }
    await purgeSiteCache(opts.tags)
    return doc
  }
  const afterDelete: CollectionAfterDeleteHook = async ({ req, doc }) => {
    await logActivity(req, { action: 'delete', entity, entityId: doc.id, label: opts.label(doc) })
    await purgeSiteCache(opts.tags)
  }
  return { afterChange: [afterChange], afterDelete: [afterDelete] }
}

/** Global (bitta sahifa sozlamasi) uchun: o'zgargan guruhlar jurnalga yoziladi */
export function trackGlobal(entity: string, label: string, tags: string[]): GlobalAfterChangeHook {
  return async ({ req, doc, previousDoc }) => {
    if (req.context?.seed) return doc
    const changes: Record<string, { before: unknown; after: unknown }> = {}
    for (const key of Object.keys(doc)) {
      if (['id', 'updatedAt', 'createdAt', 'globalType'].includes(key)) continue
      if (!same(previousDoc?.[key], doc[key])) changes[key] = { before: '…', after: '…' }
    }
    if (Object.keys(changes).length) await logActivity(req, { action: 'settings', entity, label, changes })
    await purgeSiteCache(tags)
    return doc
  }
}
