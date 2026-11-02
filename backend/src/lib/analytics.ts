import { createHash } from 'node:crypto'
import type { Payload, PayloadRequest } from 'payload'
import { clientIp, parseUserAgent } from './request'

// Sayt statistikasi — cookie'siz va shaxsiy ma'lumotsiz (Umami usulida):
// IP manzil saqlanmaydi; tashrifchi kodi = hash(kunlik tuz + IP + brauzer), tuz har kuni almashadi,
// shuning uchun bir kishini kunlar bo'yicha kuzatib bo'lmaydi va cookie banner kerak emas.
// Xom yozuvlar alohida jadvalda (analytics.events — Payload kolleksiyasi emas, har bir ko'rish uchun yengil INSERT).

type Pool = { query: (sql: string, params?: unknown[]) => Promise<{ rows: any[] }> }
const poolOf = (payload: Payload) => (payload.db as unknown as { pool: Pool }).pool

const BOTS = /bot|crawl|spider|slurp|preview|headless|lighthouse|monitor|curl|wget|python|axios|node-fetch/i

// Jadval Payload'ning `public` sxemasida EMAS: Payload dev rejimida o'zi bilmagan jadvalni o'chirmoqchi bo'lib,
// "rozimisiz?" deb javob kutib qoladi va backend butunlay to'xtaydi. Alohida `analytics` sxemasiga u tegmaydi.
export async function ensureAnalyticsTable(payload: Payload) {
  await poolOf(payload).query(`
    CREATE SCHEMA IF NOT EXISTS analytics;
    CREATE TABLE IF NOT EXISTS analytics.events (
      id bigserial PRIMARY KEY,
      ts timestamptz NOT NULL DEFAULT now(),
      visitor text NOT NULL,
      kind text NOT NULL,
      path text,
      lang text,
      referrer text,
      device text,
      country text,
      name text,
      value text
    );
    CREATE INDEX IF NOT EXISTS events_ts ON analytics.events (ts);
    CREATE INDEX IF NOT EXISTS events_kind_ts ON analytics.events (kind, ts);
  `)
}

function visitorOf(req: PayloadRequest) {
  const day = new Date(Date.now() + 5 * 3600 * 1000).toISOString().slice(0, 10)
  const salt = createHash('sha256').update(`${process.env.PAYLOAD_SECRET ?? ''}:${day}`).digest('hex')
  return createHash('sha256').update(`${salt}:${clientIp(req)}:${req.headers.get('user-agent') ?? ''}`).digest('hex').slice(0, 24)
}

const clip = (v: unknown, n: number) => (typeof v === 'string' && v.trim() ? v.trim().slice(0, n) : null)

/** Bitta yozuv: kind = pageview | event | search */
export async function recordHit(req: PayloadRequest, hit: { kind: string; path?: unknown; lang?: unknown; referrer?: unknown; name?: unknown; value?: unknown }) {
  const ua = req.headers.get('user-agent') ?? ''
  if (!ua || BOTS.test(ua)) return
  let referrer: string | null = null
  try {
    const r = clip(hit.referrer, 500)
    if (r) referrer = new URL(r).hostname.replace(/^www\./, '')
  }
  catch {
    // noto'g'ri manzil — manbasiz
  }
  // Mamlakat: Cloudflare yoki nginx GeoIP sarlavhasi bo'lsa (IP'dan o'zimiz aniqlamaymiz)
  const country = clip(req.headers.get('cf-ipcountry') ?? req.headers.get('x-country-code'), 2)?.toUpperCase() ?? null
  await poolOf(req.payload).query(
    'INSERT INTO analytics.events (visitor, kind, path, lang, referrer, device, country, name, value) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)',
    [visitorOf(req), hit.kind, clip(hit.path, 300), clip(hit.lang, 5), referrer, parseUserAgent(ua).device ?? null, country === 'XX' ? null : country, clip(hit.name, 80), clip(hit.value, 200)],
  )
}

type Range = '1' | '7' | '30' | '365'

const SOURCES: [RegExp, string][] = [
  [/(^|\.)google\./, 'Google'], [/(^|\.)yandex\./, 'Yandex'], [/(^|\.)bing\.com$/, 'Bing'],
  [/(^|\.)t\.me$|telegram/, 'Telegram'], [/facebook\.com$|fb\.com$/, 'Facebook'], [/instagram\.com$/, 'Instagram'],
  [/youtube\.com$/, 'YouTube'], [/uzswlu\.uz$|localhost/, 'Sayt içidan'],
]

