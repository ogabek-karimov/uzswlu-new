// O'qildi deb belgilash: `ids` (ixtiyoriy) — tanlanganlar, bo'lmasa hammasi. Faqat o'zinikini belgilaydi (backend tekshiradi)
export default defineEventHandler(async (event) => {
  const body = await readBody<{ ids?: unknown }>(event).catch(() => ({}))
  const ids = Array.isArray(body?.ids) ? body.ids.filter(x => Number.isInteger(x)).slice(0, 100) : undefined
  return backendUserFetch(event, '/me/notifications', { method: 'POST', body: ids ? { ids } : {} })
})
