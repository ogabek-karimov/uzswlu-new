import { statfs } from 'node:fs/promises'
import path from 'node:path'
import type { Endpoint } from 'payload'
import { isEditor } from '../lib/access'
import { json } from '../lib/public'
import { mediaUsage, usedMediaIds } from '../lib/usage'
import { youtubeId } from '../collections/Videos'

// Admin panel: media kutubxona statistikasi, fayl qayerda ishlatilgani, YouTube ma'lumotlari

type Row = { id: number; folder?: string | null; mimeType?: string | null; filesize?: number | null; originalSize?: number | null }

/** GET /api/panel/media-stats — papkalar/turlar bo'yicha son, egallangan joy, WebP tejami, disk */
const stats: Endpoint = {
  path: '/panel/media-stats',
  method: 'get',
  handler: async (req) => {
    if (!isEditor(req.user as never)) return json({ message: 'Unauthorized' }, 401)
    const res = await req.payload.find({
      collection: 'media',
      pagination: false,
      depth: 0,
      overrideAccess: true,
      select: { folder: true, mimeType: true, filesize: true, originalSize: true },
    })
    const rows = res.docs as unknown as Row[]
    const folders: Record<string, number> = {}
    const kinds = { image: 0, pdf: 0, audio: 0 }
    let used = 0
    let saved = 0
    for (const r of rows) {
      folders[r.folder ?? 'posts'] = (folders[r.folder ?? 'posts'] ?? 0) + 1
      if (r.mimeType?.startsWith('image/')) kinds.image++
      else if (r.mimeType === 'application/pdf') kinds.pdf++
      else if (r.mimeType?.startsWith('audio/')) kinds.audio++
      used += r.filesize ?? 0
      if (r.originalSize && r.filesize && r.originalSize > r.filesize) saved += r.originalSize - r.filesize
    }
    let disk: { total: number; free: number } | null = null
    try {
      const s = await statfs(path.resolve(process.cwd(), 'media'))
      disk = { total: s.blocks * s.bsize, free: s.bavail * s.bsize }
    }
    catch {
      // disk ma'lumoti bo'lmasa ham ro'yxat ishlaydi
    }
    return json({ total: rows.length, folders, kinds, used, saved, disk })
  },
}

/** GET /api/panel/media-usage/:id — fayl ishlatilgan joylar */
const usage: Endpoint = {
  path: '/panel/media-usage/:id',
  method: 'get',
  handler: async (req) => {
    if (!isEditor(req.user as never)) return json({ message: 'Unauthorized' }, 401)
    const id = Number(req.routeParams?.id)
    if (!Number.isInteger(id)) return json({ message: 'Not found' }, 404)
    return json({ used: await mediaUsage(req.payload, id, req) })
  },
}

/** GET /api/panel/media-used — ishlatilayotgan fayllar ID'lari ("Ishlatilmaganlar" filtri) */
const used: Endpoint = {
  path: '/panel/media-used',
  method: 'get',
  handler: async (req) => {
    if (!isEditor(req.user as never)) return json({ message: 'Unauthorized' }, 401)
    return json({ ids: [...await usedMediaIds(req.payload)].map(Number) })
  },
}

/** GET /api/panel/youtube?url= — YouTube'dan nom, muqova va davomiylik (faqat ochiq ma'lumot) */
const youtube: Endpoint = {
  path: '/panel/youtube',
  method: 'get',
  handler: async (req) => {
    if (!isEditor(req.user as never)) return json({ message: 'Unauthorized' }, 401)
    const id = youtubeId(req.searchParams.get('url'))
    if (!id) return json({ message: 'YouTube havolasi notoğri' }, 400)
    const watch = `https://www.youtube.com/watch?v=${id}`
    const result: { id: string; url: string; title: string | null; author: string | null; thumbnail: string; duration: string | null } = {
      id, url: watch, title: null, author: null, thumbnail: `https://i.ytimg.com/vi/${id}/hqdefault.jpg`, duration: null,
    }
    try {
      const res = await fetch(`https://www.youtube.com/oembed?url=${encodeURIComponent(watch)}&format=json`, { signal: AbortSignal.timeout(6000) })
      if (res.status === 404 || res.status === 401) return json({ message: 'Video topilmadi yoki yopiq' }, 404)
      if (res.ok) {
        const o = await res.json() as { title?: string; author_name?: string }
        result.title = o.title ?? null
        result.author = o.author_name ?? null
      }
    }
    catch {
      return json({ message: 'YouTube javob bermadi — keyinroq urinib köring' }, 502)
    }
    // Davomiylik oEmbed'da yo'q — video sahifasidagi lengthSeconds'dan (topilmasa qo'lda kiritiladi)
    try {
      const html = await fetch(watch, { signal: AbortSignal.timeout(6000), headers: { 'accept-language': 'en' } }).then(r => r.text())
      const sec = Number(html.match(/"lengthSeconds":"(\d+)"/)?.[1])
      if (sec > 0) {
        const h = Math.floor(sec / 3600)
        const m = Math.floor((sec % 3600) / 60)
        const s = String(sec % 60).padStart(2, '0')
        result.duration = h ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`
      }
    }
    catch {
      // davomiylik ixtiyoriy
    }
    return json(result)
  },
}

export const mediaEndpoints: Endpoint[] = [stats, usage, used, youtube]
