import type { CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'

// Faollik jurnali: kim, qachon, nimani o'zgartirdi. Qaytarish Payload versiyalari orqali.
export const Activity: CollectionConfig = {
  slug: 'activity',
  labels: { singular: 'Amal', plural: 'Faollik jurnali' },
  admin: { useAsTitle: 'label', defaultColumns: ['createdAt', 'userName', 'action', 'label'] },
  access: {
    read: superOnly,
    create: () => false,
    update: () => false,
    delete: superOnly,
  },
  fields: [
    { name: 'user', type: 'relationship', relationTo: 'users', index: true },
    { name: 'userName', type: 'text' },
    {
      name: 'action',
      type: 'select',
      index: true,
      options: ['create', 'edit', 'publish', 'hide', 'show', 'delete', 'restore', 'role', 'settings'].map(v => ({ label: v, value: v })),
    },
    { name: 'entity', type: 'text', index: true },
    { name: 'entityId', type: 'text' },
    { name: 'label', type: 'text' },
    { name: 'changes', type: 'json' },
    { name: 'ip', type: 'text' },
  ],
}
