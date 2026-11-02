import type { AppealResult } from '#shared/types/api'

const FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
const MAX_FILE = 10 * 1024 * 1024

// Virtual qabulxona murojaati. Maydonlar shu yerda tekshiriladi, keyin backend'ga uzatiladi.
export default defineEventHandler(async (event): Promise<AppealResult> => {
  const parts = await readMultipartFormData(event)
  if (!parts) throw createError({ statusCode: 400, statusMessage: 'Form data required' })

  const field = (name: string) => parts.find(p => p.name === name && !p.filename)?.data.toString('utf8').trim() ?? ''
  const file = parts.find(p => p.name === 'file' && p.filename && p.data.length)

  const form = {
    name: field('name'),
    phone: field('phone'),
    email: field('email'),
    recipient: field('recipient'),
    message: field('message'),
    consent: field('consent'),
  }

  const invalid = (statusMessage: string) => createError({ statusCode: 422, statusMessage })
  if (form.name.length < 3 || form.name.length > 200) throw invalid('Invalid name')
  if (!/^\+?[\d\s()-]{7,20}$/.test(form.phone)) throw invalid('Invalid phone')
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email) || form.email.length > 200) throw invalid('Invalid email')
  if (!/^[\w-]{1,40}$/.test(form.recipient)) throw invalid('Invalid recipient')
  if (form.message.length < 10 || form.message.length > 5000) throw invalid('Invalid message')
  if (form.consent !== 'yes') throw invalid('Consent required')
  if (file && (!FILE_TYPES.includes(file.type ?? '') || file.data.length > MAX_FILE)) throw invalid('Invalid file')

  const { apiBase, apiToken } = useRuntimeConfig(event)

  if (!apiBase) {
    // Mock: murojaat saqlanmaydi, faqat raqam qaytadi
    return { number: `VQ-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 100_000)).padStart(5, '0')}` }
  }

  const body = new FormData()
  for (const [key, value] of Object.entries(form)) body.append(key, value)
  if (file) body.append('file', new Blob([new Uint8Array(file.data)], { type: file.type }), file.filename)

  return $fetch<AppealResult>('/appeals', {
    baseURL: apiBase,
    method: 'POST',
    body,
    timeout: 20000,
    headers: apiToken ? { Authorization: `Bearer ${apiToken}` } : undefined,
  })
})
