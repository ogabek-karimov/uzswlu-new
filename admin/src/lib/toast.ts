// Yuqorida çiqadigan «Saqlandi» bildiriş (AppToaster.vue körsatadi).
// API qatlami (lib/api.ts) har bir muvaffaqiyatli saqlaş / naşr / öçirişdan keyin öz-özidan çaqiradi — sahifalar alohida yozmaydi.
// Vue'siz: Node testlarida ham işlaydi.

export type Toast = { id: number; text: string; kind: 'success' | 'delete' }

type Listener = (t: Toast) => void
const listeners = new Set<Listener>()
let seq = 0

export function onToast(fn: Listener): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export function toast(text: string, kind: Toast['kind'] = 'success') {
  const t = { id: ++seq, text, kind }
  listeners.forEach(fn => fn(t))
}

/** Bu manzillar «saqlaş» emas: kiriş/çiqiş, 2FA, bildirişlarni öqilgan deb belgilaş */
const SILENT = /^\/(users\/(login|logout|unlock|2fa)|panel\/notifications)(\/|$)/

/** Muvaffaqiyatli so'rovdan keyin qaysi xabar körsatiladi (null — hec qanday) */
export function savedMessage(method: string, path: string, body?: unknown): Omit<Toast, 'id'> | null {
  if (method === 'GET' || SILENT.test(path)) return null
  if (method === 'DELETE') return { text: 'Öçirildi', kind: 'delete' }
  if (path === '/media' && method === 'POST') return { text: 'Fayl yuklandi', kind: 'success' }
  if (/\/versions\/\d+$/.test(path)) return { text: 'Versiya tiklandi', kind: 'success' }
  const status = body && typeof body === 'object' && !(body instanceof FormData) ? (body as { status?: unknown }).status : undefined
  if (status === 'published') return { text: 'Naşr qilindi', kind: 'success' }
  if (status === 'draft') return { text: 'Qoralama saqlandi', kind: 'success' }
  return { text: 'Saqlandi', kind: 'success' }
}
