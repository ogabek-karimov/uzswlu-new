import { createByteCache, safeMediaPath } from '../../utils/media-cache'
import { isBackendFailure } from '../../utils/last-good'

// Rasm va hujjatlar: sayt backenddan olib vaqtincha xotirada saqlaydi. Backend o'chib qolsa,
// saqlangan fayl `staleIfErrorSeconds` (3 soat) davomida beriladi. Katta va boshqa turdagi fayllar
// (video, katta PDF) keshlanmasdan, Range bilan to'g'ridan-to'g'ri uzatiladi.
const MAX_FILE_BYTES = 5 * 1024 * 1024
const MAX_TOTAL_BYTES = 96 * 1024 * 1024
const FRESH_MS = 60 * 60 * 1000 // shuncha vaqt backendga bormasdan beriladi (fayl almashsa URL ham o'zgaradi)
const CACHEABLE = /^(image\/|application\/pdf)/

const cache = createByteCache(MAX_TOTAL_BYTES)
let downUntil = 0

function upstreamOrigin(event: Parameters<typeof useRuntimeConfig>[0]): string {
  const { mediaUpstream, apiBase, cmsBase } = useRuntimeConfig(event)
  const base = String(mediaUpstream || apiBase || cmsBase || '')
  try { return new URL(base).origin }
  catch { return '' }
}

export default defineEventHandler(async (event) => {
  const path = safeMediaPath(getRouterParam(event, 'path'))
  if (!path) throw createError({ statusCode: 400, statusMessage: 'Bad media path' })

  const origin = upstreamOrigin(event)
  if (!origin) throw createError({ statusCode: 404, statusMessage: 'Media is not configured' })
  const target = new URL(`/media/${path}`, origin)
  if (target.origin !== origin || !target.pathname.startsWith('/media/')) {
    throw createError({ statusCode: 400, statusMessage: 'Bad media path' })
  }

  const maxStaleMs = Math.max(0, Number(useRuntimeConfig(event).staleIfErrorSeconds) || 0) * 1000
  const key = target.pathname
  const range = getHeader(event, 'range')
  const hit = range ? undefined : cache.get(key)

  const serve = (file: NonNullable<typeof hit>, stale: boolean) => {
    setResponseHeaders(event, {
      'content-type': file.type,
      'cache-control': 'public, max-age=3600',
      ...(file.etag ? { etag: file.etag } : {}),
      ...(file.lastModified ? { 'last-modified': file.lastModified } : {}),
      ...(stale ? { 'x-stale-age': String(Math.round((Date.now() - file.at) / 1000)) } : {}),
    })
    return file.body
  }

  // Yangi nusxa bor yoki backend yaqinda yiqilgan — tarmoqqa bormaymiz
  if (hit && (Date.now() - hit.at < FRESH_MS || Date.now() < downUntil)) {
    return serve(hit, Date.now() - hit.at >= FRESH_MS)
  }

  try {
    const res = await fetch(target, {
      headers: range ? { range } : undefined,
      signal: AbortSignal.timeout(8000),
    })
    downUntil = 0
    if (res.status >= 500 || res.status === 429) throw Object.assign(new Error(`HTTP ${res.status}`), { status: res.status })
    if (res.status === 404) throw createError({ statusCode: 404, statusMessage: 'Not found' })
    if (!res.ok && res.status !== 206) throw createError({ statusCode: res.status })

    const type = res.headers.get('content-type') ?? 'application/octet-stream'
    const length = Number(res.headers.get('content-length') ?? Number.NaN)
    const cacheable = res.status === 200 && !range && CACHEABLE.test(type) && length <= MAX_FILE_BYTES

    if (!cacheable) {
      // Keshlanmaydi: oqim bilan (Range ham) to'g'ridan-to'g'ri uzatiladi
      setResponseStatus(event, res.status)
      for (const h of ['content-type', 'content-length', 'content-range', 'accept-ranges', 'etag', 'last-modified']) {
        const v = res.headers.get(h)
        if (v) setResponseHeader(event, h, v)
      }
      setResponseHeader(event, 'cache-control', 'public, max-age=3600')
      return sendStream(event, res.body as ReadableStream)
    }

    const body = new Uint8Array(await res.arrayBuffer())
    cache.set(key, { body, type, etag: res.headers.get('etag') ?? undefined, lastModified: res.headers.get('last-modified') ?? undefined })
    setResponseHeaders(event, { 'content-type': type, 'cache-control': 'public, max-age=3600' })
    const etag = res.headers.get('etag')
    if (etag) setResponseHeader(event, 'etag', etag)
    return body
  }
  catch (error) {
    if (!isBackendFailure(error)) throw error
    downUntil = Date.now() + 15_000
    if (hit && Date.now() - hit.at <= maxStaleMs) return serve(hit, true)
    throw createError({ statusCode: 502, statusMessage: 'Media is temporarily unavailable' })
  }
})
