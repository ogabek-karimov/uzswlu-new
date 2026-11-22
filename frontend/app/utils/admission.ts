// Faol qabul yili (admin → Qabul yillari → «Faol qilish»): saytning hamma joyida shundan olinadi.
// full — "2026/2027" (sarlavhalar), short — "2026" (header tugmasi). Sayt ma'lumoti kelmasa — zaxira qiymat.
export function admissionYear(site?: { admissionYear?: string } | null) {
  const full = site?.admissionYear || '2026/2027'
  return { full, short: full.split('/')[0] || full }
}

// Qabul sahifasi manzili yildan mustaqil
export const ADMISSION_PATH = '/qabul'
