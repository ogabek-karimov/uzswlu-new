// Sahifa qayta yuklanganda joy bir tekis tiklanadi (sakramaydi).
// 1) Til tanlagich sahifani to'liq qayta yuklaydi (aralash til bo'lmasin) — bosishdan oldin scrollY saqlanadi (LangSwitcher),
//    yangi tildagi sahifa ochilgach o'sha joyga qaytariladi.
// 2) F5 / «Yangilash»: brauzerning o'z tiklashi o'chiriladi (u `scroll-behavior: smooth` bilan sekin aylantirar, keyin Nuxt
//    tepaga chiqarar, rasmlar yuklanib yana siljirdi — sahifa pastga-tepaga sakrardi). Joy ketishdan oldin saqlanadi va
//    sahifa ochilishi bilan darhol (animatsiyasiz) o'sha joyga qo'yiladi.
// 3) SPA ichida faqat til o'zgargan o'tishda Nuxt'ning «tepaga chiq»i o'chiriladi (meta.scrollToTop = false).
export default defineNuxtPlugin((nuxtApp) => {
  const router = useRouter()
  const base = (name: unknown) => String(name ?? '').split('___')[0]
  const same = (a: object, b: object) => JSON.stringify(a) === JSON.stringify(b)

  router.beforeEach((to, from) => {
    if (!to.name || !from.name || to.name === from.name) return
    if (base(to.name) === base(from.name) && same(to.params, from.params) && same(to.query, from.query) && to.hash === from.hash)
      to.meta.scrollToTop = false
  })

  const here = () => location.pathname + location.search
  try {
    history.scrollRestoration = 'manual'
  }
  catch {}
  window.addEventListener('pagehide', () => {
    try {
      sessionStorage.setItem('reload-scroll', JSON.stringify({ url: here(), y: Math.round(window.scrollY) }))
    }
    catch {}
  })

  let y: number | null = null
  try {
    const raw = sessionStorage.getItem('lang-scroll')
    const saved = JSON.parse(sessionStorage.getItem('reload-scroll') ?? 'null') as { url?: string; y?: number } | null
    sessionStorage.removeItem('lang-scroll')
    sessionStorage.removeItem('reload-scroll')
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
    if (raw !== null) y = Number(raw)
    else if ((nav?.type === 'reload' || nav?.type === 'back_forward') && saved?.url === here() && !location.hash) y = Number(saved.y)
  }
  catch {}
  if (y === null || !Number.isFinite(y) || y <= 0) return

  const jump = () => {
    if (Math.abs(window.scrollY - y!) > 4) window.scrollTo({ top: y!, behavior: 'instant' as ScrollBehavior })
  }
  // Server sahifasi (SSR) allaqachon chizilgan — tepani ko'rsatmay darhol joyiga
  jump()

  let stop = false
  const cancel = () => (stop = true)
  for (const ev of ['wheel', 'touchstart', 'keydown', 'mousedown'] as const)
    window.addEventListener(ev, cancel, { once: true, passive: true })
  nuxtApp.hook('page:finish', () => {
    // Rasmlar va kech yuklanadigan bloklar joylashguncha ~2 s davomida o'sha joyda ushlab turiladi
    let tries = 0
    const hold = () => {
      if (stop || tries++ > 20) return
      jump()
      setTimeout(hold, 100)
    }
    setTimeout(hold, 0)
  })
})
