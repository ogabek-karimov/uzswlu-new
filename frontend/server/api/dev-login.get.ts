// Faqat lokal sinov (NUXT_DEV_LOGIN=true): backend «rol tanlab kirish» sahifasi tokenni shu yerga yo'llaydi,
// biz uni sayt manzilidagi `session` cookie'ga yozib, kabinetga o'tkazamiz. Productionda o'chiq (404).
export default defineEventHandler((event) => {
  if (!useRuntimeConfig(event).devLogin) throw createError({ statusCode: 404, statusMessage: 'Not Found' })
  const token = String(getQuery(event).token ?? '')
  if (!/^[\w-]{20,200}$/.test(token)) throw createError({ statusCode: 400, statusMessage: 'Bad Request' })
  setCookie(event, 'session', token, { httpOnly: true, sameSite: 'lax', path: '/', maxAge: 8 * 3600 })
  return sendRedirect(event, '/dashboard', 302)
})
