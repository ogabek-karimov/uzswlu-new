import type { CabinetDocument } from '#shared/types/api'

// Hujjat yuklash: multipart — file (yoki videolar uchun url) + title_uz/title_ru/title_en/title_zh.
// Fayl turi kengaytma bo'yicha tekshiriladi; backend tarkibini ham tekshirishi shart.
export default defineEventHandler(async (event): Promise<CabinetDocument> => {
  assertUploadSize(event, DOC_MAX_BYTES + 512 * 1024)
  const section = readDocSection(getRouterParam(event, 'section'))
  const rules = DOC_RULES[section]
  const parts = (await readMultipartFormData(event)) ?? []
  const field = (name: string) => parts.find(p => p.name === name && !p.filename)?.data.toString('utf8').trim() ?? ''

  const title = { uz: field('title_uz'), ru: field('title_ru'), en: field('title_en'), zh: field('title_zh') }
  if (!title.uz || Object.values(title).some(v => v.length > 255)) throw createError({ statusCode: 422, statusMessage: 'title' })

  const file = parts.find(p => p.name === 'file' && p.filename)
  const url = field('url')
  if (rules.link) {
    if (!/^https:\/\/[^\s<>"']+$/i.test(url)) throw createError({ statusCode: 422, statusMessage: 'url' })
  }
  else {
    const ext = file?.filename?.split('.').pop()?.toLowerCase() ?? ''
    if (!file || !rules.types.includes(ext) || file.data.length > DOC_MAX_BYTES) throw createError({ statusCode: 422, statusMessage: 'file' })
  }

  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) {
    // Mock: fayl xotirada data URL bo'lib turadi ("Ochish" ishlashi uchun)
    const href = rules.link ? url : `data:${file!.type || 'application/octet-stream'};base64,${file!.data.toString('base64')}`
    return addMockDoc(section, { title, url: href })
  }

  const form = new FormData()
  for (const [k, v] of Object.entries(title)) form.append(`title_${k}`, v)
  if (rules.link) form.append('url', url)
  else form.append('file', new Blob([file!.data], { type: file!.type }), file!.filename)
  return backendUserFetch<CabinetDocument>(event, `/me/documents/${section}`, { method: 'POST', body: form })
})
