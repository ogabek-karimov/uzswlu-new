import type { CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup } from '../lib/i18n'
import { track } from '../lib/track'

// Rektorat sahifasi: rektor, prorektorlar va matbuot kotibi (rektor maslahatchisi)
export const Leaders: CollectionConfig = {
  slug: 'leaders',
  labels: { singular: 'Rahbar', plural: 'Rahbariyat' },
  defaultSort: 'order',
  access: { read: () => true, create: superOnly, update: superOnly, delete: superOnly },
  fields: [
    {
      name: 'kind',
      label: 'Turi',
      type: 'select',
      required: true,
      defaultValue: 'prorector',
      options: [
        { label: 'Rektor', value: 'rector' },
        { label: 'Prorektor', value: 'prorector' },
        { label: 'Matbuot kotibi / maslahatçi', value: 'press' },
      ],
    },
    { name: 'name', label: 'F.I.Ş.', type: 'text', required: true },
    // Staff sahifasidagi ID (/teacher/:id) — HEMIS'dagi xodim bilan bog'lanish
    { name: 'staffId', label: 'Xodim ID (HEMIS)', type: 'text' },
    { name: 'photo', label: 'Rasm', type: 'upload', relationTo: 'media' },
    i18nGroup('role', 'Lavozim', { type: 'textarea', required: true }),
    i18nGroup('hours', 'Qabul kuni va vaqti'),
    { name: 'phone', label: 'Telefon', type: 'text' },
    { name: 'ext', label: 'Ichki raqam', type: 'text' },
    { name: 'email', label: 'E-pochta', type: 'email' },
    { name: 'reception', label: '“Virtual qabulxona” formasida ko‘rsatish', type: 'checkbox', defaultValue: true },
    { name: 'order', type: 'number', defaultValue: 0, index: true },
  ],
  hooks: track('leaders', { label: d => d.name, fields: ['kind', 'name', 'staffId', 'photo', 'role', 'hours', 'phone', 'ext', 'email', 'reception', 'order'], tags: ['leadership', 'contact'] }),
}
