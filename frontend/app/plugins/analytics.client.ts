// Sahifa ko'rishlarini hisoblash (admin paneldagi "Statistika"). Birinchi ochilishda — qayerdan kelgani
// (faqat tashqi sayt nomi), keyingi o'tishlarda — faqat manzil. Qidiruv so'zlari ham yoziladi.
export default defineNuxtPlugin((nuxtApp) => {
  const router = useRouter()
  let first = true
  const send = () => {
    const route = router.currentRoute.value
    const external = first && document.referrer && !document.referrer.startsWith(location.origin) ? document.referrer : undefined
    first = false
    trackHit({ kind: 'pageview', path: route.path, referrer: external })
    const q = route.query.q
    if (route.path.replace(/^\/(ru|en|zh)(?=\/|$)/, '').startsWith('/search') && typeof q === 'string' && q.trim()) trackHit({ kind: 'search', value: q.trim().slice(0, 100) })
  }
  nuxtApp.hook('app:mounted', send)
  router.afterEach((to, from) => {
    if (!first && to.fullPath !== from.fullPath) send()
  })
})
