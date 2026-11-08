import type { H3Event } from 'h3'

/**
 * Yuklash so'rovi hajmini fayl xotiraga o'qilishidan OLDIN `Content-Length` bo'yicha tekshiradi.
 * `readMultipartFormData` butun so'rovni xotiraga yuklaydi — katta so'rov serverni to'ldirib yubormasligi uchun.
 */
export function assertUploadSize(event: H3Event, maxBytes: number) {
  const raw = getHeader(event, 'content-length')
  if (!raw || !/^\d+$/.test(raw)) throw createError({ statusCode: 411, statusMessage: 'Content-Length required' })
  if (Number(raw) > maxBytes) throw createError({ statusCode: 413, statusMessage: 'Payload too large' })
}
