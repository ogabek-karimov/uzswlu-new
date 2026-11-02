import { ref } from 'vue'
import { api } from './api'
import { relative } from './format'

// HEMIS ma'lumoti (faqat o'qish) — fakultetlar, kafedralar, xodimlar sahifalari uchun bitta so'rov
export type HemisData = {
  syncedAt: string | null
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
  return { text: `HEMIS: ${relative(d.syncedAt).toLowerCase()} da yangilandi`, ok: true }
}
