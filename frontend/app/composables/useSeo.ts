import type { MaybeRefOrGetter } from 'vue'

/** Ijtimoiy tarmoq (Telegram, Facebook, X) uchun standart rasm: `public/og-default.jpg` (1200×630) */
export const DEFAULT_OG_IMAGE = '/og-default.jpg'

const OG_LOCALE: Record<string, string> = { uz: 'uz_UZ', ru: 'ru_RU', en: 'en_US', zh: 'zh_CN' }

/** Saytning ochiq manzili: `NUXT_PUBLIC_SITE_URL`, bo'lmasa — hozirgi so'rov manzili. Oxirida `/` yo'q. */
export function useSiteOrigin(): string {
  const configured = String(useRuntimeConfig().public.siteUrl || '').trim().replace(/\/+$/, '')
  if (configured) return configured
  return useRequestURL().origin
}

/**
 * Sahifaning SEO va ijtimoiy preview ma'lumoti (title, description, Open Graph, Twitter, rasm).
 * Har bir sahifa `useSeo({ title, description, image, type })` chaqiradi; berilmagan qismlar saytning umumiy qiymati bilan to'ldiriladi.
 */
export function useSeo(options: {
  title?: MaybeRefOrGetter<string | null | undefined>
  description?: MaybeRefOrGetter<string | null | undefined>
  image?: MaybeRefOrGetter<string | null | undefined>
  type?: 'website' | 'article' | 'profile'
  noindex?: boolean
} = {}) {
  const { t } = useI18n()
  const origin = useSiteOrigin()
  const title = computed(() => toValue(options.title) || undefined)
  const description = computed(() => (toValue(options.description) || '').replace(/\s+/g, ' ').trim().slice(0, 300) || t('meta.description'))
  const image = computed(() => absoluteUrl(origin, toValue(options.image) || DEFAULT_OG_IMAGE))
  const ogTitle = computed(() => (title.value ? `${title.value} — ${t('university.short')}` : t('university.name')))

  useSeoMeta({
    title,
    description,
    ogTitle,
    ogDescription: description,
    ogImage: image,
    twitterTitle: ogTitle,
    twitterDescription: description,
    twitterImage: image,
    ogType: options.type ?? 'website',
    ...(options.noindex ? { robots: 'noindex, nofollow' } : {}),
  })
}

/** Barcha sahifalar uchun umumiy teglar (app.vue): canonical, hreflang, og:url, og:locale, twitter:card */
export function useSiteSeo() {
  const { t, locale, locales } = useI18n()
  const route = useRoute()
  const switchLocalePath = useSwitchLocalePath()
  const origin = useSiteOrigin()
  const i18nHead = useLocaleHead()

  const codes = computed(() => (locales.value as { code: string }[]).map(l => l.code))
  const urlFor = (code: string) => absoluteUrl(origin, switchLocalePath(code as never) || route.path)
  const canonical = computed(() => urlFor(locale.value))

  useHead(() => ({
    htmlAttrs: { lang: i18nHead.value.htmlAttrs?.lang },
    // i18n moduli canonical/alternate'ni o'zining baseUrl'idan yasaydi; domen muhitdan kelishi uchun o'zimiznikini beramiz
    link: [
      ...(i18nHead.value.link ?? []).filter(l => l.rel !== 'canonical' && l.rel !== 'alternate'),
      { rel: 'canonical', href: canonical.value },
      ...codes.value.map(code => ({ rel: 'alternate', hreflang: code, href: urlFor(code) })),
      { rel: 'alternate', hreflang: 'x-default', href: urlFor('uz') },
    ],
    meta: [
      ...(i18nHead.value.meta ?? []).filter(m => !String(m.property ?? '').startsWith('og:')),
      { name: 'theme-color', content: '#1c1548' },
    ],
    titleTemplate: (title?: string) => (title ? `${title} — ${t('university.short')}` : t('university.name')),
  }))

  useSeoMeta({
    description: () => t('meta.description'),
    ogSiteName: () => t('university.name'),
    ogUrl: canonical,
    ogLocale: () => OG_LOCALE[locale.value] ?? 'uz_UZ',
    ogLocaleAlternate: () => codes.value.filter(c => c !== locale.value).map(c => OG_LOCALE[c] ?? c),
    ogType: 'website',
    ogTitle: () => t('university.name'),
    ogDescription: () => t('meta.description'),
    ogImage: () => absoluteUrl(origin, DEFAULT_OG_IMAGE),
    ogImageWidth: 1200,
    ogImageHeight: 630,
    twitterCard: 'summary_large_image',
    twitterTitle: () => t('university.name'),
    twitterDescription: () => t('meta.description'),
    twitterImage: () => absoluteUrl(origin, DEFAULT_OG_IMAGE),
  })
}
