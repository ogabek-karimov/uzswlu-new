import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: ['@nuxtjs/i18n', '@nuxt/icon', '@nuxt/fonts'],

  css: ['~/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    // Backend API manzili va kaliti (.env: NUXT_API_BASE, NUXT_API_TOKEN).
    // Faqat serverda qoladi, brauzerga chiqmaydi. Bo'sh bo'lsa — mock ma'lumot.
    apiBase: '',
    apiToken: '',
    // O'zimizning CMS (Payload) — yangiliklar, e'lonlar, tadbirlar (.env: NUXT_CMS_BASE=http://localhost:3001/api/site).
    // Berilsa postlar shu yerdan olinadi; qolgan bo'limlar hozircha apiBase/mock'dan.
    cmsBase: '',
    // Backend o'chib qolsa, oxirgi muvaffaqiyatli javob shuncha soniya ko'rsatib turiladi (.env: NUXT_STALE_IF_ERROR_SECONDS). 0 — o'chirilgan.
    staleIfErrorSeconds: 3 * 60 * 60,
    // Backend yiqilgandan keyin shuncha soniya unga bormasdan saqlangan nusxa beriladi (NUXT_BACKEND_COOLDOWN_SECONDS)
    backendCooldownSeconds: 15,
    // Rasm/fayllar sayt orqali beriladi va vaqtincha keshlanadi (/media/...). Backendning brauzerga ko'rinadigan
    // manzili (PUBLIC_SERVER_URL) — javobdagi havolalarni almashtirish uchun (NUXT_MEDIA_PUBLIC_ORIGIN).
    mediaPublicOrigin: 'http://localhost:8000',
    // Sayt serveridan backend fayllariga yo'l; bo'sh bo'lsa NUXT_API_BASE manzilidan olinadi (NUXT_MEDIA_UPSTREAM).
    mediaUpstream: '',
    public: {
      // Saytning ochiq manzili: canonical, hreflang, sitemap.xml, robots.txt, og:url (.env: NUXT_PUBLIC_SITE_URL=https://uzswlu.uz).
      // Bo'sh bo'lsa — so'rov kelgan manzil olinadi (nginx Host/X-Forwarded-* ni uzatishi shart).
      siteUrl: '',
    },
  },

  // Yuklama (ko'p tashrifchi): sahifalar CDN/nginx keshida 60 soniya turishi uchun javob sarlavhalari beriladi;
  // bosh sahifalar (4 til) Node'ning o'zida ham stale-while-revalidate bilan keshlanadi — SSR har so'rovda qayta ishlamaydi.
  // Shaxsiy yoki cheksiz xilma-xil sahifalar (kabinet, qidiruv) keshlanmaydi. Nginx namunasi: docs/10-server.md
  routeRules: {
    '/**': { headers: { 'cache-control': 'public, s-maxage=60, stale-while-revalidate=300' } },
    '/_nuxt/**': { headers: { 'cache-control': 'public, max-age=31536000, immutable' } },
    '/': { swr: 60 },
    '/ru': { swr: 60 },
    '/en': { swr: 60 },
    '/zh': { swr: 60 },
    '/dashboard': { headers: { 'cache-control': 'private, no-store' } },
    '/ru/dashboard': { headers: { 'cache-control': 'private, no-store' } },
    '/en/dashboard': { headers: { 'cache-control': 'private, no-store' } },
    '/zh/dashboard': { headers: { 'cache-control': 'private, no-store' } },
    '/search': { headers: { 'cache-control': 'private, no-store' } },
    '/ru/search': { headers: { 'cache-control': 'private, no-store' } },
    '/en/search': { headers: { 'cache-control': 'private, no-store' } },
    '/zh/search': { headers: { 'cache-control': 'private, no-store' } },
    '/api/**': { headers: { 'cache-control': 'private, no-store' } },
  },

  i18n: {
    defaultLocale: 'uz',
    strategy: 'prefix_except_default',
    detectBrowserLanguage: false,
    // Faqat modulning ichki hisob-kitobi uchun; canonical/hreflang'ni app/composables/useSeo.ts muhitdagi domen bilan yasaydi
    baseUrl: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:3000',
    locales: [
      { code: 'uz', language: 'uz-Latn-UZ', name: 'O‘zbekcha', file: 'uz.json' },
      { code: 'ru', language: 'ru-RU', name: 'Русский', file: 'ru.json' },
      { code: 'en', language: 'en-US', name: 'English', file: 'en.json' },
      { code: 'zh', language: 'zh-CN', name: '中文', file: 'zh.json' },
    ],
  },

  fonts: {
    families: [
      { name: 'Onest', provider: 'google', weights: [400, 500, 600, 700], global: true },
      { name: 'Playfair Display', provider: 'google', weights: [500, 600, 700], styles: ['normal', 'italic'], global: true },
    ],
  },

  icon: {
    clientBundle: { scan: true },
  },
})
