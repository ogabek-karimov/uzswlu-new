import type { CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup, LOCALES, LOCALE_LABELS } from '../lib/i18n'
import { track } from '../lib/track'

const pagesAccess = ({ req }: { req: { user?: unknown } }) => ['superadmin', 'pages'].includes((req.user as { role?: string } | null)?.role ?? '')

// Hujjat toifalari (Universitet hujjatlari, Qonunchilik …)
export const DocCategories: CollectionConfig = {
  slug: 'doc-categories',
  labels: { singular: 'Hujjat toifasi', plural: 'Hujjat toifalari' },
  defaultSort: 'order',
  access: { read: () => true, create: pagesAccess, update: pagesAccess, delete: superOnly },
  fields: [
    i18nGroup('title', 'Nomi', { required: true }),
    { name: 'order', type: 'number', defaultValue: 0 },
  ],
  hooks: track('doc-categories', { label: d => d.title?.uz, fields: ['title', 'order'], tags: ['documents'] }),
}

// Me'yoriy hujjatlar: har bir tilda alohida PDF (o'zbekchasi majburiy) yoki tashqi havola (lex.uz)
export const Documents: CollectionConfig = {
  slug: 'documents',
  labels: { singular: 'Hujjat', plural: 'Hujjatlar' },
  defaultSort: 'order',
  access: { read: () => true, create: pagesAccess, update: pagesAccess, delete: pagesAccess },
  fields: [
    i18nGroup('title', 'Nomi', { required: true }),
    { name: 'category', label: 'Toifa', type: 'relationship', relationTo: 'doc-categories', required: true, index: true },
    { name: 'number', label: 'Hujjat raqami va sanasi', type: 'text' },
    {
      name: 'files',
      label: 'PDF fayllar',
      type: 'group',
      fields: LOCALES.map(lang => ({ name: lang, label: LOCALE_LABELS[lang], type: 'upload' as const, relationTo: 'media' as const })),
    },
    // PDF o'rniga tashqi sahifa (masalan, lex.uz)
    { name: 'url', label: 'Tashqi havola', type: 'text' },
    {
      name: 'display',
      label: 'Saytda ko‘rinishi',
      type: 'select',
      defaultValue: 'open',
      options: [
        { label: 'Ichi ko‘rinadi', value: 'embed' },
        { label: 'Bosib ochiladi', value: 'open' },
        { label: 'Yuklab olish', value: 'download' },
      ],
    },
    { name: 'height', label: 'Ramka balandligi', type: 'number', defaultValue: 680 },
    // Qaysi sahifalarda chiqadi (sahifa manzillari)
    { name: 'pages', label: 'Sahifalar', type: 'text', hasMany: true, defaultValue: ['meyoriy-hujjatlar'] },
    { name: 'downloads', label: 'Yuklab olindi', type: 'number', defaultValue: 0, admin: { readOnly: true } },
    { name: 'order', type: 'number', defaultValue: 0, index: true },
  ],
  hooks: track('documents', { label: d => d.title?.uz, fields: ['title', 'category', 'number', 'files', 'url', 'display', 'height', 'pages', 'order'], tags: ['documents'] }),
}
