// Vazifani o'chirish: faqat bergan odam (backend tekshiradi)
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id') ?? ''
  if (!/^\d{1,12}$/.test(id)) throw createError({ statusCode: 422, statusMessage: 'Invalid task' })
  return backendUserFetch(event, `/me/tasks/${id}`, { method: 'DELETE' })
})
