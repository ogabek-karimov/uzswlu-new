// Kabinetdan chiqish («Chiqish» tugmasi — /logout): backend sessiyani bazadan o'chiradi (token qayta ishlamaydi),
// sayt `session` cookie'sini o'chiradi va bosh sahifaga qaytaradi. Backend javob bermasa ham cookie baribir o'chiriladi.
export default defineEventHandler(async (event) => {
  const { apiBase } = useRuntimeConfig(event)
  if (apiBase && getCookie(event, 'session')) {
    await backendUserFetch(event, '/me/logout', { method: 'POST' }).catch(() => null)
  }
  deleteCookie(event, 'session', { path: '/', httpOnly: true, sameSite: 'lax' })
  setHeader(event, 'Cache-Control', 'no-store')
  return sendRedirect(event, '/', 302)
})
