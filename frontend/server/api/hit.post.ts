// Sayt statistikasi: brauzerdan kelgan yozuv CMS'ga uzatiladi (foydalanuvchining IP va brauzer
// ma'lumoti faqat anonim kunlik kod hisoblash uchun; cookie ishlatilmaydi). Hech qachon xato qaytarmaydi.
export default defineEventHandler(async (event) => {
  const { cmsBase } = useRuntimeConfig(event)
  if (cmsBase) {
    const body = await readBody<Record<string, unknown>>(event).catch(() => null)
    const ip = getRequestIP(event, { xForwardedFor: true })
    const country = getHeader(event, 'cf-ipcountry')
    await $fetch('/hit', {
      baseURL: cmsBase,
      method: 'POST',
      body: typeof body === 'string' ? JSON.parse(body) : body,
      timeout: 3000,
      headers: {
        'user-agent': getHeader(event, 'user-agent') ?? '',
        ...(ip ? { 'x-forwarded-for': ip } : {}),
        ...(country ? { 'cf-ipcountry': country } : {}),
      },
    }).catch(() => {})
  }
  setResponseStatus(event, 204)
  return null
})
