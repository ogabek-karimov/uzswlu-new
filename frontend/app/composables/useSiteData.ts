import type { HomeData, SiteData } from '#shared/types/api'

export function useSiteData() {
  const { locale } = useI18n()
  return useFetch<SiteData>('/api/site', { key: 'site', query: { lang: locale } })
}

export function useHomeData() {
  const { locale } = useI18n()
  return useFetch<HomeData>('/api/home', { key: 'home', query: { lang: locale } })
}

export type DateStyle = 'long' | 'day' | 'month' | 'monthShort' | 'weekday' | 'time' | 'datetime'

const INTL_OPTIONS: Record<DateStyle, Intl.DateTimeFormatOptions> = {
  long: { dateStyle: 'long' },
  day: { day: 'numeric' },
  month: { month: 'long' },
  monthShort: { month: 'short' },
  weekday: { weekday: 'long' },
  time: { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' },
  datetime: { dateStyle: 'medium', timeStyle: 'short' },
}

// Brauzerlarning ko'pchiligida o'zbekcha oy nomlari yo'q ("2026 M10 20" chiqadi),
// shuning uchun o'zbek tili uchun qo'lda formatlaymiz.
const UZ_MONTHS = ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun', 'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr']
const UZ_MONTHS_SHORT = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek']
const UZ_WEEKDAYS = ['yakşanba', 'duşanba', 'seşanba', 'çorşanba', 'payşanba', 'juma', 'şanba']

function formatUz(date: Date, style: DateStyle) {
  // Toshkent vaqti (UTC+5) bo'yicha
  const local = new Date(date.getTime() + 5 * 60 * 60 * 1000)
  const day = local.getUTCDate()
  const month = local.getUTCMonth()
  const year = local.getUTCFullYear()
  const time = `${String(local.getUTCHours()).padStart(2, '0')}:${String(local.getUTCMinutes()).padStart(2, '0')}`

  switch (style) {
    case 'day': return String(day)
    case 'month': return UZ_MONTHS[month]!
    case 'monthShort': return UZ_MONTHS_SHORT[month]!
    case 'weekday': return UZ_WEEKDAYS[local.getUTCDay()]!
    case 'time': return time
    case 'datetime': return `${day}-${UZ_MONTHS_SHORT[month]}, ${year}, ${time}`
    default: return `${day}-${UZ_MONTHS[month]}, ${year}`
  }
}

/** Sanani joriy tilda formatlash: "20-oktabr, 2026" / "20 октября 2026 г." / "2026年10月20日" */
export function useFormatDate() {
  const { locale, localeProperties } = useI18n()

  return (iso: string, style: DateStyle = 'long') => {
    const date = new Date(iso)
    if (locale.value === 'uz') return formatUz(date, style)
    return new Intl.DateTimeFormat(localeProperties.value.language, { timeZone: 'Asia/Tashkent', ...INTL_OPTIONS[style] }).format(date)
  }
}
