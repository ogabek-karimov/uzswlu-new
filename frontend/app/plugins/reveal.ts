// Bo'limlar sahifa aylantirilganda ko'rinish maydoniga kirganda silliq paydo bo'ladi (fade-in + pastdan siljish).
//   <HomeNews v-reveal />                — bo'lim bir marta paydo bo'ladi
//   <HomeFaculties v-reveal />           — ichidagi [data-reveal-item] kartalar har biri o'zi ekranga kirganda, navbat bilan (0,12 s) paydo bo'ladi
// Qoidalar: server HTML'i har doim ko'rinadi (JS'siz ham o'qiladi); ekranda turgan bo'lim animatsiyasiz qoladi;
// prefers-reduced-motion yoki IntersectionObserver yo'q bo'lsa — hech narsa yashirilmaydi; animatsiyadan so'ng klasslar olib tashlanadi
// (transform qolmasin: hover/sticky/blur bilan to'qnashmasligi uchun). Stillar: main.css (.reveal).
const STEP_MS = 120 // birga ko'ringan kartalar orasidagi navbat
const MAX_STEPS = 8

export default defineNuxtPlugin((nuxtApp) => {
  let io: IntersectionObserver | undefined
  const watched = new WeakMap<Element, HTMLElement[]>()

  function done(el: HTMLElement) {
    const clear = () => {
      el.classList.remove('reveal', 'reveal-in')
      el.style.transitionDelay = ''
    }
    el.addEventListener('transitionend', clear, { once: true })
    setTimeout(clear, 2200) // transitionend kelmasa ham tozalanadi
  }

  // Har bir karta o'zi ekranga kirganda chiqadi; bir vaqtda kirganlar — yuqoridan pastga, chapdan o'ngga navbat bilan
  function observer() {
    return (io ??= new IntersectionObserver((entries) => {
      const shown = entries
        .filter(e => e.isIntersecting)
        .map(e => e.target as HTMLElement)
        .sort((a, b) => {
          const ra = a.getBoundingClientRect()
          const rb = b.getBoundingClientRect()
          return Math.round(ra.top - rb.top) || ra.left - rb.left
        })
      shown.forEach((el, i) => {
        io!.unobserve(el)
        el.style.transitionDelay = `${Math.min(i, MAX_STEPS) * STEP_MS}ms`
        el.classList.add('reveal-in')
        done(el)
      })
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.12 }))
  }

  // Sahifalararo o'tish holati: router o'tishni boshlaganda — true; Nuxt sahifani joylab, aylantirishni tugatgach — false
  let navigating = false
  const pending: (() => void)[] = []
  const router = useRouter()
  let fallback: ReturnType<typeof setTimeout> | undefined
  const flush = () => {
    clearTimeout(fallback)
    navigating = false
    pending.splice(0).forEach(fn => fn())
  }
  router.beforeEach((to, from) => {
    if (!from.matched.length || to.path === from.path) return
    navigating = true
    clearTimeout(fallback)
    fallback = setTimeout(flush, 1500) // zaxira: hook kelmasa ham kartalar yashirin qolib ketmaydi
  })
  nuxtApp.hook('page:loading:end', () => {
    if (!navigating) return
    // Nuxt'ning scrollBehavior'i ham shu hook'dan keyin requestAnimationFrame'da ishlaydi — ikki kadr kutamiz
    requestAnimationFrame(() => requestAnimationFrame(flush))
  })
  const afterNavigation = (fn: () => void) => (navigating ? pending.push(fn) : fn())

  nuxtApp.vueApp.directive('reveal', {
    // SSR: hech narsa qo'shilmaydi — kontent ko'rinib turadi
    getSSRProps: () => ({}),
    mounted(el: HTMLElement) {
      if (!import.meta.client || !(el instanceof HTMLElement)) return // v-if bo'lsa ildiz izoh (comment) bo'lishi mumkin
      if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return
      const items = Array.from(el.querySelectorAll<HTMLElement>('[data-reveal-item]'))
      const all = items.length ? items : [el]
      // Sahifadan sahifaga o'tishda (SPA): yangi sahifa avval eski aylantirish joyida chiziladi, keyin tepaga chiqadi —
      // shuning uchun hammasi darhol yashiriladi va sahifa joylashgach kuzatiladi (birinchi ekrandagilar ham navbat bilan chiqadi)
      if (navigating) {
        for (const h of all) h.classList.add('reveal')
        watched.set(el, all)
        afterNavigation(() => {
          for (const h of all) if (h.isConnected) observer().observe(h)
        })
        return
      }
      // Birinchi yuklanish: ekranda turgan narsa animatsiyasiz qoladi (server HTML'i yonib-o'chib qolmasin)
      const below = (n: HTMLElement) => n.getBoundingClientRect().top > window.innerHeight * 0.92
      const hidden = all.filter(below)
      for (const h of hidden) {
        h.classList.add('reveal')
        observer().observe(h)
      }
      watched.set(el, hidden)
    },
    unmounted(el: HTMLElement) {
      for (const h of watched.get(el) ?? []) io?.unobserve(h)
      watched.delete(el)
    },
  })
})
