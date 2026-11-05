/**
 * Surat o'lchami (eni va bo'yi) — faylning boshidagi bir necha baytdan, butun faylni yuklamasdan.
 * PNG, JPEG, WebP, GIF. Maqola sahifasi suratning tik yoki yotiqligini oldindan bilishi uchun
 * (sahifa ochilganda joylashuv sakramaydi). Fayl almashsa URL ham o'zgaradi — natija uzoq keshlanadi.
 */
export interface ImageSize { width: number; height: number }

const MAX_BYTES = 256 * 1024

const u16be = (b: Uint8Array, i: number) => (b[i]! << 8) | b[i + 1]!
const u16le = (b: Uint8Array, i: number) => b[i]! | (b[i + 1]! << 8)
const u24le = (b: Uint8Array, i: number) => b[i]! | (b[i + 1]! << 8) | (b[i + 2]! << 16)
const u32be = (b: Uint8Array, i: number) => ((b[i]! << 24) | (b[i + 1]! << 16) | (b[i + 2]! << 8) | b[i + 3]!) >>> 0
const ascii = (b: Uint8Array, i: number, n: number) => String.fromCharCode(...b.subarray(i, i + n))

/** undefined — yana bayt kerak, null — format tanilmadi */
function parse(b: Uint8Array): ImageSize | null | undefined {
  if (b.length < 30) return undefined
  // PNG: IHDR bo'lagi doim birinchi
  if (b[0] === 0x89 && ascii(b, 1, 3) === 'PNG') return { width: u32be(b, 16), height: u32be(b, 20) }
  if (ascii(b, 0, 4) === 'GIF8') return { width: u16le(b, 6), height: u16le(b, 8) }
  if (ascii(b, 0, 4) === 'RIFF' && ascii(b, 8, 4) === 'WEBP') {
    const chunk = ascii(b, 12, 4)
    if (chunk === 'VP8 ') return { width: u16le(b, 26) & 0x3fff, height: u16le(b, 28) & 0x3fff }
    if (chunk === 'VP8L') {
      return {
        width: 1 + (((b[22]! & 0x3f) << 8) | b[21]!),
        height: 1 + (((b[24]! & 0x0f) << 10) | (b[23]! << 2) | ((b[22]! & 0xc0) >> 6)),
      }
    }
    if (chunk === 'VP8X') return { width: 1 + u24le(b, 24), height: 1 + u24le(b, 27) }
    return null
  }
  // JPEG: SOF markerigacha bo'laklar bo'ylab yuramiz
  if (b[0] === 0xff && b[1] === 0xd8) {
    let i = 2
    while (i + 9 < b.length) {
      if (b[i] !== 0xff) { i++; continue }
      const marker = b[i + 1]!
      if (marker === 0xff) { i++; continue }
      if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
        return { width: u16be(b, i + 7), height: u16be(b, i + 5) }
      }
      if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd8)) { i += 2; continue }
      i += 2 + u16be(b, i + 2)
    }
    return undefined
  }
  return null
}

async function probe(url: string): Promise<ImageSize | null> {
  const res = await fetch(url, { headers: { Range: `bytes=0-${MAX_BYTES - 1}` }, signal: AbortSignal.timeout(4000) })
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)
  const reader = res.body.getReader()
  let buffer = new Uint8Array(0)
  try {
    while (buffer.length < MAX_BYTES) {
      const { done, value } = await reader.read()
      if (done) break
      const next = new Uint8Array(buffer.length + value.length)
      next.set(buffer)
      next.set(value, buffer.length)
      buffer = next
      const size = parse(buffer)
      if (size !== undefined) return size && size.width > 0 && size.height > 0 ? size : null
    }
    return parse(buffer) ?? null
  }
  finally {
    await reader.cancel().catch(() => {})
  }
}

/** Tarmoq xatosi keshlanmaydi (keyingi so'rovda qayta urinadi), tanilmagan format esa keshlanadi */
export const imageSize = defineCachedFunction(probe, {
  name: 'image-size',
  maxAge: 60 * 60 * 24 * 30,
  getKey: (url: string) => url,
})
