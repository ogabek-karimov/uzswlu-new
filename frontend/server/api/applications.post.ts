import type { AppealResult } from '#shared/types/api'

const FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
const MAX_FILE = 5 * 1024 * 1024
const FILES = ['passportFile', 'diplomaFile', 'photoFile'] as const
const TEXT = ['lastName', 'firstName', 'middleName', 'passport', 'country', 'address', 'gender', 'faculty', 'studyForm', 'degree', 'program', 'phone', 'email', 'lang', 'consent'] as const

// Xorijiy abituriyent arizasi («Ariza şakli»): maydonlar va 3 ta fayl shu yerda tekshiriladi, keyin backend'ga uzatiladi
export default defineEventHandler(async (event): Promise<AppealResult> => {
  assertUploadSize(event, MAX_FILE * 3 + 512 * 1024)
  const parts = await readMultipartFormData(event)
  if (!parts) throw createError({ statusCode: 400, statusMessage: 'Form data required' })
  const field = (name: string) => parts.find(p => p.name === name && !p.filename)?.data.toString('utf8').replace(/\s+/g, ' ').trim() ?? ''
  const form = Object.fromEntries(TEXT.map(k => [k, field(k)])) as Record<(typeof TEXT)[number], string>
  form.passport = form.passport.replace(/\s/g, '').toUpperCase()

  const invalid = (statusMessage: string) => createError({ statusCode: 422, statusMessage })
  const len = (v: string, a: number, b: number) => v.length >= a && v.length <= b
  if (!len(form.lastName, 2, 70) || !len(form.firstName, 2, 60) || form.middleName.length > 60) throw invalid('Invalid name')
  if (!/^[A-Z0-9]{5,20}$/.test(form.passport)) throw invalid('Invalid passport')
  if (!len(form.country, 2, 80) || !len(form.address, 5, 300) || !len(form.faculty, 2, 200) || !len(form.program, 2, 300)) throw invalid('Invalid form')
  if (!['male', 'female'].includes(form.gender) || !['day', 'distance', 'evening'].includes(form.studyForm) || !['bachelor', 'master', 'doctorate'].includes(form.degree)) throw invalid('Invalid form')
  if (!/^\+?[\d\s()-]{7,20}$/.test(form.phone)) throw invalid('Invalid phone')
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email) || form.email.length > 200) throw invalid('Invalid email')
  if (form.consent !== 'yes') throw invalid('Consent required')
  const files = FILES.map(name => parts.find(p => p.name === name && p.filename && p.data.length))
  if (files.some(f => !f || !FILE_TYPES.includes(f.type ?? '') || f.data.length > MAX_FILE)) throw invalid('Invalid file')

  const { apiBase, apiToken } = useRuntimeConfig(event)
  if (!apiBase) return { number: `AR-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 100_000)).padStart(5, '0')}` }

  const body = new FormData()
  for (const [key, value] of Object.entries(form)) body.append(key, value)
  FILES.forEach((name, i) => {
    const f = files[i]!
    body.append(name, new Blob([new Uint8Array(f.data)], { type: f.type }), f.filename)
  })
  return $fetch<AppealResult>('/applications', {
    baseURL: apiBase,
    method: 'POST',
    body,
    timeout: 30000,
    headers: apiToken ? { Authorization: `Bearer ${apiToken}` } : undefined,
  })
})
