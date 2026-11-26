// Hujjat fayllari: PDF va Office (Word, Excel, PowerPoint). Backend ham shu turlarni qabul qiladi
// (apps.core.models.DOC_EXT; makro/ichki ob'ekt bo'lsa rad etiladi). Rasm va MP3 — alohida.

export const DOC_EXTS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'] as const

/** <input type="file" accept> — hujjatlar uchun */
export const DOC_ACCEPT = [
  ...DOC_EXTS.map(e => `.${e}`),
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
].join(',')

/** Fayl nomidan kengaytma (kichik harflarda): "Reja 2023.DOCX" → "docx" */
export function extOf(name?: string | null): string {
  const m = /\.([a-z0-9]+)$/i.exec(name ?? '')
  return m ? m[1]!.toLowerCase() : ''
}

export function isDocFile(name?: string | null): boolean {
  return (DOC_EXTS as readonly string[]).includes(extOf(name))
}

/** Fayl nomidan sarlavha: kengaytma, pastki chiziq va ortiqcha bo'shliqlarsiz */
export function titleFromName(name: string): string {
  return name.replace(/\.[a-z0-9]+$/i, '').replace(/[_]+/g, ' ').replace(/\s+/g, ' ').trim()
}

/** Belgi uchun rang: PDF qizil, Word ko'k, Excel yashil, PowerPoint to'q sariq */
export function docTone(ext: string): { bg: string; fg: string } {
  if (ext.startsWith('doc')) return { bg: '#E7F0FD', fg: '#1D4ED8' }
  if (ext.startsWith('xls')) return { bg: '#E6F6EC', fg: '#067647' }
  if (ext.startsWith('ppt')) return { bg: '#FEEFE3', fg: '#C2410C' }
  if (ext === 'pdf') return { bg: '#FDECEA', fg: '#B42318' }
  return { bg: '#EEF0F5', fg: '#475467' }
}
