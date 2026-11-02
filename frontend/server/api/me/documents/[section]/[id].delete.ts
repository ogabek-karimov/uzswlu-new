// Hujjatni butunlay o'chirish (yozuv va fayl) — faqat o'z hujjatini; qaytarib bo'lmaydi
export default defineEventHandler(async (event) => {
  const section = readDocSection(getRouterParam(event, 'section'))
  const id = getRouterParam(event, 'id') ?? ''
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) {
    if (!deleteMockDoc(section, id)) throw createError({ statusCode: 404, statusMessage: 'Not found' })
    return { ok: true }
  }
  return backendUserFetch(event, `/me/documents/${section}/${encodeURIComponent(id)}`, { method: 'DELETE' })
})
