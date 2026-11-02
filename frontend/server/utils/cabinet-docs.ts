import type { CabinetDocSection } from '#shared/types/api'

/** Hujjat bo'limlari va ruxsat etilgan turlar (oldingi saytdagi qoidalar) */
export const DOC_RULES: Record<CabinetDocSection, { types: string[]; link?: boolean }> = {
  cv: { types: ['pdf', 'doc', 'docx'] },
  books: { types: ['pdf', 'doc', 'docx'] },
  articles: { types: ['pdf', 'doc', 'docx'] },
  presentations: { types: ['ppt', 'pptx', 'pdf'] },
  // Videolar: fayl emas, faqat https havola (YouTube va boshqalar)
  videos: { types: [], link: true },
}

export const DOC_MAX_BYTES = 20 * 1024 * 1024

export function readDocSection(section: string | undefined): CabinetDocSection {
  if (!section || !(section in DOC_RULES)) throw createError({ statusCode: 404, statusMessage: 'Unknown section' })
  return section as CabinetDocSection
}
