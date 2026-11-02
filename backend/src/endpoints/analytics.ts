import type { Endpoint } from 'payload'
import { isSuper } from '../lib/access'
import { recordHit, statsFor } from '../lib/analytics'
import { json } from '../lib/public'

// Sayt statistikasi: sayt (Nuxt serveri) har bir sahifa ochilishini va muhim harakatlarni yuboradi

/** POST /api/site/hit — { kind: pageview|event|search, path, lang, referrer, name, value } */
const hit: Endpoint = {
  path: '/site/hit',
  method: 'post',
  handler: async (req) => {
    try {
      const body = await req.json?.() as Record<string, unknown> | undefined
      if (body && ['pageview', 'event', 'search'].includes(String(body.kind))) await recordHit(req, body as { kind: string })
    }
    catch {
      // statistika hech qachon saytni to'xtatmaydi
    }
    return new Response(null, { status: 204 })
  },
}

/** GET /api/panel/stats?range=1|7|30|365 — faqat superadmin */
const stats: Endpoint = {
  path: '/panel/stats',
  method: 'get',
  handler: async (req) => {
    if (!isSuper(req.user as never)) return json({ message: 'Forbidden' }, 403)
    const r = req.searchParams.get('range')
    return json(await statsFor(req.payload, (['1', '7', '30', '365'].includes(r ?? '') ? r : '30') as '30'))
  },
}

export const analyticsEndpoints: Endpoint[] = [hit, stats]
