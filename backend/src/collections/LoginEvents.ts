import type { CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'

// Kirish tarixi: har bir urinish (muvaffaqiyatli yoki xato) — IP, qurilma, brauzer bilan. Faqat superadmin ko'radi.
export const LoginEvents: CollectionConfig = {
  slug: 'login-events',
  labels: { singular: 'Kiriş', plural: 'Kiriş tarixi' },
  admin: { useAsTitle: 'username', defaultColumns: ['createdAt', 'username', 'result', 'ip'] },
  access: {
    read: superOnly,
    create: () => false,
    update: () => false,
    delete: superOnly,
  },
  fields: [
    { name: 'user', type: 'relationship', relationTo: 'users', index: true },
    { name: 'username', type: 'text', index: true },
    {
      name: 'method',
      type: 'select',
      defaultValue: 'password',
      options: [{ label: 'Login va parol', value: 'password' }, { label: 'HEMIS', value: 'hemis' }],
    },
    {
      name: 'result',
      type: 'select',
      index: true,
      options: [
        { label: 'Muvaffaqiyatli', value: 'success' },
        { label: 'Notöğri parol', value: 'bad_password' },
        { label: 'Bloklangan', value: 'locked' },
        { label: 'Ruxsat yöq', value: 'denied' },
      ],
    },
    { name: 'ip', type: 'text', index: true },
    { name: 'network', type: 'text' },
    { name: 'browser', type: 'text' },
    { name: 'os', type: 'text' },
    { name: 'device', type: 'text' },
    { name: 'userAgent', type: 'text' },
  ],
}
