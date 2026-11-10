// Backend bilan ishlash. Cookie avtomatik yuboriladi (bir xil manzil — /api proxy).
// Django/DRF backend'da admin panel API'si /api/cms ostida (Payload REST bilan bir xil shakl).

export class ApiError extends Error {
  status: number
  data?: unknown
  constructor(status: number, message: string, data?: unknown) {
    super(message)
    this.status = status
    this.data = data
  }
}

export const API_BASE: string = import.meta.env?.VITE_API_BASE ?? '/api/cms'

type Query = Record<string, unknown>

/** Payload `where` va boshqa obyektlarni query-string'ga: where[type][equals]=news */
export function qs(params: Query, prefix = ''): string {
  const parts: string[] = []
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    const name = prefix ? `${prefix}[${key}]` : key
    if (typeof value === 'object' && !Array.isArray(value)) parts.push(qs(value as Query, name))
    else if (Array.isArray(value)) value.forEach((v, i) => parts.push(typeof v === 'object' ? qs(v as Query, `${name}[${i}]`) : `${encodeURIComponent(`${name}[${i}]`)}=${encodeURIComponent(String(v))}`))
    else parts.push(`${encodeURIComponent(name)}=${encodeURIComponent(String(value))}`)
  }
  return parts.filter(Boolean).join('&')
}

/** So'rov muddati: oddiy so'rov 30 s, fayl yuklash (FormData) 2 daqiqa. Undan oshsa — "javob bermadi" xabari, sahifa cheksiz yuklanmaydi. */
export const TIMEOUT_MS = { default: 30_000, upload: 120_000 }

/** Sessiya tugaganda (himoyalangan so'rovga 401) chaqiriladi; ulanishi main.ts da */
let unauthorizedHandler: (() => void) | null = null
export function setUnauthorizedHandler(fn: (() => void) | null) {
  unauthorizedHandler = fn
}

/** Bu manzillarda 401 — "login/parol noto'g'ri" yoki "hali kirmagan" degani; sessiya tugadi emas */
const AUTH_PATHS = /^\/users\/(login|login\/2fa|me|logout)(\/|$)/

/** Server JSON o'rniga HTML (nginx 502/504 sahifasi) yoki bo'sh javob qaytarganda tushunarli xabar */
export function httpMessage(status: number): string {
  if (status === 401) return 'Sessiya tugagan. Qayta kiring.'
  if (status === 403) return 'Bu amal uchun ruxsat yo‘q.'
  if (status === 404) return 'Topilmadi.'
  if (status === 413) return 'Fayl yoki so‘rov hajmi juda katta.'
  if (status === 429) return 'Juda ko‘p so‘rov yuborildi. Birozdan keyin qayta urinib ko‘ring.'
  if (status === 502 || status === 503 || status === 504) return `Server vaqtincha javob bermayapti (${status}). Birozdan keyin qayta urinib ko‘ring.`
  if (status >= 500) return `Serverda xatolik (${status}). Birozdan keyin qayta urinib ko‘ring.`
  return `Xato (${status})`
}

function parseJson(text: string): { ok: true; value: unknown } | { ok: false } {
  if (!text) return { ok: true, value: null }
  try { return { ok: true, value: JSON.parse(text) } }
  catch { return { ok: false } }
}

async function request<T>(method: string, path: string, body?: unknown, query?: Query): Promise<T> {
  const url = `${API_BASE}${path}${query ? `?${qs(query)}` : ''}`
  const isForm = body instanceof FormData
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), isForm ? TIMEOUT_MS.upload : TIMEOUT_MS.default)

  let res: Response
  let text: string
  try {
    res = await fetch(url, {
      method,
      credentials: 'include',
      headers: body && !isForm ? { 'content-type': 'application/json' } : undefined,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
      signal: controller.signal,
    })
    text = await res.text()
  }
  catch (e) {
    if ((e as Error).name === 'AbortError') throw new ApiError(0, 'Server javob bermadi (vaqt tugadi). Internetni tekshirib, qayta urinib ko‘ring.')
    throw new ApiError(0, 'Server bilan aloqa yo‘q. Internetni tekshirib, qayta urinib ko‘ring.')
  }
  finally {
    clearTimeout(timer)
  }

  const parsed = parseJson(text)
  const data = parsed.ok ? (parsed.value as { errors?: { message?: string }[]; message?: string } | null) : null
  if (!res.ok) {
    if (res.status === 401 && !AUTH_PATHS.test(path)) unauthorizedHandler?.()
    // Javob JSON bo'lmasa (HTML xato sahifasi) — xom matnni emas, holat bo'yicha tushunarli xabar
    const message = data?.errors?.[0]?.message ?? data?.message ?? httpMessage(res.status)
    throw new ApiError(res.status, message, data)
  }
  if (!parsed.ok) throw new ApiError(res.status, 'Server kutilmagan javob qaytardi. Birozdan keyin qayta urinib ko‘ring.')
  return parsed.value as T
}

export const api = {
  get: <T>(path: string, query?: Query) => request<T>('GET', path, undefined, query),
  post: <T>(path: string, body?: unknown, query?: Query) => request<T>('POST', path, body, query),
  patch: <T>(path: string, body?: unknown, query?: Query) => request<T>('PATCH', path, body, query),
  del: <T>(path: string, query?: Query) => request<T>('DELETE', path, undefined, query),
}

export type Paginated<T> = { docs: T[]; totalDocs: number; page: number; totalPages: number; limit: number }

/** Faylni Media'ga yuklash (rasm, PDF) */
export async function uploadMedia(file: File, data: Record<string, unknown> = {}) {
  const form = new FormData()
  form.append('file', file)
  form.append('_payload', JSON.stringify(data))
  const res = await api.post<{ doc: MediaDoc }>('/media', form)
  return res.doc
}

export type I18n = { uz?: string | null; ru?: string | null; en?: string | null; zh?: string | null }

export type MediaDoc = {
  id: number
  url?: string | null
  filename?: string | null
  mimeType?: string | null
  filesize?: number | null
  createdAt?: string | null
  width?: number | null
  height?: number | null
  alt?: I18n
  sizes?: Record<string, { url?: string | null } | undefined>
}

export type User = {
  id: number
  name: string
  username?: string | null
  email?: string | null
  role: 'superadmin' | 'editor' | 'faculty' | 'pages' | 'sdg'
  status?: 'active' | 'invited' | 'disabled'
  position?: string | null
  department?: string | null
  scope?: string | null
  avatar?: MediaDoc | number | null
  lockUntil?: string | null
  loginAttempts?: number
  twoFactorEnabled?: boolean
  createdAt?: string
  updatedAt?: string
}
