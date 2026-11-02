import type { Field } from 'payload'

/** Sayt tillari: har bir matnli maydon shu 4 tilda saqlanadi (xitoy tili ham teng huquqli) */
export const LOCALES = ['uz', 'ru', 'en', 'zh'] as const
export type Lang = (typeof LOCALES)[number]

export const LOCALE_LABELS: Record<Lang, string> = { uz: 'Özbekça', ru: 'Rusça', en: 'Inglizça', zh: 'Xitoyça' }

export function isLang(value: unknown): value is Lang {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

type GroupOptions = {
  type?: 'text' | 'textarea'
  /** Faqat özbekça majburiy */
  required?: boolean
  hasMany?: boolean
  defaults?: Partial<Record<Lang, string>>
}

/** { uz, ru, en, zh } guruhi — admin panel bitta saqlashda barcha tillarni yuboradi */
export function i18nGroup(name: string, label: string, opts: GroupOptions = {}): Field {
  return {
    name,
    label,
    type: 'group',
    fields: LOCALES.map((lang): Field => {
      if (opts.hasMany) return { name: lang, label: LOCALE_LABELS[lang], type: 'text', hasMany: true }
      return {
        name: lang,
        label: LOCALE_LABELS[lang],
        type: opts.type ?? 'text',
        required: Boolean(opts.required && lang === 'uz'),
        defaultValue: opts.defaults?.[lang],
      }
    }),
  }
}

export type I18n = Partial<Record<Lang, string | null>>

/** Tanlangan tildagi qiymat (böş bölsa — null) */
export function pick(value: I18n | null | undefined, lang: Lang): string | null {
  const v = value?.[lang]
  return typeof v === 'string' && v.trim() ? v : null
}
