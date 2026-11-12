// Til almashtirilganda sahifa tepasiga sakramaydi: faqat til o'zgarsa (o'sha sahifa, o'sha parametrlar),
// Nuxt'ning standart scrollBehavior'iga «tepaga chiqma» deyiladi (meta.scrollToTop = false) — joy saqlanadi.
// Boshqa hamma o'tishlar avvalgidek: yangi sahifa tepadan, «orqaga» — saqlangan joyga, #hash — elementga.
export default defineNuxtPlugin(() => {
  const router = useRouter()
  const base = (name: unknown) => String(name ?? '').split('___')[0]
  const same = (a: object, b: object) => JSON.stringify(a) === JSON.stringify(b)

  router.beforeEach((to, from) => {
    if (!to.name || !from.name || to.name === from.name) return
    if (base(to.name) === base(from.name) && same(to.params, from.params) && same(to.query, from.query) && to.hash === from.hash)
      to.meta.scrollToTop = false
  })
})
