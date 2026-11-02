import type { I18n, MediaDoc } from './api'
import type { PostType } from './constants'

export type Attachment = { id?: string; file: MediaDoc | number; title?: I18n; display: 'embed' | 'open' | 'download' | 'link'; height?: number }

export type Post = {
  id: number
  type: PostType
  title: I18n
  excerpt?: I18n
  body?: I18n
  slug?: string
  category?: { id: number; name: I18n } | number | null
  sdg?: number
  cover?: MediaDoc | number | null
  coverByLang?: { ru?: MediaDoc | number | null; en?: MediaDoc | number | null; zh?: MediaDoc | number | null }
  gallery?: (MediaDoc | number)[]
  attachments?: Attachment[]
  tags?: { uz?: string[]; ru?: string[]; en?: string[]; zh?: string[] }
  author?: { id: number; name: string; position?: string | null } | number | null
  publishedAt?: string | null
  status: 'draft' | 'published'
  hidden?: boolean
  startsAt?: string | null
  endsAt?: string | null
  location?: I18n
  updatedAt?: string
  createdAt?: string
}

export type PostState = 'published' | 'draft' | 'scheduled'

/** Saytdagi holati: kelajak vaqtli nashr — rejalashtirilgan */
export function postState(p: Pick<Post, 'status' | 'publishedAt'>): PostState {
  if (p.status !== 'published') return 'draft'
  if (p.publishedAt && new Date(p.publishedAt).getTime() > Date.now()) return 'scheduled'
  return 'published'
}

export const STATE_BADGE: Record<PostState, { label: string; cls: string }> = {
  published: { label: 'Naşr qilingan', cls: 'bg-[#DDFBF0] text-[#0B5A43]' },
  draft: { label: 'Qoralama', cls: 'bg-[#F1F0F5] text-muted' },
  scheduled: { label: 'Rejalaştirilgan', cls: 'bg-[#FEF3DC] text-[#8A5A00]' },
}

/** Tilning to'ldirilganligi: 1 — sarlavha va matn bor, 0.5 — faqat sarlavha, 0 — bo'sh */
export function langFill(p: Pick<Post, 'title' | 'body' | 'excerpt'>, lang: keyof I18n): 0 | 0.5 | 1 {
  const title = (p.title?.[lang] ?? '').trim()
  if (!title) return 0
  const body = (p.body?.[lang] ?? '').replace(/<[^>]+>/g, '').trim()
  return body || (p.excerpt?.[lang] ?? '').trim() ? 1 : 0.5
}

export function mediaUrl(m: MediaDoc | number | null | undefined, size: 'thumb' | 'card' | 'hero' = 'thumb') {
  if (!m || typeof m === 'number') return null
  return m.sizes?.[size]?.url ?? m.url ?? null
}
