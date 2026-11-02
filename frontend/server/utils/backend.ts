import type { H3Event } from 'h3'

/**
 * Backend API'ga server tomondan so'rov. Token faqat shu yerda ishlatiladi
 * va brauzerga hech qachon chiqmaydi.
 */
export function backendFetch<T>(event: H3Event, path: string, query?: Record<string, unknown>) {
  const { apiBase, apiToken } = useRuntimeConfig(event)

  return $fetch<T>(path, {
    baseURL: apiBase,
    query,
    timeout: 8000,
    headers: apiToken ? { Authorization: `Bearer ${apiToken}` } : undefined,
  })
}

/** O'zimizning CMS (Payload) ochiq API'si: yangiliklar, e'lonlar, tadbirlar */
export function cmsFetch<T>(event: H3Event, path: string, query?: Record<string, unknown>) {
  const { cmsBase } = useRuntimeConfig(event)
  return $fetch<T>(path, { baseURL: cmsBase, query, timeout: 8000 })
}

/**
 * Kirgan xodim nomidan so'rov (kabinet): brauzerdan kelgan sessiya cookie'si yoki
 * Authorization sarlavhasi backend'ga uzatiladi. Kirmagan bo'lsa backend 401 qaytaradi.
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
