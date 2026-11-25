import type { ICONS } from '@/components/Icon.vue'

export type NavItem = { to: string; label: string; icon: keyof typeof ICONS; section?: string; superOnly?: boolean; soon?: boolean }

// Muharrir (kichik admin) faqat o'ziga ruxsat berilgan bo'limlarni ko'radi
export const groups: { label: string; items: NavItem[] }[] = [
  { label: 'Asosiy', items: [
    { to: '/', label: 'Boşqaruv paneli', icon: 'dashboard', section: 'dashboard' },
    { to: '/statistika', label: 'Statistika', icon: 'stats', superOnly: true },
    { to: '/arizalar', label: 'Arizalar', icon: 'docs', superOnly: true },
  ] },
  { label: 'Kontent', items: [
    { to: '/postlar/news', label: 'Yangiliklar', icon: 'news', section: 'news' },
    { to: '/postlar/announcements', label: 'E’lonlar', icon: 'announcements', section: 'announcements' },
    { to: '/postlar/events', label: 'Tadbirlar', icon: 'events', section: 'events' },
    { to: '/sahifalar', label: 'Sahifalar', icon: 'pages', section: 'pages' },
    { to: '/tezkor-xizmatlar', label: 'Tezkor xizmatlar', icon: 'quick', section: 'quick-links' },
    { to: '/telefonlar', label: 'Telefonlar', icon: 'phone', section: 'phones' },
    { to: '/qabul-yillari', label: 'Qabul yillari', icon: 'calendar', section: 'admission' },
    { to: '/bolimlar', label: 'Bölimlar', icon: 'staff', section: 'units' },
    { to: '/haqoratli-sozlar', label: 'Haqoratli sözlar', icon: 'shield', section: 'rude-words' },
    { to: '/karusel', label: 'Boş sahifa karuseli', icon: 'carousel', superOnly: true },
    { to: '/media', label: 'Media kutubxona', icon: 'media', section: 'media' },
    { to: '/hujjatlar', label: 'Hujjatlar', icon: 'docs', section: 'documents' },
    { to: '/video', label: 'Video darsliklar', icon: 'video', section: 'videos' },
    { to: '/onlayn-kameralar', label: 'Onlayn kameralar', icon: 'cctv', section: 'pages' },
  ] },
  { label: 'Tuzilma', items: [
    { to: '/fakultetlar', label: 'Fakultetlar', icon: 'faculties', section: 'faculties' },
    { to: '/kafedralar', label: 'Kafedralar', icon: 'departments', section: 'departments' },
    { to: '/rahbariyat', label: 'Rahbariyat', icon: 'leaders', section: 'leaders' },
    { to: '/xodimlar', label: 'Xodimlar', icon: 'staff', section: 'staff' },
    { to: '/brm', label: 'BRM', icon: 'sdg', section: 'sdg' },
    { to: '/ramzlar', label: 'Ramzlar', icon: 'symbols', superOnly: true },
  ] },
  { label: 'Tizim', items: [
    { to: '/rollar', label: 'Rollar va ruxsatlar', icon: 'users', superOnly: true },
    { to: '/ruxsatlar', label: 'Ruxsatlar kutubxonasi', icon: 'shield', superOnly: true },
    { to: '/foydalanuvchilar', label: 'Foydalanuvçilar va rollar', icon: 'users', superOnly: true },
    { to: '/kirish-tarixi', label: 'Kiriş tarixi', icon: 'logins', superOnly: true },
    { to: '/faollik', label: 'Faollik jurnali', icon: 'activity', superOnly: true },
    { to: '/sozlamalar', label: 'Sayt sozlamalari', icon: 'settings', superOnly: true },
  ] },
]
