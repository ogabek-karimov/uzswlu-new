import { timingSafeEqual } from 'node:crypto'

/**
 * Sayt (Nuxt) ichki keshini tozalash. Backend admin kontentni saqlaganda chaqiradi (backend/apps/api/edge.py),
 * shunda bosh sahifa va ro'yxatlar 5 daqiqa kutmay yangilanadi.
 * Himoya: `Authorization: Bearer <NUXT_API_TOKEN>` (backenddagi API_TOKEN bilan bir xil). Token bo'sh bo'lsa endpoint o'chiq (404).
 */
function sameToken(given: string, expected: string): boolean {
  const a = Buffer.from(given)
  const b = Buffer.from(expected)
  return a.length === b.length && timingSafeEqual(a, b)
}

export default defineEventHandler(async (event) => {
  const { apiToken } = useRuntimeConfig(event)
  const tokens = String(apiToken || '').split(',').map(t => t.trim()).filter(Boolean)
  if (!tokens.length) throw createError({ statusCode: 404, statusMessage: 'Not Found' })

  const given = (getHeader(event, 'authorization') || '').replace(/^Bearer\s+/i, '')
  if (!tokens.some(t => sameToken(given, t))) throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })

  await useStorage('cache').clear()
  return { ok: true }
})
