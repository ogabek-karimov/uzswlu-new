import { reactive } from 'vue'
import { toNewAlphabet } from './alphabet'
import type { Action, Section } from './api'

// Rol bo'limlari — SERVERDAN keladi (`/users/me` → `sections`, manba: backend `apps/accounts/roles.py` SECTIONS).
// Yangi bo'lim backendga qo'shilsa, ruxsatlar jadvallari, profil va faollik jurnali uni o'zi ko'rsatadi — bu yerda hech narsa yozilmaydi.
export const SECTIONS = reactive<Section[]>([])
export const SECTION_PATHS = reactive<Record<string, string>>({})

export function setSections(list: Section[] | undefined) {
  if (!list?.length) return
  SECTIONS.splice(0, SECTIONS.length, ...list.map(s => ({ ...s, label: toNewAlphabet(s.label), group: toNewAlphabet(s.group) })))
  for (const k of Object.keys(SECTION_PATHS)) delete SECTION_PATHS[k]
  for (const s of list) SECTION_PATHS[s.key] = s.path
}

export type RoleDoc = {
  id: number
  slug: string
  name: string
  description?: string | null
  system: boolean
  scoped: boolean
  editAll?: boolean
  /** rolning o'z belgilari (tahrirlash uchun) */
  permissions: Record<string, Action[]>
  /** biriktirilgan ruxsat to'plamlari */
  permissionSets?: number[]
  /** yakuniy ruxsat: o'z belgilari + to'plamlar */
  effective?: Record<string, Action[]>
  users: number
}

// Amallar (backend `roles.ACTIONS` bilan bir xil): yozish amallaridan biri bo'lsa — ko'rish ham avtomatik
export const ACTIONS: { key: Action; label: string; short: string }[] = [
  { key: 'read', label: 'Köriş', short: 'Köriş' },
  { key: 'create', label: 'Qöşiş', short: 'Qöşiş' },
  { key: 'update', label: 'Tahrirlaş', short: 'Tahrir' },
  { key: 'delete', label: 'Öçiriş', short: 'Öçiriş' },
]

/** Ruxsatlar kutubxonasidagi to'plam */
export type PermissionSetDoc = {
  id: number
  name: string
  description?: string | null
  permissions: Record<string, Action[]>
  roles: number
}

/** Amallar ro'yxatini qisqa matnga: «Köriş, Qöşiş, Tahrir» yoki «Hammasi» */
export function actionsLabel(acts: Action[] | undefined): string {
  if (!acts?.length) return 'yöq'
  if (ACTIONS.every(a => acts.includes(a.key))) return 'hammasi'
  return ACTIONS.filter(a => acts.includes(a.key)).map(a => a.short.toLowerCase()).join(', ')
}
