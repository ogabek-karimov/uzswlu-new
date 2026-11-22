import type { CabinetTask } from '#shared/types/api'

// Vazifa yaratish: huquq (kimga topshiriq berish mumkin) backendda HEMIS lavozimidan tekshiriladi.
export default defineEventHandler(async (event): Promise<CabinetTask> => {
  const body = await readBody<Record<string, unknown>>(event)
  const str = (v: unknown, max: number) => typeof v === 'string' && v.length <= max
  if (!str(body?.title, 200) || !String(body.title).trim()) throw createError({ statusCode: 422, statusMessage: 'Invalid title' })
  if (body.note != null && !str(body.note, 2000)) throw createError({ statusCode: 422, statusMessage: 'Invalid note' })
  if (body.due != null && body.due !== '' && !(typeof body.due === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(body.due))) throw createError({ statusCode: 422, statusMessage: 'Invalid due' })
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) throw createError({ statusCode: 503, statusMessage: 'Backend ulanmagan' })
  return backendUserFetch<CabinetTask>(event, '/me/tasks', { method: 'POST', body: { title: body.title, note: body.note, due: body.due || null, assigneeId: body.assigneeId || null } })
})
