// Statistika: muhim harakatni yozish ("Ariza topshirish" bosildi, vizitka ulashildi …).
// Cookie va shaxsiy ma'lumotsiz — faqat harakat nomi, sahifa va til.
export function trackHit(hit: { kind: 'pageview' | 'event' | 'search'; name?: string; value?: string; path?: string; referrer?: string }) {
  if (import.meta.server) return
  try {
    const nuxt = useNuxtApp()
    const body = JSON.stringify({ path: location.pathname, lang: nuxt.$i18n?.locale.value, ...hit })
    // sendBeacon sahifa yopilayotganda ham yetkazadi; text/plain — CORS tekshiruvisiz
    if (!navigator.sendBeacon?.('/api/hit', new Blob([body], { type: 'text/plain' }))) {
      fetch('/api/hit', { method: 'POST', body, keepalive: true }).catch(() => {})
    }
  }
  catch {
    // statistika saytni hech qachon to'xtatmaydi
  }
}

export const trackEvent = (name: string, value?: string) => trackHit({ kind: 'event', name, value })
