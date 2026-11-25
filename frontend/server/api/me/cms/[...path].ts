// Rol egasi (dekan, kafedra mudiri…) saytdagi kabinetdan turib o'z bo'limlarining ma'lumotlari bilan ishlaydi (yangilik, e'lon, tadbir).
// Brauzer faqat shu yerga murojaat qiladi; sessiya backend'ga Bearer sifatida uzatiladi. Ruxsat (bo'lim, fakultet doirasi, «faqat o'zi yozgan»)
// backendda admin paneldagi qoidalar bilan tekshiriladi — bu yerda faqat manzil va parametrlar oq ro'yxatdan o'tkaziladi.
const PATH = /^(posts(\/\d+)?|media)$/
const QUERY = /^(where\[(type|status)\]\[equals\]|sort|limit|page|depth)$/
const SORT = /^-?(publishedAt|createdAt|updatedAt|startsAt)$/
const UPLOAD_MAX = 10 * 1024 * 1024
const MONTH = /^(\d{4})-(0[1-9]|1[0-2])$/
const SEARCH_LANGS = ['uz', 'ru', 'en', 'zh']
const IMAGES = ['image/jpeg', 'image/png', 'image/webp']
const METHODS = ['GET', 'POST', 'PATCH', 'DELETE']

export default defineEventHandler(async (event) => {
  const path = getRouterParam(event, 'path') ?? ''
  if (!PATH.test(path)) throw createError({ statusCode: 404, statusMessage: 'Not Found' })
  const method = event.method.toUpperCase() as 'GET' | 'POST' | 'PATCH' | 'DELETE'
  if (!METHODS.includes(method)) throw createError({ statusCode: 405, statusMessage: 'Method Not Allowed' })
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) throw createError({ statusCode: 503, statusMessage: 'Backend ulanmagan' })

  const query: Record<string, string> = {}
  for (const [k, v] of Object.entries(getQuery(event))) {
    if (!QUERY.test(k) || typeof v !== 'string' || v.length > 40) continue
    if (k === 'sort' && !SORT.test(v)) continue
    query[k] = v
  }
  // Ro'yxat filtri (faqat GET /posts): sarlavha bo'yicha qidiruv (4 tilda, kamida 2 belgi) va oy. Kerakli yozuvni bitta so'rov bilan
  // topish — minglab eski yozuvni sahifama-sahifa varaqlab serverni so'rovlar bilan bosishdan ko'ra yengil.
  if (method === 'GET' && path === 'posts') {
    const raw = getQuery(event)
    const q = typeof raw.q === 'string' ? raw.q.trim().slice(0, 100) : ''
    if (q.length >= 2) SEARCH_LANGS.forEach((l, i) => { query[`where[or][${i}][title.${l}][like]`] = q })
    const m = typeof raw.month === 'string' ? MONTH.exec(raw.month) : null
    if (m) {
      const y = Number(m[1]), mo = Number(m[2])
      const next = mo === 12 ? `${y + 1}-01` : `${y}-${String(mo + 1).padStart(2, '0')}`
      query['where[publishedAt][greater_than_equal]'] = `${m[0]}-01T00:00:00+05:00`   // Toshkent vaqti
      query['where[publishedAt][less_than]'] = `${next}-01T00:00:00+05:00`
    }
  }

  let body: FormData | Record<string, unknown> | undefined
  if (method === 'POST' || method === 'PATCH') {
    if (path === 'media') {
      // Muqova surati: JPG/PNG/WEBP, 10 MB gacha
      assertUploadSize(event, UPLOAD_MAX + 512 * 1024)
      const parts = await readMultipartFormData(event)
      const file = parts?.find(p => p.name === 'file' && p.filename)
      if (!file || !IMAGES.includes(file.type ?? '') || file.data.length > UPLOAD_MAX) {
        throw createError({ statusCode: 422, statusMessage: 'Invalid image', data: { message: 'JPG, PNG yoki WEBP, 10 MB gacha' } })
      }
      const form = new FormData()
      form.append('file', new Blob([file.data], { type: file.type }), file.filename)
      form.append('_payload', JSON.stringify({ alt: { uz: '' } }))
      body = form
    }
    else {
      body = await readBody<Record<string, unknown>>(event)
      if (!body || typeof body !== 'object' || Array.isArray(body)) throw createError({ statusCode: 422, statusMessage: 'Invalid body' })
    }
  }

  try {
    return await backendUserFetch(event, `/me/cms/${path}`, { method, query, body })
  }
  catch (e) {
    // Backend xabarini (masalan «O'zbekcha sarlavha majburiy») brauzerga yetkazamiz; sarlavhaga emas, `data` ga yoziladi (unda lotin bo'lmagan harflar bo'lishi mumkin)
    const err = e as { statusCode?: number, status?: number, data?: { message?: string } }
    throw createError({ statusCode: err.statusCode ?? err.status ?? 502, statusMessage: 'Request failed', data: { message: err.data?.message ?? '' } })
  }
})
