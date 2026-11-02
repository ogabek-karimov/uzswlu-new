import type { CollectionConfig, GlobalConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup } from '../lib/i18n'
import { track, trackGlobal } from '../lib/track'

const pagesAccess = ({ req }: { req: { user?: unknown } }) => ['superadmin', 'pages'].includes((req.user as { role?: string } | null)?.role ?? '')

/** YouTube havolasidan video ID: youtu.be/ID, watch?v=ID, shorts/ID, embed/ID */
export function youtubeId(url: string | null | undefined): string | null {
  if (!url) return null
  const m = url.match(/(?:youtu\.be\/|v=|\/shorts\/|\/embed\/|\/live\/)([\w-]{11})/)
  return m?.[1] ?? null
}

// Video darsliklar toifalari (til kurslari). greeting — kartadagi bezak so'z ("Hello", "你好")
export const VideoCategories: CollectionConfig = {
  slug: 'video-categories',
  labels: { singular: 'Video toifasi', plural: 'Video toifalari' },
  defaultSort: 'order',
  access: { read: () => true, create: pagesAccess, update: pagesAccess, delete: superOnly },
  fields: [
    { name: 'key', label: 'Til kodi', type: 'text', required: true, unique: true },
    i18nGroup('title', 'Nomi', { required: true }),
    { name: 'greeting', label: 'Bezak so‘z', type: 'text' },
    { name: 'order', type: 'number', defaultValue: 0 },
  ],
  hooks: track('video-categories', { label: d => d.title?.uz, fields: ['key', 'title', 'greeting', 'order'], tags: ['videos'] }),
}

// Videolar YouTube'da turadi — saytda faqat havola, nom va muqova
export const Videos: CollectionConfig = {
  slug: 'videos',
  labels: { singular: 'Video', plural: 'Videolar' },
  defaultSort: 'order',
  access: { read: () => true, create: pagesAccess, update: pagesAccess, delete: pagesAccess },
  fields: [
    { name: 'url', label: 'YouTube havolasi', type: 'text', required: true },
    i18nGroup('title', 'Nomi', { required: true }),
    { name: 'category', label: 'Toifa', type: 'relationship', relationTo: 'video-categories', required: true, index: true },
    { name: 'teacher', label: 'O‘qituvchi', type: 'text' },
    { name: 'duration', label: 'Davomiyligi', type: 'text' },
    { name: 'thumbnail', label: 'Muqova', type: 'text' },
    { name: 'order', type: 'number', defaultValue: 0, index: true },
  ],
  hooks: {
    beforeChange: [
      ({ data }) => {
        const id = youtubeId(data.url)
        if (id && !data.thumbnail) data.thumbnail = `https://i.ytimg.com/vi/${id}/hqdefault.jpg`
        return data
      },
    ],
    ...track('videos', { label: d => d.title?.uz, fields: ['url', 'title', 'category', 'teacher', 'duration', 'order'], tags: ['videos'] }),
  },
}

// Video sahifasi: jonli efir va YouTube kanal
export const VideoPage: GlobalConfig = {
  slug: 'video-page',
  label: 'Video sahifasi',
  access: { read: () => true, update: pagesAccess },
  fields: [
    { name: 'live', label: 'Hozir jonli efirda', type: 'checkbox', defaultValue: false },
    { name: 'liveUrl', label: 'Efir havolasi', type: 'text' },
    i18nGroup('nextTitle', 'Keyingi efir nomi'),
    { name: 'nextAt', label: 'Keyingi efir vaqti', type: 'date' },
    { name: 'channelUrl', label: 'YouTube kanal', type: 'text', defaultValue: 'https://www.youtube.com/c/Ozbekistondavlatjahontillariuniversiteti' },
  ],
  hooks: { afterChange: [trackGlobal('video-page', 'Video sahifasi', ['videos'])] },
}
