export const LOCALES = ['uz', 'ru', 'en', 'zh'] as const

export type Locale = (typeof LOCALES)[number]

export function normalizeLocale(value: unknown): Locale {
  return (LOCALES as readonly string[]).includes(String(value)) ? (value as Locale) : 'uz'
}
