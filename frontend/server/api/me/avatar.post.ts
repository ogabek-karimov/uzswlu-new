// Xodimning o'z surati (oldingi saytdagi qoida): JPG, PNG, WEBP, 10 MB gacha. Backend kvadrat qilib kesadi va siqadi;
// HEMIS surati o'zgarmaydi, zaxira sifatida saqlanadi ("✕" bilan unga qaytiladi).
const TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX = 10 * 1024 * 1024

export default defineEventHandler(async (event) => {
  assertUploadSize(event, MAX + 512 * 1024)
  const parts = await readMultipartFormData(event)
  const file = parts?.find(p => p.name === 'file' && p.filename)
  if (!file || !TYPES.includes(file.type ?? '') || file.data.length > MAX) {
    throw createError({ statusCode: 422, statusMessage: 'JPG, PNG yoki WEBP, 10 MB gacha' })
  }

  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) {
    // Mock: rasm xotirada data URL bo'lib turadi
    setMockPhoto(`data:${file.type};base64,${file.data.toString('base64')}`)
    return { ok: true }
  }

  const form = new FormData()
  form.append('file', new Blob([file.data], { type: file.type }), file.filename)
  return backendUserFetch(event, '/me/avatar', { method: 'POST', body: form })
})
