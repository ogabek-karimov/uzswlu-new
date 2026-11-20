// Til almashtirilganda sahifa tepaga sakramaydi.
// 1) Til tanlagich sahifani to'liq qayta yuklaydi (aralash til bo'lmasin) — bosishdan oldin scrollY saqlanadi (LangSwitcher),
//    yangi tildagi sahifa ochilgach o'sha joyga qaytariladi.
// 2) SPA ichida faqat til o'zgargan o'tishda Nuxt'ning «tepaga chiq»i o'chiriladi (meta.scrollToTop = false).
export default defineNuxtPlugin((nuxtApp) => {
  const router = useRouter()
  const base = (name: unknown) => String(name ?? '').split('___')[0]
  const same = (a: object, b: object) => JSON.stringify(a) === JSON.stringify(b)

  router.beforeEach((to, from) => {
    if (!to.name || !from.name || to.name === from.name) return
    if (base(to.name) === base(from.name) && same(to.params, from.params) && same(to.query, from.query) && to.hash === from.hash)
      to.meta.scrollToTop = false
  })

  // Saqlangan joy darhol o'qiladi; Nuxt birinchi sahifani joylab, o'zi tepaga chiqargandan keyin (page:finish) tiklanadi
  let y: number | null = null
  try {
    const raw = sessionStorage.getItem('lang-scroll')
    sessionStorage.removeItem('lang-scroll')
    y = raw === null ? null : Number(raw)
  }
  catch {}
  if (y === null || !Number.isFinite(y) || y <= 0) return

  let stop = false
  const cancel = () => (stop = true)
  window.addEventListener('wheel', cancel, { once: true, passive: true })
  window.addEventListener('touchstart', cancel, { once: true, passive: true })
  nuxtApp.hook('page:finish', () => {
    // Rasmlar va kech yuklanadigan bloklar joylashguncha ~2 s davomida o'sha joyda ushlab turiladi
    let tries = 0
    const hold = () => {
      if (stop || tries++ > 20) return
      if (Math.abs(window.scrollY - y!) > 4) window.scrollTo({ top: y!, behavior: 'instant' as ScrollBehavior })
      setTimeout(hold, 100)
    }
    setTimeout(hold, 0)
  })
})
