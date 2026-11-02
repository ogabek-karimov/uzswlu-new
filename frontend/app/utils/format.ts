/**
 * Statistik sonni sahifa uchun qisqartiradi (hozirgi saytdagi uslubda):
 * 47 → "47", 1137 → "1100" + "+", 17384 → "17" + "K+".
 * Qo'shimcha qism alohida qaytadi, chunki u boshqa rangda ko'rsatiladi.
 */
export function formatStat(value: number): { number: string; suffix: string } {
  if (value >= 10_000) return { number: String(Math.floor(value / 1000)), suffix: 'K+' }
  if (value >= 1_000) return { number: String(Math.floor(value / 100) * 100), suffix: '+' }
  return { number: String(value), suffix: '' }
}
