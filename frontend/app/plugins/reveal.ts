// Bo'limlar sahifa aylantirilganda ko'rinish maydoniga kirganda silliq paydo bo'ladi (fade-in + pastdan siljish).
//   <HomeNews v-reveal />                — bo'lim bir marta paydo bo'ladi
//   <HomeFaculties v-reveal />           — ichidagi [data-reveal-item] elementlar ketma-ket (0,07 s qadam) paydo bo'ladi
// Qoidalar: server HTML'i har doim ko'rinadi (JS'siz ham o'qiladi); ekranda turgan bo'lim animatsiyasiz qoladi;
// prefers-reduced-motion yoki IntersectionObserver yo'q bo'lsa — hech narsa yashirilmaydi; animatsiyadan so'ng klasslar olib tashlanadi
// (transform qolmasin: hover/sticky/blur bilan to'qnashmasligi uchun). Stillar: main.css (.reveal).
const STEP_MS = 70
const MAX_ITEMS = 12

export default defineNuxtPlugin((nuxtApp) => {
  let io: IntersectionObserver | undefined
  const targets = new WeakMap<Element, () => void>()

  function observer() {
    return (io ??= new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        io!.unobserve(e.target)
        targets.get(e.target)?.()
        targets.delete(e.target)
      }
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 }))
  }

  function done(el: HTMLElement) {
    const clear = () => el.classList.remove('reveal', 'reveal-in')
    el.addEventListener('transitionend', clear, { once: true })
    setTimeout(clear, 1600) // transitionend kelmasa ham tozalanadi
  }

  nuxtApp.vueApp.directive('reveal', {
    // SSR: hech narsa qo'shilmaydi — kontent ko'rinib turadi
    getSSRProps: () => ({}),
    mounted(el: HTMLElement) {
      if (!import.meta.client || !(el instanceof HTMLElement)) return // v-if bo'lsa ildiz izoh (comment) bo'lishi mumkin
      if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return
      // Birinchi ekranda turgan bo'lim — animatsiyasiz (yonib-o'chib qolmasin)
      if (el.getBoundingClientRect().top < window.innerHeight * 0.9) return

      const items = Array.from(el.querySelectorAll<HTMLElement>('[data-reveal-item]')).slice(0, MAX_ITEMS)
      const hidden = items.length ? items : [el]
      for (const h of hidden) h.classList.add('reveal')

      targets.set(el, () => {
        hidden.forEach((h, i) => {
          h.style.transitionDelay = items.length ? `${i * STEP_MS}ms` : ''
          h.classList.add('reveal-in')
          done(h)
          setTimeout(() => { h.style.transitionDelay = '' }, 1600)
        })
      })
      observer().observe(el)
    },
    unmounted(el: HTMLElement) {
      io?.unobserve(el)
      targets.delete(el)
    },
  })
})
