// Rol bo'limlari — backend `apps/accounts/roles.py` dagi SECTIONS bilan bir xil
export const SECTIONS: { key: string; label: string; group: string }[] = [
  { key: 'dashboard', label: 'Boşqaruv paneli', group: 'Asosiy' },
  { key: 'news', label: 'Yangiliklar', group: 'Kontent' },
  { key: 'announcements', label: 'E’lonlar', group: 'Kontent' },
  { key: 'events', label: 'Tadbirlar', group: 'Kontent' },
  { key: 'pages', label: 'Sahifalar', group: 'Kontent' },
  { key: 'quick-links', label: 'Tezkor xizmatlar', group: 'Kontent' },
  { key: 'phones', label: 'Telefonlar ma’lumotnomasi', group: 'Kontent' },
  { key: 'admission', label: 'Qabul yillari', group: 'Kontent' },
  { key: 'units', label: 'Bölimlar', group: 'Kontent' },
  { key: 'rude-words', label: 'Haqoratli sözlar', group: 'Kontent' },
  { key: 'media', label: 'Media kutubxona', group: 'Kontent' },
  { key: 'documents', label: 'Hujjatlar', group: 'Kontent' },
  { key: 'videos', label: 'Video darsliklar', group: 'Kontent' },
  { key: 'faculties', label: 'Fakultetlar', group: 'Tuzilma' },
  { key: 'departments', label: 'Kafedralar', group: 'Tuzilma' },
  { key: 'leaders', label: 'Rahbariyat', group: 'Tuzilma' },
  { key: 'staff', label: 'Xodimlar', group: 'Tuzilma' },
  { key: 'sdg', label: 'BRM', group: 'Tuzilma' },
]

export type RoleDoc = {
  id: number
  slug: string
  name: string
  description?: string | null
  system: boolean
  scoped: boolean
  editAll?: boolean
  permissions: Record<string, 'read' | 'write'>
  users: number
}

// Bo'lim → admin sahifasi (backend `roles.SECTION_PATHS` va AppSidebar bilan bir xil) — profildagi ruxsatlar ro'yxati havolalari
export const SECTION_PATHS: Record<string, string> = {
  dashboard: '/', news: '/postlar/news', announcements: '/postlar/announcements', events: '/postlar/events', pages: '/sahifalar',
  'quick-links': '/tezkor-xizmatlar', phones: '/telefonlar', 'rude-words': '/haqoratli-sozlar', admission: '/qabul-yillari', units: '/bolimlar',
  media: '/media', documents: '/hujjatlar', videos: '/video', faculties: '/fakultetlar', departments: '/kafedralar',
  leaders: '/rahbariyat', staff: '/xodimlar', sdg: '/brm',
}
