import type { H3Event } from 'h3'
import { createLastGood } from './last-good'
import { rewriteMediaUrls } from './media-cache'

/**
 * Backend API'ga server tomondan so'rov. Token faqat shu yerda ishlatiladi
 * va brauzerga hech qachon chiqmaydi.
 *
 * Ommaviy (GET) so'rovlar «oxirgi yaxshi javob» qatlamidan o'tadi: backend o'chib qolsa, sayt
 * oxirgi muvaffaqiyatli javobni `staleIfErrorSeconds` (standart 3 soat) davomida ko'rsatadi.
 */

type LastGood = ReturnType<typeof createLastGood>
let lastGood: LastGood | undefined

function store(event: H3Event): LastGood {
  if (!lastGood) {
    const config = useRuntimeConfig(event)
    lastGood = createLastGood({
      maxStaleMs: Math.max(0, Number(config.staleIfErrorSeconds) || 0) * 1000,
      cooldownMs: Math.max(1, Number(config.backendCooldownSeconds) || 15) * 1000,
      maxEntries: 600,
    })
  }
  return lastGood
}

/** Javobdagi backend rasm havolalarini saytning o'z `/media/...` manziliga buramiz (media keshi shu yerdan o'tadi) */
function mediaOrigins(event: H3Event): string[] {
  const { mediaPublicOrigin, mediaUpstream, apiBase, cmsBase } = useRuntimeConfig(event)
  const origins = new Set<string>()
  for (const raw of [mediaPublicOrigin, mediaUpstream, apiBase, cmsBase]) {
    try { if (raw) origins.add(new URL(String(raw)).origin) }
    catch { /* noto'g'ri manzil — o'tkazib yuboramiz */ }
  }
  return [...origins]
}

function stableQuery(query?: Record<string, unknown>): string {
  if (!query) return ''
  return Object.keys(query).sort()
    .filter(k => query[k] !== undefined && query[k] !== null && query[k] !== '')
    .map(k => `${k}=${String(query[k])}`)
    .join('&')
}

/** Cheksiz xilma-xil kalitlar (qidiruv) saqlanmaydi — xotira to'lib ketmasligi uchun */
function worthKeeping(path: string, query?: Record<string, unknown>): boolean {
  return !path.startsWith('/search') && !(query && query.q)
}

async function withLastGood<T>(
  event: H3Event,
  scope: string,
  path: string,
  query: Record<string, unknown> | undefined,
  fetcher: () => Promise<T>,
): Promise<T> {
  const { value, staleAgeMs } = await store(event).run(
    `${scope}:${path}?${stableQuery(query)}`,
    fetcher,
    worthKeeping(path, query),
    error => console.error(`[backend] javob bermayapti, saqlangan nusxa ishlatiladi: ${(error as Error).message}`),
  )
  if (staleAgeMs !== undefined) {
    // Kuzatish uchun: javob eski nusxadan berilgan (soniyada yoshi)
    setResponseHeader(event, 'x-stale-age', Math.round(staleAgeMs / 1000))
  }
  return value
}

export function backendFetch<T>(event: H3Event, path: string, query?: Record<string, unknown>): Promise<T> {
  const { apiBase, apiToken } = useRuntimeConfig(event)

  return withLastGood<T>(event, `api:${apiBase}`, path, query, async () => rewriteMediaUrls(await $fetch<T>(path, {
    baseURL: apiBase,
    query,
    timeout: 8000,
    headers: apiToken ? { Authorization: `Bearer ${apiToken}` } : undefined,
  }), mediaOrigins(event)))
}

/** O'zimizning CMS (Payload) ochiq API'si: yangiliklar, e'lonlar, tadbirlar */
export function cmsFetch<T>(event: H3Event, path: string, query?: Record<string, unknown>): Promise<T> {
  const { cmsBase } = useRuntimeConfig(event)
  return withLastGood<T>(event, `cms:${cmsBase}`, path, query, async () => rewriteMediaUrls(await $fetch<T>(path, { baseURL: cmsBase, query, timeout: 8000 }), mediaOrigins(event)))
}

/**
 * Kirgan xodim nomidan so'rov (kabinet): brauzerdan kelgan sessiya cookie'si yoki
 * Authorization sarlavhasi backend'ga uzatiladi. Kirmagan bo'lsa backend 401 qaytaradi.
 * Shaxsiy ma'lumot — hech qachon eski nusxadan berilmaydi.
 */
export function backendUserFetch<T>(event: H3Event, path: string, options: { method?: 'GET' | 'PATCH' | 'POST' | 'DELETE'; query?: Record<string, unknown>; body?: BodyInit | Record<string, unknown> } = {}) {
  const { apiBase } = useRuntimeConfig(event)
  const headers: Record<string, string> = {}
  const cookie = getHeader(event, 'cookie')
  const authorization = getHeader(event, 'authorization')
  if (cookie) headers.cookie = cookie
  if (authorization) headers.authorization = authorization

  return $fetch<T>(path, {
    baseURL: apiBase,
    method: options.method ?? 'GET',
    query: options.query,
    body: options.body,
    timeout: 20000,
    headers,
  })
}
