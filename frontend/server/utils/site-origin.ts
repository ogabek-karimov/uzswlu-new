import type { H3Event } from 'h3'

/**
 * Saytning ochiq manzili (sitemap, robots.txt, canonical uchun): `NUXT_PUBLIC_SITE_URL`,
 * berilmasa — so'rov kelgan manzil (nginx `Host`/`X-Forwarded-*` ni uzatsa to'g'ri chiqadi).
 */
export function siteOrigin(event: H3Event): string {
  const configured = String(useRuntimeConfig(event).public.siteUrl || '').trim()
  if (configured) {
    try { return new URL(configured).origin }
    catch { /* noto'g'ri qiymat — so'rov manziliga o'tamiz */ }
  }
  return getRequestURL(event, { xForwardedHost: true, xForwardedProto: true }).origin
}
