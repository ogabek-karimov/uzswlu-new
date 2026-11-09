import { ref } from 'vue'
import { api } from './api'
import { relative } from './format'

// HEMIS ma'lumoti (faqat o'qish) — fakultetlar, kafedralar, xodimlar sahifalari uchun bitta so'rov
export type HemisData = {
  syncedAt: string | null
  stale?: boolean // nusxa 30 soatdan eski — kechagi sinxronlash o'tmagan
  lastError?: string | null // faqat superadmin ko'radi
  faculties: { slug: string; name: string; stats: { students: number; departments: number; programs: number; teachers: number }; dean: string; departments: { id: string; name: string; head: string | null }[] }[]
  staff: { id: string; name: string; patronymic: string | null; group: string; employments: { department: { id: string; name: string }; position: string }[] }[]
  staffDepartments: { id: string; name: string; group: string; count: number }[]
}

const data = ref<HemisData | null>(null)
let pending: Promise<HemisData> | null = null

export function useHemis() {
  if (!data.value && !pending) {
    pending = api.get<HemisData>('/panel/hemis').then((d) => { data.value = d; return d }).finally(() => { pending = null })
  }
  return data
}

/** "HEMIS: bugun 06:00 da yangilandi" yoki namuna ekanini aytadi */
export function hemisBadge(d: HemisData | null) {
  if (!d) return { text: 'HEMIS…', ok: false }
  if (!d.syncedAt) return { text: 'HEMIS hali ulanmagan — namuna ma’lumot', ok: false }
  const when = relative(d.syncedAt).toLowerCase()
  if (d.stale || d.lastError) return { text: `HEMIS: ma’lumot eskirgan (${when} da yangilangan)${d.lastError ? ` — oxirgi urinish xato: ${d.lastError}` : ''}`, ok: false }
  return { text: `HEMIS: ${when} da yangilandi`, ok: true }
}
