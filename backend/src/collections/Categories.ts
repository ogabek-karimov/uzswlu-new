import type { CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup } from '../lib/i18n'

// Post kategoriyalari ("Xalqaro hamkorlik", "Talabalar hayoti"...) — 4 tilda
export const Categories: CollectionConfig = {
  slug: 'categories',
  labels: { singular: 'Kategoriya', plural: 'Kategoriyalar' },
  admin: { useAsTitle: 'key' },
  access: { read: () => true, create: superOnly, update: superOnly, delete: superOnly },
  fields: [
    { name: 'key', label: 'Kalit', type: 'text', required: true, unique: true },
    i18nGroup('name', 'Nomi', { required: true }),
  ],
}
