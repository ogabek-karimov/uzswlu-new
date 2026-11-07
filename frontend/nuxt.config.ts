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
    public: {
      siteUrl: 'http://localhost:3000',
    },
  },

  i18n: {
    defaultLocale: 'uz',
    strategy: 'prefix_except_default',
    detectBrowserLanguage: false,
    baseUrl: 'http://localhost:3000',
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
