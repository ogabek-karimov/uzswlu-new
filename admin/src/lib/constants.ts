export const LANGS = [
  { code: 'uz', short: 'UZ', label: 'Özbekça' },
  { code: 'ru', short: 'RU', label: 'Rusça' },
  { code: 'en', short: 'EN', label: 'Inglizça' },
  { code: 'zh', short: 'ZH', label: 'Xitoyça' },
] as const
export type Lang = (typeof LANGS)[number]['code']

export const POST_TYPES = [
  { value: 'news', label: 'Yangilik', plural: 'Yangiliklar', newLabel: 'Yangi yangilik', path: 'news' },
  { value: 'announcements', label: 'E’lon', plural: 'E’lonlar', newLabel: 'Yangi e’lon', path: 'announcements' },
  { value: 'events', label: 'Tadbir', plural: 'Tadbirlar', newLabel: 'Yangi tadbir', path: 'events' },
] as const
export type PostType = (typeof POST_TYPES)[number]['value']

// BMT rasmiy ranglari va nomlari (saytdagi bilan bir xil)
export const SDG_COLORS = ['#E5243B', '#DDA63A', '#4C9F38', '#C5192D', '#FF3A21', '#26BDE2', '#FCC30B', '#A21942', '#FD6925', '#DD1367', '#FD9D24', '#BF8B2E', '#3F7E44', '#0A97D9', '#56C02B', '#00689D', '#19486A']
export const SDG_NAMES = ['Qaşşoqlikka barham beriş', 'Oçlikka barham beriş', 'Soğliq va farovonlik', 'Sifatli ta’lim', 'Gender tengligi', 'Toza suv va sanitariya', 'Arzon va toza energiya', 'Munosib mehnat va iqtisodiy ösiş', 'Sanoat, innovatsiya va infratuzilma', 'Tengsizlikni kamaytiriş', 'Barqaror şaharlar', 'Mas’uliyatli iste’mol', 'Iqlim özgarişiga qarşi kuraş', 'Dengiz ekotizimlari', 'Quruqlik ekotizimlari', 'Tinçlik, adolat va boşqaruv', 'Maqsadlar yölida hamkorlik']

export const PDF_MODES = [
  { value: 'embed', label: 'Içi körinadi', note: 'Sahifada ramka içida oçiladi — aylantirib öqiladi.' },
  { value: 'open', label: 'Bosib oçiladi', note: 'Karta; bosilganda yangi oynada oçiladi.' },
  { value: 'download', label: 'Yuklab oliş', note: 'Karta; bosilganda fayl yuklab olinadi.' },
  { value: 'link', label: 'Matn-havola', note: 'Matn ostida faqat nomi (masalan, AVTOREFERAT); bosilganda PDF oçiladi.' },
] as const

/** Saytning manzili (postni saytda ko'rish uchun) */
export const SITE_URL = import.meta.env.VITE_SITE_URL ?? 'http://localhost:3000'
/** Fayllarning ochiq manzili (backend) — "Havolani nusxalash" uchun */
export const MEDIA_BASE = import.meta.env.VITE_MEDIA_BASE ?? 'http://localhost:3001'
export const VERSION = '1.0.0'
