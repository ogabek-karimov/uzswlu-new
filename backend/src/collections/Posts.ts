import type { CollectionConfig, Where } from 'payload'
import { editorsOnly, isSuper, loggedIn } from '../lib/access'
import { logActivity, purgeSiteCache } from '../lib/activity'
import { cleanHtml, slugify } from '../lib/html'
import { i18nGroup, LOCALES } from '../lib/i18n'

// Yangiliklar, e'lonlar va tadbirlar — bitta to'plam (eski admin'dagi "Sahifa" tanlovi = type).
// Saytda ko'rinishi: status=published, hidden emas va publishedAt <= hozir (kelajak vaqt = rejalashtirilgan).
export const Posts: CollectionConfig = {
  slug: 'posts',
  labels: { singular: 'Post', plural: 'Postlar' },
  admin: { useAsTitle: 'label', defaultColumns: ['label', 'type', 'status', 'publishedAt'] },
  versions: { maxPerDoc: 30 },
  trash: true,
  access: {
    read: loggedIn,
    create: editorsOnly,
    update: editorsOnly,
    delete: editorsOnly,
  },
  fields: [
    {
      name: 'type',
      label: 'Turi',
      type: 'select',
      required: true,
      defaultValue: 'news',
      index: true,
      options: [
        { label: 'Yangilik', value: 'news' },
        { label: 'E’lon', value: 'announcements' },
        { label: 'Tadbir', value: 'events' },
      ],
    },
    i18nGroup('title', 'Sarlavha', { required: true }),
    i18nGroup('excerpt', 'Qisqa tavsif', { type: 'textarea' }),
    i18nGroup('body', 'Matn (HTML)', { type: 'textarea' }),
    { name: 'label', type: 'text', admin: { hidden: true } },
    { name: 'slug', label: 'Manzil', type: 'text', index: true },
    { name: 'category', label: 'Kategoriya', type: 'relationship', relationTo: 'categories' },
    {
      name: 'sdg',
      label: 'BRM (0 — kirmaydi)',
      type: 'number',
      defaultValue: 0,
      min: 0,
      max: 17,
      index: true,
    },
    { name: 'cover', label: 'Asosiy rasm', type: 'upload', relationTo: 'media' },
    {
      name: 'coverByLang',
      label: 'Har til uçun alohida rasm',
      type: 'group',
      fields: (['ru', 'en', 'zh'] as const).map(lang => ({ name: lang, type: 'upload' as const, relationTo: 'media' as const })),
    },
    { name: 'gallery', label: 'Galereya', type: 'upload', relationTo: 'media', hasMany: true },
    {
      name: 'attachments',
      label: 'Fayllar (PDF)',
      type: 'array',
      fields: [
        { name: 'file', type: 'upload', relationTo: 'media', required: true },
        i18nGroup('title', 'Nomi'),
        {
          name: 'display',
          label: 'Saytda körinişi',
          type: 'select',
          defaultValue: 'open',
          options: [
            { label: 'Içi körinadi', value: 'embed' },
            { label: 'Bosib oçiladi', value: 'open' },
            { label: 'Yuklab oliş', value: 'download' },
            // Matn ostida faqat nomi (masalan, "AVTOREFERAT") — bosilganda PDF ochiladi
            { label: 'Matn-havola', value: 'link' },
          ],
        },
        { name: 'height', type: 'number', defaultValue: 680 },
      ],
    },
    i18nGroup('tags', 'Teglar', { hasMany: true }),
    { name: 'author', label: 'Muallif', type: 'relationship', relationTo: 'users', access: { update: ({ req }) => isSuper(req.user as { role?: string }) } },
    {
      name: 'publishedAt',
      label: 'Naşr vaqti',
      type: 'date',
      index: true,
      admin: { date: { pickerAppearance: 'dayAndTime', timeFormat: 'HH:mm' } },
    },
    {
      name: 'status',
      label: 'Holati',
      type: 'select',
      defaultValue: 'draft',
      index: true,
      options: [
        { label: 'Qoralama', value: 'draft' },
        { label: 'Naşr qilingan', value: 'published' },
      ],
    },
    { name: 'hidden', label: 'Saytdan vaqtinça yaşirilgan', type: 'checkbox', defaultValue: false, index: true },
    // Tadbirlar uchun
    { name: 'startsAt', label: 'Boşlaniş', type: 'date', admin: { condition: (_, s) => s?.type === 'events' } },
    { name: 'endsAt', label: 'Tugaş', type: 'date', admin: { condition: (_, s) => s?.type === 'events' } },
    i18nGroup('location', 'Ötkaziladigan joy'),
    { name: 'views', type: 'number', defaultValue: 0, admin: { readOnly: true } },
  ],
  hooks: {
    beforeChange: [
      async ({ data, req, operation, originalDoc }) => {
        const title = data.title ?? originalDoc?.title
        data.label = title?.uz ?? ''
        // HTML matnni tozalash (XSS'dan himoya)
        if (data.body) {
          for (const lang of LOCALES) {
            if (typeof data.body[lang] === 'string') data.body[lang] = cleanHtml(data.body[lang])
          }
        }
        if (operation === 'create' && req.user && !data.author) data.author = req.user.id
        if (data.status === 'published' && !data.publishedAt && !originalDoc?.publishedAt) data.publishedAt = new Date().toISOString()
        // Manzil: o'zbekcha sarlavhadan, tur ichida takrorlanmas
        if (!data.slug && title?.uz) {
          const base = slugify(title.uz)
          const type = data.type ?? originalDoc?.type ?? 'news'
          let slug = base
          for (let i = 2; i < 50; i++) {
            const where: Where = { and: [{ slug: { equals: slug } }, { type: { equals: type } }] }
            if (originalDoc?.id) where.and!.push({ id: { not_equals: originalDoc.id } })
            const { totalDocs } = await req.payload.count({ collection: 'posts', where, overrideAccess: true, req })
            if (!totalDocs) break
            slug = `${base}-${i}`
          }
          data.slug = slug
        }
        return data
      },
    ],
    afterChange: [
      async ({ req, doc, previousDoc, operation }) => {
        if (req.context?.seed) return doc
        const label = doc.title?.uz ?? doc.label
        if (operation === 'create') {
          await logActivity(req, { action: doc.status === 'published' ? 'publish' : 'create', entity: 'posts', entityId: doc.id, label })
        }
        else if (previousDoc) {
          const changes: Record<string, { before: unknown; after: unknown }> = {}
          for (const key of ['status', 'hidden', 'publishedAt', 'sdg', 'type'] as const) {
            if (previousDoc[key] !== doc[key]) changes[key] = { before: previousDoc[key], after: doc[key] }
          }
          for (const lang of LOCALES) {
            if ((previousDoc.title?.[lang] ?? '') !== (doc.title?.[lang] ?? '')) changes[`title.${lang}`] = { before: previousDoc.title?.[lang] ?? '', after: doc.title?.[lang] ?? '' }
            if ((previousDoc.body?.[lang] ?? '') !== (doc.body?.[lang] ?? '')) changes[`body.${lang}`] = { before: '…', after: '…' }
          }
          const action = changes.hidden ? (doc.hidden ? 'hide' : 'show')
            : changes.status && doc.status === 'published' ? 'publish'
              : 'edit'
          if (Object.keys(changes).length) await logActivity(req, { action, entity: 'posts', entityId: doc.id, label, changes })
        }
        await purgeSiteCache(['posts', 'home'])
        return doc
      },
    ],
    afterDelete: [
      async ({ req, doc }) => {
        await logActivity(req, { action: 'delete', entity: 'posts', entityId: doc.id, label: doc.title?.uz ?? doc.label })
        await purgeSiteCache(['posts', 'home'])
      },
    ],
  },
}
