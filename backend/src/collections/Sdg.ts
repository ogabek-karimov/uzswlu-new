import type { CollectionConfig, GlobalConfig } from 'payload'
import { sdgManagers, superOnly } from '../lib/access'
import { cleanHtml } from '../lib/html'
import { i18nGroup, LOCALES } from '../lib/i18n'
import { track, trackGlobal } from '../lib/track'

// BRM — BMTning 17 ta barqaror rivojlanish maqsadi. Har bir maqsad sahifasi: tavsif, ichki bo'limlar
// (saytdagi tablar), hisobotlar (PDF yoki havola) va THE Impact Rankings natijasi.
// Maqsadga bog'langan yangiliklar Posts'dagi `sdg` maydonidan avtomatik olinadi.
export const SdgGoals: CollectionConfig = {
  slug: 'sdg-goals',
  labels: { singular: 'BRM maqsadi', plural: 'BRM maqsadlari' },
  defaultSort: 'n',
  // 17 maqsad o'zgarmaydi (qo'shilmaydi, o'chirilmaydi); mazmunini superadmin va BRM menejeri tahrirlaydi
  access: { read: () => true, create: superOnly, update: sdgManagers, delete: superOnly },
  fields: [
    { name: 'n', label: 'Raqami', type: 'number', required: true, unique: true, min: 1, max: 17 },
    i18nGroup('title', 'Nomi', { required: true }),
    i18nGroup('subtitle', 'Maqsad tavsifi', { type: 'textarea' }),
    { name: 'url', label: 'Sahifa manzili', type: 'text', required: true },
    { name: 'impactRank', label: 'THE Impact: o‘rni', type: 'text' },
    { name: 'impactScore', label: 'THE Impact: ball', type: 'text' },
    {
      name: 'highlight',
      label: 'Ajratilgan natija',
      type: 'group',
      fields: [
        { name: 'label', label: 'Sarlavha', type: 'text' },
        i18nGroup('value', 'Qiymati'),
      ],
    },
    {
      name: 'sections',
      label: 'Ichki bo‘limlar',
      type: 'array',
      fields: [
        { name: 'key', type: 'text' },
        i18nGroup('title', 'Nomi', { required: true }),
        i18nGroup('body', 'Matni', { type: 'textarea' }),
        { name: 'images', label: 'Rasmlar', type: 'upload', relationTo: 'media', hasMany: true },
      ],
    },
    {
      name: 'reports',
      label: 'Hisobotlar',
      type: 'array',
      fields: [
        { name: 'file', label: 'PDF', type: 'upload', relationTo: 'media' },
        // PDF o'rniga tashqi sahifa
        { name: 'url', label: 'Havola', type: 'text' },
        i18nGroup('title', 'Nomi'),
        { name: 'meta', label: 'Izoh (sana, til)', type: 'text' },
        { name: 'display', type: 'select', defaultValue: 'open', options: ['embed', 'open', 'download'] },
        { name: 'height', type: 'number', defaultValue: 680 },
      ],
    },
  ],
  hooks: {
    beforeChange: [
      ({ data }) => {
        for (const s of data.sections ?? []) {
          for (const lang of LOCALES) {
            if (typeof s.body?.[lang] === 'string') s.body[lang] = cleanHtml(s.body[lang])
          }
        }
        return data
      },
    ],
    ...track('sdg-goals', { label: d => `BRM ${d.n} — ${d.title?.uz ?? ''}`, fields: ['title', 'subtitle', 'impactRank', 'impactScore', 'highlight', 'sections', 'reports'], tags: ['sdg'] }),
  },
}

// BRM bosh sahifasi uchun umumiy sozlamalar
export const SdgPage: GlobalConfig = {
  slug: 'sdg-page',
  label: 'BRM sahifasi',
  access: { read: () => true, update: sdgManagers },
  fields: [
    { name: 'impactYear', label: 'THE Impact Rankings yili', type: 'number', defaultValue: 2025 },
  ],
  hooks: { afterChange: [trackGlobal('sdg-page', 'BRM sahifasi', ['sdg'])] },
}
