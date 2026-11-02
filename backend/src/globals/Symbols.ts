import type { GlobalConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup } from '../lib/i18n'
import { trackGlobal } from '../lib/track'

const symbol = (name: 'emblem' | 'flag' | 'anthem', label: string, defaults: { title: Record<string, string>; link: string; source: string }) => ({
  name,
  label,
  type: 'group' as const,
  fields: [
    { name: 'image', label: 'Rasm', type: 'upload' as const, relationTo: 'media' as const },
    ...(name === 'anthem' ? [{ name: 'audio', label: 'Audio', type: 'upload' as const, relationTo: 'media' as const }] : []),
    i18nGroup('title', 'Sarlavha', { defaults: defaults.title }),
    i18nGroup('description', 'Tavsif', { type: 'textarea' }),
    { name: 'link', label: 'Rasmiy manba havolasi', type: 'text' as const, defaultValue: defaults.link },
    { name: 'source', label: 'Manba nomi', type: 'text' as const, defaultValue: defaults.source },
  ],
})

// Davlat ramzlari: gerb, bayroq va madhiya (bosh sahifadagi blok)
export const Symbols: GlobalConfig = {
  slug: 'symbols',
  label: 'Ramzlar',
  access: { read: () => true, update: superOnly },
  fields: [
    symbol('emblem', 'Davlat gerbi', { title: { uz: 'Özbekiston Respublikasi davlat gerbi', ru: 'Государственный герб Республики Узбекистан', en: 'State Emblem of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国国徽' }, link: 'https://archive.uz/ozbekiston-respublikasi-davlat-gerbi', source: 'archive.uz' }),
    symbol('flag', 'Davlat bayrog‘i', { title: { uz: 'Özbekiston Respublikasi davlat bayroği', ru: 'Государственный флаг Республики Узбекистан', en: 'State Flag of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国国旗' }, link: 'https://archive.uz/ozbekiston-respublikasining-davlat-bayrogi', source: 'archive.uz' }),
    symbol('anthem', 'Davlat madhiyasi', { title: { uz: 'Özbekiston Respublikasi davlat madhiyasi', ru: 'Государственный гимн Республики Узбекистан', en: 'State Anthem of the Republic of Uzbekistan', zh: '乌兹别克斯坦共和国国歌' }, link: 'https://www.youtube.com/watch?v=rdOw_VSXbU4', source: 'YouTube' }),
  ],
  versions: { max: 50 },
  hooks: { afterChange: [trackGlobal('symbols', 'Davlat ramzlari', ['home', 'symbols'])] },
}
