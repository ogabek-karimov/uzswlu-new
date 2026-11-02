import path from 'path'
import { APIError, type CollectionConfig } from 'payload'
import { editorsOnly, superOnly } from '../lib/access'
import { logActivity } from '../lib/activity'
import { i18nGroup } from '../lib/i18n'
import { mediaUsage } from '../lib/usage'

// Rasm, PDF va audio. Rasmlar yuklanganda WebP'ga o'giriladi va kichik o'lchamlari yaratiladi.
export const Media: CollectionConfig = {
  slug: 'media',
  labels: { singular: 'Fayl', plural: 'Media' },
  access: {
    read: () => true,
    create: editorsOnly,
    update: editorsOnly,
    delete: superOnly,
  },
  upload: {
    staticDir: path.resolve(process.cwd(), 'media'),
    mimeTypes: ['image/*', 'application/pdf', 'audio/mpeg'],
    formatOptions: { format: 'webp', options: { quality: 82 } },
    resizeOptions: { width: 2560, withoutEnlargement: true },
    imageSizes: [
      { name: 'thumb', width: 400 },
      { name: 'card', width: 900 },
      { name: 'hero', width: 1920 },
    ],
    focalPoint: true,
  },
  fields: [
    i18nGroup('alt', 'Tavsif (közi ojizlar uçun)'),
    {
      name: 'folder',
      label: 'Papka',
      type: 'select',
      defaultValue: 'posts',
      options: [
        { label: 'Yangiliklar', value: 'posts' },
        { label: 'Karusel', value: 'carousel' },
        { label: 'Hujjatlar', value: 'docs' },
        { label: 'Xodimlar', value: 'staff' },
        { label: 'Logotiplar', value: 'logos' },
        { label: 'Audio', value: 'audio' },
      ],
    },
    // Yuklangan asl fayl hajmi (WebP'ga o'girilgandan keyin qancha joy tejalganini ko'rsatish uchun)
    { name: 'originalSize', type: 'number', admin: { readOnly: true } },
    { name: 'uploadedBy', type: 'relationship', relationTo: 'users', admin: { readOnly: true } },
  ],
  hooks: {
    beforeChange: [
      ({ data, req, operation }) => {
        const file = req.file as { size?: number } | undefined
        if (file?.size) data.originalSize = file.size
        if (operation === 'create' && req.user && !data.uploadedBy) data.uploadedBy = req.user.id
        return data
      },
    ],
    // Saytda ishlatilayotgan faylni o'chirib bo'lmaydi — avval o'sha joydan olib tashlanadi
    beforeDelete: [
      async ({ req, id }) => {
        const used = await mediaUsage(req.payload, id, req)
        if (used.length) throw new APIError(`Fayl işlatilmoqda: ${used.slice(0, 3).join('; ')}`, 409)
      },
    ],
    afterDelete: [
      async ({ req, doc }) => {
        await logActivity(req, { action: 'delete', entity: 'media', entityId: doc.id, label: doc.filename })
      },
    ],
  },
}
