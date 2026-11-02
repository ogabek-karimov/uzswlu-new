import type { HemisEmployment, LocalizedText, StaffContactType, StaffDocSection, StaffNetwork, StaffProfile, StaffScienceNetwork } from '#shared/types/api'

const foldName = (s: string) => s.toLowerCase().replace(/[‘’ʻʼ`´']/g, '\'')

/**
 * To'liq ism va vizitka qatorlari (oldingi saytdagi qoida): HEMIS'dagi ism tartibi saqlanadi,
 * unda sharif bo'lmasa oxiriga qo'shiladi; vizitkada sharif ism-familiyadan keyingi qatorda.
 */
export function staffName(name: string, patronymic?: string | null) {
  const base = name.replace(/\s+/g, ' ').trim()
  const pat = (patronymic ?? '').trim()
  if (!pat) return { full: base, main: base, sharif: '' }
  if (!foldName(base).includes(foldName(pat))) return { full: `${base} ${pat}`, main: base, sharif: pat }
  if (base.length > pat.length && foldName(base).endsWith(foldName(pat))) {
    return { full: base, main: base.slice(0, base.length - pat.length).trim(), sharif: base.slice(-pat.length) }
  }
  return { full: base, main: base, sharif: '' }
}

/** HEMIS o'qituvchilik lavozimlari kodlari (Stajer-o'qituvchi … Professor) */
const TEACHING_CODES = new Set(['11', '12', '13', '14', '15'])
/** HEMIS employeeStatus: ishdan bo'shagan */
const DISMISSED = '14'

/**
 * HEMIS ish joylaridan ko'rsatiladigan lavozim va bo'limlar (oldingi saytdagi qoida):
 * ishdan bo'shaganlar tashlanadi; avval boshqaruv/asosiy lavozim, keyin o'qituvchilik lavozimlari (kod 11–15);
 * guruh ichida HEMIS tartibi; takrorlar olib tashlanadi; bo'limlar o'z lavozimi bilan bir xil tartibda.
 */
export function staffRoles(employments: HemisEmployment[]) {
  const rows = employments
    .filter(e => e.status?.code !== DISMISSED)
    .map((e, i) => ({ e, i, teach: TEACHING_CODES.has(e.position.code) ? 1 : 0 }))
    .sort((a, b) => a.teach - b.teach || a.i - b.i)
  const positions = [...new Set(rows.map(r => r.e.position.name))]
  const departments = [...new Map(rows.map(r => [r.e.department.id, r.e.department])).values()]
  return { positions, departments }
}

/** "Ibragimov Otabek Alisherovich" → "IO" */
export function initials(name: string) {
  const words = name.split(/\s+/).filter(Boolean)
  return ((words[0]?.[0] ?? '') + (words[1]?.[0] ?? '')).toUpperCase()
}

// Surati yo'q xodimlar uchun bosh harf foni — ID bo'yicha doim bir xil rang
const TINTS = [
  'bg-brand-100 text-brand-700',
  'bg-accent-100 text-accent-700',
  'bg-[#fdf0e1] text-[#8a4b12]',
  'bg-[#fce7ec] text-[#9d1c3f]',
]

export function avatarTint(id: string) {
  let sum = 0
  for (const ch of id) sum += ch.charCodeAt(0)
  return TINTS[sum % TINTS.length]!
}

// tile — kartadagi ikonka foni; hover — chap kartadagi yumaloq ikonkaning hover rangi (brend rangi)
const INSTAGRAM = 'bg-[linear-gradient(135deg,#feda75,#fa7e1e_30%,#d62976_60%,#962fbf_85%,#4f5bd5)]'

/** Ijtimoiy tarmoqlar */
export const staffNetworks: Record<StaffNetwork, { label: string; icon: string; tile: string; hover: string }> = {
  instagram: { label: 'Instagram', icon: 'simple-icons:instagram', tile: INSTAGRAM, hover: 'hover:bg-[linear-gradient(45deg,#f9a03f,#d6249f,#5851db)]' },
  threads: { label: 'Threads', icon: 'simple-icons:threads', tile: 'bg-black', hover: 'hover:bg-black' },
  facebook: { label: 'Facebook', icon: 'simple-icons:facebook', tile: 'bg-[#1877f2]', hover: 'hover:bg-[#1877f2]' },
  linkedin: { label: 'LinkedIn', icon: 'simple-icons:linkedin', tile: 'bg-[#0a66c2]', hover: 'hover:bg-[#0a66c2]' },
  x: { label: 'X', icon: 'simple-icons:x', tile: 'bg-black', hover: 'hover:bg-black' },
  youtube: { label: 'YouTube', icon: 'simple-icons:youtube', tile: 'bg-[#ff0000]', hover: 'hover:bg-[#ff0000]' },
}

const digits = (s: string) => s.replace(/[^\d+]/g, '')

/** Aloqa turlari: yorliq (i18n kaliti staff.contact.*), ikonka, rang va havola */
export const staffContacts: Record<StaffContactType, { icon: string; tile: string; hover: string; href: (v: string) => string; external?: boolean }> = {
  email: { icon: 'lucide:mail', tile: 'bg-brand-900', hover: 'hover:bg-brand-700', href: v => `mailto:${v}` },
  telegram: {
    icon: 'simple-icons:telegram', tile: 'bg-[#229ed9]', hover: 'hover:bg-[#229ed9]', external: true,
    href: v => (/^https?:\/\//.test(v) ? v : `https://t.me/${v.replace(/^@/, '')}`),
  },
  // wa.me kompyuterda ham, telefonda ham to'g'ri WhatsApp'ni ochadi
  whatsapp: { icon: 'simple-icons:whatsapp', tile: 'bg-[#25d366]', hover: 'hover:bg-[#25d366]', external: true, href: v => `https://wa.me/${digits(v).replace('+', '')}` },
  mobile: { icon: 'lucide:smartphone', tile: 'bg-[#2e7d32]', hover: 'hover:bg-[#2e7d32]', href: v => `tel:${digits(v)}` },
  phone: { icon: 'lucide:phone', tile: 'bg-brand-800', hover: 'hover:bg-brand-700', href: v => `tel:${digits(v)}` },
  office: {
    icon: 'lucide:map-pin', tile: 'bg-[#14a37f]', hover: 'hover:bg-[#14a37f]', external: true,
    href: v => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(v)}`,
  },
}

/** Ilmiy profillar */
export const staffScience: Record<StaffScienceNetwork, { label: string; icon: string; tile: string }> = {
  orcid: { label: 'ORCID', icon: 'simple-icons:orcid', tile: 'bg-[#7a9a1f]' },
  scholar: { label: 'Google Scholar', icon: 'simple-icons:googlescholar', tile: 'bg-[#4285f4]' },
  scopus: { label: 'Scopus', icon: 'simple-icons:scopus', tile: 'bg-[#e9711c]' },
  researchgate: { label: 'ResearchGate', icon: 'simple-icons:researchgate', tile: 'bg-[#00a88f]' },
}

/** Kartadagi bitta plita (Aloqa / Ijtimoiy tarmoqlar / Ilmiy profillar) */
export interface StaffTile {
  key: string
  label: string
  sub: string
  icon: string
  tile: string
  href: string
  external: boolean
}

const hostOf = (url: string) => {
  try {
    return new URL(url).host.replace(/^www\./, '')
  }
  catch {
    return url
  }
}

/** Profil ma'lumotidan plitalar — Staff sahifasi va kabinetda bir xil ko'rinish uchun */
export function staffTiles(person: Pick<StaffProfile, 'contacts' | 'socials' | 'science'>, t: (key: string) => string) {
  const contacts: StaffTile[] = person.contacts.map((c, i) => ({
    key: `${c.type}-${i}`,
    label: t(`staff.contact.${c.type}`),
    // Telegram — "Xabar yozish", qolganlari — qiymatning o'zi
    sub: c.type === 'telegram' ? t('staff.profile.writeMessage') : c.value,
    icon: staffContacts[c.type].icon,
    tile: staffContacts[c.type].tile,
    href: staffContacts[c.type].href(c.value),
    external: !!staffContacts[c.type].external,
  }))
  const socials: StaffTile[] = person.socials.map(s => ({
    key: s.network, label: staffNetworks[s.network].label, sub: t('staff.profile.personalPage'),
    icon: staffNetworks[s.network].icon, tile: staffNetworks[s.network].tile, href: s.url, external: true,
  }))
  const science: StaffTile[] = person.science.map(s => ({
    key: s.network, label: staffScience[s.network].label, sub: hostOf(s.url),
    icon: staffScience[s.network].icon, tile: staffScience[s.network].tile, href: s.url, external: true,
  }))
  return { contacts, socials, science }
}

/** Hujjat nomi: tanlangan tilda; xitoychasi bo'lmasa inglizcha, u ham bo'lmasa o'zbekcha (oldingi saytdagi qoida) */
export function docTitleFor(title: LocalizedText, lang: string) {
  return title[lang as keyof LocalizedText] || (lang === 'zh' ? title.en : '') || title.uz
}

/** Hujjat bo'limlari (yorliq i18n kaliti staff.docs.*) */
export const staffDocs: Record<StaffDocSection, { icon: string; tile: string }> = {
  cv: { icon: 'lucide:file-user', tile: 'bg-[#d64545]' },
  books: { icon: 'lucide:book-open', tile: 'bg-[#2f6fd6]' },
  articles: { icon: 'lucide:newspaper', tile: 'bg-[#1f9d66]' },
}
