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
