/**
 * Ichki raqamlar ro'yxatini ko'rsatish uchun: "1061–1064" (diapazon) → "1061, 1062, 1063, 1064".
 * Vergul bilan berilgan ro'yxat o'zgarmaydi; tushunarsiz matn o'z holicha qaytadi. Diapazon 20 tadan oshmasa yoyiladi.
 */
export function formatExtensions(value?: string | null): string {
  const text = (value ?? '').trim()
  if (!text) return ''
  return text
    .split(/\s*[,;]\s*/)
    .flatMap((part) => {
      const m = part.match(/^(\d{2,6})\s*[–—-]\s*(\d{2,6})$/)
      if (!m) return [part]
      const [from, to] = [Number(m[1]), Number(m[2])]
      if (to < from || to - from > 19) return [part]
      return Array.from({ length: to - from + 1 }, (_, i) => String(from + i).padStart(m[1]!.length, '0'))
    })
    .join(', ')
}