/** Statistika sahifasi uchun barcha raqamlar */
export async function statsFor(payload: Payload, range: Range) {
  const pool = poolOf(payload)
  const now = new Date()
  const ms = { '1': 86400e3, '7': 7 * 86400e3, '30': 30 * 86400e3, '365': 365 * 86400e3 }[range]
  const from = new Date(now.getTime() - ms)
  const prev = new Date(from.getTime() - ms)

  const summary = async (a: Date, b: Date) => (await pool.query(`
    WITH ev AS (SELECT visitor, ts FROM analytics.events WHERE kind = 'pageview' AND ts >= $1 AND ts < $2),
    s AS (SELECT visitor, ts, CASE WHEN lag(ts) OVER w IS NULL OR ts - lag(ts) OVER w > interval '30 minutes' THEN 1 ELSE 0 END AS fresh FROM ev WINDOW w AS (PARTITION BY visitor ORDER BY ts)),
    v AS (SELECT visitor, ts, sum(fresh) OVER (PARTITION BY visitor ORDER BY ts) AS n FROM s),
    visits AS (SELECT count(*) AS views, extract(epoch FROM max(ts) - min(ts)) AS dur FROM v GROUP BY visitor, n)
    SELECT (SELECT count(DISTINCT visitor) FROM ev)::int AS visitors, count(*)::int AS visits, coalesce(sum(views), 0)::int AS pageviews,
           coalesce(avg(dur), 0)::float AS duration, coalesce(avg(CASE WHEN views = 1 THEN 1 ELSE 0 END), 0)::float AS bounce
    FROM visits`, [a, b])).rows[0]

  const unit = range === '1' ? 'hour' : range === '365' ? 'month' : 'day'
  const [cur, before, series, refs, countries, langs, pages, searches, events] = await Promise.all([
    summary(from, now),
    summary(prev, from),
    pool.query(`SELECT date_trunc('${unit}', ts AT TIME ZONE 'Asia/Tashkent') AS t, count(*)::int AS views, count(DISTINCT visitor)::int AS visitors
                FROM analytics.events WHERE kind = 'pageview' AND ts >= $1 GROUP BY 1 ORDER BY 1`, [from]),
    pool.query(`SELECT coalesce(referrer, '') AS k, count(DISTINCT visitor)::int AS v FROM analytics.events WHERE kind = 'pageview' AND ts >= $1 GROUP BY 1 ORDER BY 2 DESC LIMIT 50`, [from]),
    pool.query(`SELECT country AS k, count(DISTINCT visitor)::int AS v FROM analytics.events WHERE kind = 'pageview' AND ts >= $1 AND country IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 6`, [from]),
    pool.query(`SELECT coalesce(lang, 'uz') AS k, count(*)::int AS v FROM analytics.events WHERE kind = 'pageview' AND ts >= $1 GROUP BY 1 ORDER BY 2 DESC`, [from]),
    pool.query(`SELECT path AS k, count(*)::int AS v FROM analytics.events WHERE kind = 'pageview' AND ts >= $1 AND path IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 8`, [from]),
    pool.query(`SELECT lower(value) AS k, count(*)::int AS v FROM analytics.events WHERE kind = 'search' AND ts >= $1 AND value IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 8`, [from]),
    pool.query(`SELECT name AS k, count(*)::int AS v FROM analytics.events WHERE kind = 'event' AND ts >= $1 GROUP BY 1 ORDER BY 2 DESC LIMIT 8`, [from]),
  ])

  // Manbalar: domenlar guruhlanadi (Google, Telegram …), bo'sh — to'g'ridan-to'g'ri
  const sources = new Map<string, number>()
  for (const r of refs.rows as { k: string; v: number }[]) {
    const name = !r.k ? 'Töğridan-töğri' : SOURCES.find(([re]) => re.test(r.k))?.[1] ?? r.k
    sources.set(name, (sources.get(name) ?? 0) + r.v)
  }
  const top = [...sources.entries()].sort((a, b) => b[1] - a[1])
  const rest = top.slice(5).reduce((s, [, v]) => s + v, 0)

  return {
    range,
    from: from.toISOString(),
    current: cur,
    previous: before,
    unit,
    series: series.rows.map((r: { t: Date; views: number; visitors: number }) => ({ t: new Date(r.t).toISOString(), views: r.views, visitors: r.visitors })),
    sources: [...top.slice(0, 5), ...(rest ? [['Boşqa', rest] as [string, number]] : [])].map(([k, v]) => ({ k, v })),
    countries: countries.rows,
    langs: langs.rows,
    pages: pages.rows,
    searches: searches.rows,
    events: events.rows,
  }
}
