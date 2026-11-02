import type { Access, CollectionConfig } from 'payload'
import { superOnly } from '../lib/access'
import { i18nGroup } from '../lib/i18n'
import { track } from '../lib/track'

// Tuzilma: fakultetlar, kafedralar va xodim profillari.
// HEMIS'dan keladigan ma'lumot (dekan, xodimlar soni, F.I.Sh., lavozim) bu yerda saqlanmaydi —
// faqat admin to'ldiradigan qism: matn, logo, aloqa, tarjimalar, bio, ilmiy profillar.

const facultyAccess: Access = ({ req }) => ['superadmin', 'faculty'].includes((req.user as { role?: string } | null)?.role ?? '')

export const Faculties: CollectionConfig = {
  slug: 'faculties',
  labels: { singular: 'Fakultet', plural: 'Fakultetlar' },
  defaultSort: 'order',
  access: { read: () => true, create: superOnly, update: facultyAccess, delete: superOnly },
  fields: [
    // Sayt manzili (/faculty/:slug) va HEMIS'dagi fakultet bilan bog'lanish
    { name: 'slug', label: 'Manzil', type: 'text', required: true, unique: true, index: true },
    i18nGroup('name', 'Nomi', { required: true }),
    { name: 'logo', label: 'Logo', type: 'upload', relationTo: 'media' },
    { name: 'cover', label: 'Muqova', type: 'upload', relationTo: 'media' },
    i18nGroup('about', 'Fakultet haqida', { type: 'textarea' }),
    { name: 'phone', label: 'Telefon', type: 'text' },
    { name: 'email', label: 'E-pochta', type: 'text' },
    i18nGroup('address', 'Manzil / xona'),
    { name: 'mapUrl', label: 'Xarita havolasi', type: 'text' },
    { name: 'order', type: 'number', defaultValue: 0, index: true },
  ],
  hooks: track('faculties', { label: d => d.name?.uz, fields: ['slug', 'name', 'logo', 'cover', 'about', 'phone', 'email', 'address', 'mapUrl', 'order'], tags: ['faculties', 'home'] }),
}

export const Departments: CollectionConfig = {
  slug: 'departments',
  labels: { singular: 'Kafedra', plural: 'Kafedralar' },
  access: { read: () => true, create: facultyAccess, update: facultyAccess, delete: superOnly },
  fields: [
    { name: 'hemisId', label: 'HEMIS ID', type: 'text', required: true, unique: true, index: true },
    { name: 'faculty', label: 'Fakultet (manzil)', type: 'text', index: true },
    // O'zbekchasi HEMIS'dan; ru/en/zh tarjimalari shu yerda
    i18nGroup('name', 'Nomi'),
    { name: 'image', label: 'Kafedra rasmi', type: 'upload', relationTo: 'media' },
    i18nGroup('about', 'Kafedra haqida', { type: 'textarea' }),
    { name: 'room', label: 'Xona', type: 'text' },
    { name: 'ext', label: 'Ichki telefon', type: 'text' },
    { name: 'showStaff', label: 'Xodimlar ro‘yxatini sahifada ko‘rsatish', type: 'checkbox', defaultValue: true },
  ],
  hooks: track('departments', { label: d => d.name?.uz ?? d.hemisId, fields: ['name', 'image', 'about', 'room', 'ext', 'showStaff'], tags: ['faculties'] }),
}

export const StaffProfiles: CollectionConfig = {
  slug: 'staff-profiles',
  labels: { singular: 'Xodim profili', plural: 'Xodim profillari' },
  access: { read: () => true, create: superOnly, update: superOnly, delete: superOnly },
  fields: [
    { name: 'hemisId', label: 'HEMIS ID', type: 'text', required: true, unique: true, index: true },
    { name: 'name', label: 'F.I.Sh. (HEMIS’dan, qidiruv uchun)', type: 'text' },
    i18nGroup('bio', 'Bio', { type: 'textarea' }),
    { name: 'orcid', label: 'ORCID', type: 'text' },
    { name: 'scholar', label: 'Google Scholar', type: 'text' },
    { name: 'scopus', label: 'Scopus ID', type: 'text' },
    { name: 'researchgate', label: 'ResearchGate', type: 'text' },
    { name: 'hidden', label: 'Saytda yashirilgan', type: 'checkbox', defaultValue: false, index: true },
  ],
  hooks: track('staff-profiles', { label: d => d.name ?? d.hemisId, fields: ['bio', 'orcid', 'scholar', 'scopus', 'researchgate', 'hidden'], tags: ['staff'] }),
}
