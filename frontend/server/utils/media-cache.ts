/**
 * Media (rasm, PDF) uchun sayt ichidagi vaqtinchalik kesh — mantiq qismi.
 * Nuxt/Nitro'ga bog'liq emas, alohida sinash mumkin (`npm run test:last-good`).
 *
 *  - `rewriteMediaUrls` — API javobidagi `<backend>/media/...` havolalarini sayt ichidagi `/media/...` ga buradi,
 *    shunda brauzer rasmlarni saytdan oladi va sayt ularni keshlaydi.
 *  - `safeMediaPath` — foydalanuvchi bergan yo'ldan faqat xavfsiz `/media/...` ni qoldiradi (path traversal, SSRF).
 *  - `createByteCache` — hajm bo'yicha cheklangan (LRU) xotira keshi.
 */

/** `https://api.site.uz/media/a.jpg` → `/media/a.jpg` (matn ichida ham, ichma-ich obyektda ham) */
export function rewriteMediaUrls<T>(value: T, origins: string[]): T {
  const prefixes = origins.map(o => `${o.replace(/\/+$/, '')}/media/`).filter(p => p.length > '/media/'.length)
  if (!prefixes.length) return value

  const walk = (v: unknown): unknown => {
    if (typeof v === 'string') {
      for (const p of prefixes) {
        if (v.startsWith(p)) return `/media/${v.slice(p.length)}`
      }
      // HTML bo'lagi ichidagi havolalar (<img src="https://.../media/x.jpg">)
      if (v.includes('/media/')) {
        let out = v
        for (const p of prefixes) if (out.includes(p)) out = out.split(p).join('/media/')
        return out
      }
      return v
    }
    if (Array.isArray(v)) return v.map(walk)
    if (v && typeof v === 'object') {
      const out: Record<string, unknown> = {}
      for (const [k, x] of Object.entries(v as Record<string, unknown>)) out[k] = walk(x)
      return out
    }
    return v
  }
  return walk(value) as T
}

/**
 * So'rov yo'lini tekshiradi. Qaytaradi: `a/b.jpg` (prefikssiz, kodlangan) yoki null (xavfli).
 * `..`, teskari slash, NUL, bo'sh segment va juda uzun yo'llar rad etiladi.
 */
export function safeMediaPath(raw: unknown): string | null {
  if (typeof raw !== 'string' || !raw || raw.length > 300) return null
  let decoded: string
  try { decoded = decodeURIComponent(raw) }
  catch { return null }
  if (decoded.includes('\0') || decoded.includes('\\') || decoded.startsWith('/')) return null
  const parts = decoded.split('/')
  if (parts.some(p => p === '' || p === '.' || p === '..')) return null
  return parts.map(encodeURIComponent).join('/')
}

export interface CachedFile {
  body: Uint8Array
  type: string
  at: number
  etag?: string
  lastModified?: string
}

/** Jami hajm (bayt) bo'yicha cheklangan LRU; eng eskisi chiqariladi */
export function createByteCache(maxBytes: number, now: () => number = Date.now) {
  const map = new Map<string, CachedFile>()
  let bytes = 0

  return {
    get(key: string): CachedFile | undefined {
      const e = map.get(key)
      if (e) { map.delete(key); map.set(key, e) }
      return e
    },
    set(key: string, file: Omit<CachedFile, 'at'>) {
      if (file.body.byteLength > maxBytes) return
      const old = map.get(key)
      if (old) { bytes -= old.body.byteLength; map.delete(key) }
      map.set(key, { ...file, at: now() })
      bytes += file.body.byteLength
      while (bytes > maxBytes) {
        const oldest = map.keys().next().value
        if (oldest === undefined) break
        bytes -= map.get(oldest)!.body.byteLength
        map.delete(oldest)
      }
    },
    get size() { return map.size },
    get bytes() { return bytes },
  }
}

/** Brauzerda ochilishi mumkin turlar; boshqasi yuklab olinadi va hech qachon sahifa sifatida bajarilmaydi */
const INLINE = new Set(['image/webp', 'image/jpeg', 'image/png', 'image/gif', 'audio/mpeg', 'application/pdf'])
export const SANDBOX_CSP = "default-src 'none'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'; sandbox"

/** Backend bergan Content-Type ishonchli emas deb olinadi: ruxsat ro'yxatidagi bo'lmasa — octet-stream + attachment */
export function safeMediaHeaders(rawType: string | null | undefined, name: string): Record<string, string> {
  const type = (rawType ?? '').split(';')[0]!.trim().toLowerCase()
  const headers: Record<string, string> = { 'x-content-type-options': 'nosniff' }
  if (INLINE.has(type)) {
    headers['content-type'] = type
    if (type !== 'application/pdf') headers['content-security-policy'] = SANDBOX_CSP
  }
  else {
    let raw = name.split('/').pop() ?? 'file'
    try { raw = decodeURIComponent(raw) }
    catch { /* noto'g'ri kodlangan nom — o'z holicha */ }
    const base = raw.replace(/[^\w.\-]+/g, '_').slice(0, 120) || 'file'
    headers['content-type'] = 'application/octet-stream'
    headers['content-disposition'] = `attachment; filename="${base}"`
  }
  return headers
}
