import type { CabinetTask } from '#shared/types/api'

// Vazifa holati: faqat ijrochi o'zgartiradi (backend tekshiradi)
export default defineEventHandler(async (event): Promise<CabinetTask> => {
  const id = getRouterParam(event, 'id') ?? ''
  const { status } = await readBody<{ status?: string }>(event)
  if (!/^\d{1,12}$/.test(id) || (status !== 'open' && status !== 'done')) throw createError({ statusCode: 422, statusMessage: 'Invalid task' })
  return backendUserFetch<CabinetTask>(event, `/me/tasks/${id}`, { method: 'PATCH', body: { status } })
})
