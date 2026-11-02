// Backend (Payload REST) bilan ishlash. Cookie avtomatik yuboriladi (bir xil manzil — /api proxy).

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: unknown) {
    super(message)
  }
}

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

async function request<T>(method: string, path: string, body?: unknown, query?: Query): Promise<T> {
  const url = `/api${path}${query ? `?${qs(query)}` : ''}`
  const isForm = body instanceof FormData
  const res = await fetch(url, {
    method,
    credentials: 'include',
    headers: body && !isForm ? { 'content-type': 'application/json' } : undefined,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  })
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) {
    const message = data?.errors?.[0]?.message ?? data?.message ?? `Xato (${res.status})`
    throw new ApiError(res.status, message, data)
  }
  return data as T
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
  createdAt?: string
  updatedAt?: string
}
