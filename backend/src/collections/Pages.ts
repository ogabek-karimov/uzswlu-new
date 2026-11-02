import { APIError, type Access, type CollectionConfig } from 'payload'
import { cleanHtml, slugify } from '../lib/html'
import { i18nGroup, LOCALES } from '../lib/i18n'
import { track } from '../lib/track'

// Saytdagi sahifalar daraxti. Yuqori daraja — menyu bo'limlari (Universitet, Abituriyentlar …),
// ichidagilari — sahifalar. Sayt menyusi shu daraxtdan o'z-o'zidan quriladi.
//   group   — menyu bo'limi (mega-menyu ustuni)
//   text    — matnli sahifa (kirish, matn, raqamlar, vaqt chizig'i, PDF'lar)
//   special — saytning maxsus sahifasi (Rektorat, BRM maqsadi, Hujjatlar …) — mazmuni o'z bo'limida
//   link    — tashqi havola yoki PDF fayl
const pagesAccess: Access = ({ req }) => ['superadmin', 'pages'].includes((req.user as { role?: string } | null)?.role ?? '')

export const Pages: CollectionConfig = {
  slug: 'pages',
  labels: { singular: 'Sahifa', plural: 'Sahifalar' },
  defaultSort: 'order',
  access: { read: () => true, create: pagesAccess, update: pagesAccess, delete: pagesAccess },
  versions: { maxPerDoc: 20 },
  fields: [
    i18nGroup('title', 'Nomi', { required: true }),
    { name: 'template', label: 'Shablon', type: 'select', required: true, defaultValue: 'text', options: ['group', 'text', 'special', 'link'] },
    { name: 'parent', label: 'Ota sahifa', type: 'relationship', relationTo: 'pages', index: true },
    // Manzil: /slug (matnli sahifa); maxsus sahifa va havola uchun to'liq yo'l `url`da
    { name: 'slug', label: 'Manzil', type: 'text', index: true },
    { name: 'url', label: 'Havola / yo‘l', type: 'text' },
    { name: 'file', label: 'PDF fayl', type: 'upload', relationTo: 'media' },
    { name: 'groupKey', label: 'Bo‘lim kaliti (belgi uchun)', type: 'text' },
    i18nGroup('description', 'Bo‘lim tavsifi', { type: 'textarea' }),
    { name: 'overview', label: 'Bo‘limning umumiy sahifasi', type: 'text' },
    { name: 'sdg', label: 'BRM maqsadi', type: 'number', min: 0, max: 17 },
    { name: 'inMenu', label: 'Menyuda ko‘rsatish', type: 'checkbox', defaultValue: true },
    { name: 'published', label: 'Nashr qilingan', type: 'checkbox', defaultValue: true, index: true },
    { name: 'highlight', label: 'Ajratib ko‘rsatish', type: 'checkbox', defaultValue: false },
    // Matnli sahifa mazmuni
    i18nGroup('lead', 'Kirish matni', { type: 'textarea' }),
    i18nGroup('body', 'Matn', { type: 'textarea' }),
    { name: 'facts', label: 'Raqamlar', type: 'array', fields: [{ name: 'value', type: 'text', required: true }, i18nGroup('label', 'Izoh')] },
    { name: 'timeline', label: 'Vaqt chizig‘i', type: 'array', fields: [i18nGroup('label', 'Yil / sarlavha'), i18nGroup('text', 'Matn'), { name: 'highlight', type: 'checkbox' }] },
    {
      name: 'attachments',
      label: 'PDF hujjatlar',
      type: 'array',
      fields: [
        { name: 'file', type: 'upload', relationTo: 'media' },
        { name: 'url', type: 'text' },
        i18nGroup('title', 'Nomi'),
        i18nGroup('meta', 'Izoh'),
        { name: 'display', type: 'select', defaultValue: 'open', options: ['embed', 'open', 'download', 'link'] },
        { name: 'height', type: 'number', defaultValue: 680 },
      ],
    },
    { name: 'order', type: 'number', defaultValue: 0, index: true },
  ],
  hooks: {
    beforeChange: [
      async ({ data, req, originalDoc }) => {
        if (data.body) {
          for (const lang of LOCALES) {
            // "<!-- timeline -->" belgisi (vaqt chizig'i joyi) tozalashda yo'qolmasin: [[timeline]] ko'rinishida saqlanadi
            if (typeof data.body[lang] === 'string') data.body[lang] = cleanHtml(data.body[lang].replace(/<!--\s*timeline\s*-->/g, '<p>[[timeline]]</p>'))
          }
        }
        const template = data.template ?? originalDoc?.template
        // Matnli sahifa manzili o'zbekcha nomidan; butun sayt bo'yicha takrorlanmas
        if (template === 'text' || template === 'group') {
          if (!data.slug && template === 'text') data.slug = slugify(data.title?.uz ?? originalDoc?.title?.uz ?? '')
          if (data.slug) {
            data.slug = slugify(data.slug)
            const clash = await req.payload.find({
              collection: 'pages', where: { and: [{ slug: { equals: data.slug } }, ...(originalDoc?.id ? [{ id: { not_equals: originalDoc.id } }] : [])] },
              limit: 1, depth: 0, overrideAccess: true, req,
            })
            if (clash.docs.length) throw new APIError(`“/${data.slug}” manzili band — boşqa manzil tanlang`, 400)
          }
        }
        if (data.parent && originalDoc?.id && Number(data.parent) === Number(originalDoc.id)) throw new APIError('Sahifa özining içiga qöyilmaydi', 400)
        return data
      },
    ],
    beforeDelete: [
      async ({ req, id }) => {
        const kids = await req.payload.count({ collection: 'pages', where: { parent: { equals: id } }, overrideAccess: true, req })
        if (kids.totalDocs) throw new APIError('Avval içidagi sahifalarni köçiring yoki öçiring', 409)
      },
    ],
    ...track('pages', { label: d => d.title?.uz, fields: ['title', 'template', 'parent', 'slug', 'url', 'inMenu', 'published', 'highlight', 'lead', 'body', 'facts', 'timeline', 'attachments', 'order'], tags: ['menu', 'pages'] }),
  },
}
