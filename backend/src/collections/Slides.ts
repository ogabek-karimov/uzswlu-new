import type { CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup } from '../lib/i18n'
import { track } from '../lib/track'

// Bosh sahifa karuseli — xodim sahifalari pastida ham shu slaydlar chiqadi (bitta manba)
export const Slides: CollectionConfig = {
  slug: 'slides',
  labels: { singular: 'Slayd', plural: 'Karusel' },
  defaultSort: 'order',
  access: { read: () => true, create: superOnly, update: superOnly, delete: superOnly },
  fields: [
    { name: 'name', label: 'Nomi (faqat admin uchun)', type: 'text', required: true },
    { name: 'image', label: 'Rasm (16:9)', type: 'upload', relationTo: 'media', required: true },
    i18nGroup('alt', 'Rasm tavsifi'),
    { name: 'link', label: 'Bosilganda ochiladi', type: 'text' },
    { name: 'startsAt', label: 'Ko‘rsatish boshlanadi', type: 'date' },
    { name: 'endsAt', label: 'Tugaydi', type: 'date' },
    { name: 'order', type: 'number', defaultValue: 0, index: true },
  ],
  hooks: track('slides', { label: d => d.name, fields: ['name', 'image', 'alt', 'link', 'startsAt', 'endsAt', 'order'], tags: ['home'] }),
}
