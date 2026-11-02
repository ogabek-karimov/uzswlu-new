import type { MenuLink } from '#shared/types/api'

// Menyu bo'limlari ikonkalari (MenuGroup.id bo'yicha)
const GROUP_ICONS: Record<string, string> = {
  university: 'lucide:landmark',
  applicants: 'lucide:graduation-cap',
  activity: 'lucide:layers',
  news: 'lucide:newspaper',
  sdg: 'lucide:sprout',
  programs: 'lucide:book-open',
  video: 'lucide:circle-play',
  contact: 'lucide:phone',
}

export const groupIcon = (id: string) => GROUP_ICONS[id] ?? 'lucide:circle'

// BMT barqaror rivojlanish maqsadlarining rasmiy ranglari (1–17)
const SDG_COLORS = [
  '#E5243B', '#DDA63A', '#4C9F38', '#C5192D', '#FF3A21', '#26BDE2', '#FCC30B', '#A21942', '#FD6925',
  '#DD1367', '#FD9D24', '#BF8B2E', '#3F7E44', '#0A97D9', '#56C02B', '#00689D', '#19486A',
]

export const sdgColor = (n: number) => SDG_COLORS[n - 1] ?? '#5B4BBE'

function luminance(hex: string) {
  const [r, g, b] = [1, 3, 5].map(i => Number.parseInt(hex.slice(i, i + 2), 16) / 255)
    .map(c => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!
}

const INK = '#13112F'

/** Rangli fonda o'qiladigan matn rangi: oq yoki to'q — qaysi biri kuchliroq kontrast bersa (WCAG) */
export function sdgInk(n: number) {
  const bg = luminance(sdgColor(n)) + 0.05
  const withInk = bg / (luminance(INK) + 0.05)
  const withWhite = 1.05 / bg
  return withInk > withWhite ? INK : '#FFFFFF'
}

export const isExternal = (link: MenuLink) => /^https?:\/\//.test(link.url)
