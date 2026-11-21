// Rol bo'limlari — backend `apps/accounts/roles.py` dagi SECTIONS bilan bir xil
export const SECTIONS: { key: string; label: string; group: string }[] = [
  { key: 'dashboard', label: 'Boşqaruv paneli', group: 'Asosiy' },
  { key: 'news', label: 'Yangiliklar', group: 'Kontent' },
  { key: 'announcements', label: 'E’lonlar', group: 'Kontent' },
  { key: 'events', label: 'Tadbirlar', group: 'Kontent' },
  { key: 'pages', label: 'Sahifalar', group: 'Kontent' },
  { key: 'quick-links', label: 'Tezkor xizmatlar', group: 'Kontent' },
  { key: 'media', label: 'Media kutubxona', group: 'Kontent' },
  { key: 'documents', label: 'Hujjatlar', group: 'Kontent' },
  { key: 'videos', label: 'Video darsliklar', group: 'Kontent' },
  { key: 'faculties', label: 'Fakultetlar', group: 'Tuzilma' },
  { key: 'departments', label: 'Kafedralar', group: 'Tuzilma' },
  { key: 'leaders', label: 'Rahbariyat', group: 'Tuzilma' },
  { key: 'staff', label: 'Xodimlar', group: 'Tuzilma' },
  { key: 'sdg', label: 'BRM', group: 'Tuzilma' },
]

// HEMIS lavozimi → admin roli (backend `roles.HEMIS_ROLES` bilan bir xil)
export const HEMIS_ROLES: { key: string; label: string }[] = [
  { key: 'dean', label: 'Dekan' },
  { key: 'chair_head', label: 'Kafedra mudiri' },
  { key: 'teacher', label: 'O‘qituvchi' },
  { key: 'staff', label: 'Boshqa xodim' },
]

export type RoleDoc = {
  id: number
  slug: string
  name: string
  description?: string | null
  system: boolean
  scoped: boolean
  hemisRole?: string | null
  permissions: Record<string, 'read' | 'write'>
  users: number
}
