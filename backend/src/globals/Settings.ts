import type { GlobalConfig } from 'payload'
import { superOnly } from '../lib/access'
import { logActivity, purgeSiteCache } from '../lib/activity'
import { i18nGroup } from '../lib/i18n'

// Sayt sozlamalari (eski admin'dagi "Universitet sozlamalari"). Har bir saqlash versiya bo'lib yoziladi —
// istalgan oldingi holatga, jumladan asl (birinchi) holatga qaytarish mumkin.
export const Settings: GlobalConfig = {
  slug: 'settings',
  label: 'Sayt sozlamalari',
  versions: { max: 200 },
  access: { read: () => true, update: superOnly, readVersions: superOnly },
  fields: [
    {
      name: 'site',
      label: 'Umumiy',
      type: 'group',
      fields: [
        i18nGroup('name', 'Universitet nomi', {
          defaults: { uz: 'Özbekiston davlat jahon tillari universiteti', ru: 'Узбекский государственный университет мировых языков', en: 'Uzbekistan State University of World Languages', zh: '乌兹别克斯坦国立世界语言大学' },
        }),
        i18nGroup('abbr', 'Qisqartma', { defaults: { uz: 'ÖzDJTU', ru: 'УзГУМЯ', en: 'UzSWLU', zh: '世界语言大学' } }),
        i18nGroup('description', 'Sayt tavsifi', { type: 'textarea' }),
      ],
    },
    {
      name: 'contact',
      label: 'Aloqa',
      type: 'group',
      fields: [
        { name: 'phone', label: 'Işonç telefoni', type: 'text', defaultValue: '+998 71 230 13 73' },
        { name: 'email', label: 'E-poçta', type: 'text', defaultValue: 'uzdjtu@uzswlu.uz' },
        i18nGroup('address', 'Manzil', { defaults: { uz: 'Toshkent sh., Kichik halqa yo‘li ko‘chasi, G9-A, 21-uy' } }),
        { name: 'telegram', type: 'text', defaultValue: 'https://t.me/UzSWLU' },
        { name: 'instagram', type: 'text' },
        { name: 'facebook', type: 'text' },
        { name: 'youtube', type: 'text', defaultValue: 'https://www.youtube.com/c/Ozbekistondavlatjahontillariuniversiteti' },
      ],
    },
    {
      name: 'support',
      label: 'Texnik yordam',
      type: 'group',
      fields: [
        { name: 'telegram', label: 'Telegram manzili', type: 'text', defaultValue: 'https://t.me/Uzswlu_rttm' },
        i18nGroup('text', 'Tugma matni', { defaults: { uz: 'Texnik yordam', ru: 'Техподдержка', en: 'Tech support', zh: '技术支持' } }),
        { name: 'showInAdmin', label: 'Admin panelda', type: 'checkbox', defaultValue: true },
        { name: 'showOnSite', label: 'Saytda', type: 'checkbox', defaultValue: false },
        {
          name: 'pages',
          label: 'Qaysi sahifalarda',
          type: 'select',
          hasMany: true,
          defaultValue: ['home', 'contact', 'staff'],
          options: [
            { label: 'Barça sahifalar', value: 'all' },
            { label: 'Boş sahifa', value: 'home' },
            { label: 'Aloqa', value: 'contact' },
            { label: 'Xodim sahifalari', value: 'staff' },
            { label: 'Qabul', value: 'admission' },
          ],
        },
        {
          name: 'place',
          label: 'Sahifaning qayerida',
          type: 'select',
          defaultValue: 'float',
          options: [
            { label: 'Öng pastki burçakda', value: 'float' },
            { label: 'Sahifa oxirida', value: 'end' },
            { label: 'Footer içida', value: 'footer' },
            { label: 'Sarlavha qatorida', value: 'header' },
          ],
        },
      ],
    },
    {
      name: 'numbers',
      label: 'Boş sahifadagi raqamlar',
      type: 'group',
      fields: [
        { name: 'auto', label: 'HEMIS’dan avtomatik', type: 'checkbox', defaultValue: true },
        { name: 'students', type: 'number' },
        { name: 'staff', type: 'number' },
        { name: 'faculties', type: 'number' },
        { name: 'departments', type: 'number' },
      ],
    },
  ],
  hooks: {
    afterChange: [
      async ({ req, doc }) => {
        if (!req.context?.seed) await logActivity(req, { action: 'settings', entity: 'settings', label: 'Sayt sozlamalari saqlandi' })
        await purgeSiteCache(['settings', 'home'])
        return doc
      },
    ],
  },
}
