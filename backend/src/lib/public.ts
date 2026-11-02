import type { PayloadRequest } from 'payload'
import { isLang, type Lang } from './i18n'

// Sayt (Nuxt) uchun ochiq API yordamchilari

export type MediaDoc = { id?: number; url?: string | null; filename?: string | null; mimeType?: string | null; filesize?: number | null; sizes?: Record<string, { url?: string | null } | undefined> } | null

export const json = (data: unknown, status = 200) => Response.json(data, { status })

export const publicUrl = (url?: string | null) => {
  if (!url) return null
  if (/^https?:\/\//.test(url)) return url
  return `${(process.env.PUBLIC_SERVER_URL ?? '').replace(/\/$/, '')}${url}`
}

export const imageOf = (media: MediaDoc | number | undefined, size: 'thumb' | 'card' | 'hero' = 'card') =>
  media && typeof media === 'object' ? publicUrl(media.sizes?.[size]?.url ?? media.url) : null

export const fileOf = (media: MediaDoc | number | undefined) =>
  media && typeof media === 'object' ? publicUrl(media.url) : null

export function langOf(req: PayloadRequest): Lang {
  const lang = req.searchParams.get('lang')
  return isLang(lang) ? lang : 'uz'
}

/** PDF hajmi: kichik fayllar KB'da ("0,0 MB" chiqmasin) */
export function sizeLabel(bytes?: number | null) {
  if (!bytes) return null
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}
