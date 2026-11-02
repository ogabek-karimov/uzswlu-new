import snapshot from './snapshot.json' with { type: 'json' }
import type { Lang } from '../lib/i18n'

// HEMIS ma'lumotlari (faqat o'qish): dekan, kafedralar, talaba/o'qituvchi soni, xodimlar ro'yxati.
// HOZIRCHA NAMUNA — saytdagi vaqtinchalik ma'lumotdan olingan. HEMIS API ulanganda (universitet
// serverida, har kuni 06:00 da) shu tuzilmada haqiqiy ma'lumot bilan almashtiriladi.

type L = Record<Lang, string>

export type HemisFaculty = {
  slug: string
  order: number
  logo: string | null
  name: L
  about: L
  stats: { students: number; departments: number; programs: number; teachers: number }
  dean: Record<Lang, Record<string, unknown>>
  deanery: Record<Lang, Record<string, unknown>[]>
  programs: Record<Lang, Record<string, unknown>[]>
  departments: { id: string; head: string | null; name: L }[]
  contact: Record<Lang, { address: string; phone: string; email?: string | null; mapUrl?: string | null }>
}

export type HemisStaff = {
  id: string
  name: string
  patronymic: string | null
  group: 'lead' | 'faculty' | 'chair' | 'unit'
  employments: { department: { id: string; name: string }; position: string }[]
}

export const hemis = {
  /** Oxirgi sinxronlash vaqti; null — HEMIS hali ulanmagan (namuna ma'lumot) */
  syncedAt: snapshot.syncedAt as string | null,
  faculties: snapshot.faculties as unknown as HemisFaculty[],
  summary: snapshot.summary as { faculties: number; departments: number },
  staff: snapshot.staff as HemisStaff[],
  staffDepartments: snapshot.staffDepartments as { id: string; name: string; group: string; count: number }[],
}

export const hemisFaculty = (slug: string) => hemis.faculties.find(f => f.slug === slug) ?? null

/** Kafedra qaysi fakultetga tegishli (HEMIS tuzilmasi bo'yicha) */
export function departmentFaculty(id: string) {
  return hemis.faculties.find(f => f.departments.some(d => d.id === id)) ?? null
}
