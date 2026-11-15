// Kartalar ustida sichqoncha izidan yuruvchi yorug' dog' (spotlight). Bitta umumiy tinglovchi: [data-spot] elementga
// --mx/--my (px) yoziladi, ko'rinishi main.css'dagi `[data-spot]::before`. Faqat sichqoncha bor qurilmada va
// prefers-reduced-motion bo'lmaganda ishlaydi; elementni siljitmaydi (transform yo'q), shuning uchun qaltiramaydi.
export default defineNuxtPlugin(() => {
  if (!matchMedia('(hover: hover) and (pointer: fine)').matches || matchMedia('(prefers-reduced-motion: reduce)').matches) return
  let raf = 0
  document.addEventListener('pointermove', (e) => {
    const el = (e.target as Element | null)?.closest<HTMLElement>('[data-spot]')
    if (!el || raf) return
    raf = requestAnimationFrame(() => {
      raf = 0
      const r = el.getBoundingClientRect()
      el.style.setProperty('--mx', `${e.clientX - r.left}px`)
      el.style.setProperty('--my', `${e.clientY - r.top}px`)
    })
  }, { passive: true })
})
