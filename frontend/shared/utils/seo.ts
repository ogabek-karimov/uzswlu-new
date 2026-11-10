// SEO uchun sof (Nuxt/Nitro'siz) yordamchilar: sitemap.xml, robots.txt, havola yasash.
// server/routes/sitemap.xml.ts, robots.txt.ts va app/composables/useSeo.ts shundan foydalanadi;
// scripts/test-seo.mts to'g'ridan-to'g'ri sinaydi.

/** Til prefiksi bilan yo'l: o'zbekcha — prefikssiz (`prefix_except_default`) */
export function prefixedPath(lang: string, path: string): string {
  const clean = path === '/' ? '' : path.replace(/\/+$/, '')
  return lang === 'uz' ? (clean || '/') : `/${lang}${clean}`
}

/** Yo'l yoki nisbiy havolani to'liq URL'ga aylantiradi (og:image, canonical absolyut bo'lishi shart) */
export function absoluteUrl(origin: string, value: string): string {
  try { return new URL(value, `${origin.replace(/\/+$/, '')}/`).href }
  catch { return `${origin}${value.startsWith('/') ? '' : '/'}${value}` }
}

const escXml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

export interface SitemapEntry { loc: string; lastmod?: string }

/** sitemap.xml matni; takroriy `loc` bir marta chiqadi. Protokol chegarasi: 50 000 ta manzil */
export function buildSitemapXml(entries: SitemapEntry[]): string {
  const seen = new Set<string>()
  const rows: string[] = []
  for (const e of entries) {
    if (seen.has(e.loc) || rows.length >= 50_000) continue
    seen.add(e.loc)
    const lastmod = e.lastmod && /^\d{4}-\d{2}-\d{2}/.test(e.lastmod) ? `<lastmod>${e.lastmod.slice(0, 10)}</lastmod>` : ''
    rows.push(`<url><loc>${escXml(e.loc)}</loc>${lastmod}</url>`)
  }
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rows.join('\n')}\n</urlset>\n`
}

/** robots.txt: ochiq sahifalar ruxsat; shaxsiy va texnik yo'llar (barcha tillarda) yopiq; sitemap manzili */
export function buildRobotsTxt(origin: string, locales: readonly string[] = ['uz', 'ru', 'en', 'zh']): string {
  const hidden = ['/api/', ...['dashboard', 'search'].flatMap(p => locales.map(l => prefixedPath(l, `/${p}`)))]
  return ['User-agent: *', 'Allow: /', ...hidden.map(p => `Disallow: ${p}`), '', `Sitemap: ${origin.replace(/\/+$/, '')}/sitemap.xml`, ''].join('\n')
}

interface MenuLike { url?: string | null; overview?: string | null; links: { url: string }[] }

/** Menyudagi ichki (`/…`) sahifa yo'llari: tashqi havola, fayl va `#`/`?` qismlarsiz */
export function menuPaths(menu: MenuLike[]): string[] {
  const out: string[] = []
  for (const g of menu) {
    for (const url of [g.url, g.overview, ...g.links.map(l => l.url)]) {
      if (url && url.startsWith('/') && !url.startsWith('//') && !/\.[a-z0-9]{2,5}$/i.test(url)) out.push(url.split('#')[0]!.split('?')[0]!)
    }
  }
  return out
}
