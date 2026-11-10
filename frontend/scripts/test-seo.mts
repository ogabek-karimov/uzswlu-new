// SEO yordamchilarini sinash: npm run test:seo (Node 22.6+)
import assert from 'node:assert/strict'
import { formatExtensions } from '../shared/utils/phone.ts'
import { absoluteUrl, buildRobotsTxt, buildSitemapXml, menuPaths, prefixedPath } from '../shared/utils/seo.ts'

// prefixedPath: o'zbekcha prefikssiz, boshqalar /ru /en /zh
assert.equal(prefixedPath('uz', '/'), '/')
assert.equal(prefixedPath('ru', '/'), '/ru')
assert.equal(prefixedPath('uz', '/news/x'), '/news/x')
assert.equal(prefixedPath('en', '/news/x/'), '/en/news/x')

// absoluteUrl: nisbiy → to'liq; to'liq o'zgarmaydi; domen oxiridagi / hisobga olinmaydi
assert.equal(absoluteUrl('https://uzswlu.uz', '/og-default.jpg'), 'https://uzswlu.uz/og-default.jpg')
assert.equal(absoluteUrl('https://uzswlu.uz/', '/media/a.webp'), 'https://uzswlu.uz/media/a.webp')
assert.equal(absoluteUrl('https://uzswlu.uz', 'https://cdn.example.com/a.jpg'), 'https://cdn.example.com/a.jpg')
assert.ok(!absoluteUrl('https://uzswlu.uz', '/x').includes('localhost'))

// sitemap: takrorlar bir marta, & va < belgilari ekranlanadi, noto'g'ri sana tashlanadi
const xml = buildSitemapXml([
  { loc: 'https://uzswlu.uz/' },
  { loc: 'https://uzswlu.uz/' },
  { loc: 'https://uzswlu.uz/news/a?x=1&y=2', lastmod: '2026-10-20T10:00:00+05:00' },
  { loc: 'https://uzswlu.uz/news/b', lastmod: 'kecha' },
])
assert.equal(xml.match(/<url>/g)?.length, 3)
assert.ok(xml.includes('a?x=1&amp;y=2'))
assert.ok(xml.includes('<lastmod>2026-10-20</lastmod>'))
assert.ok(!xml.includes('kecha'))
assert.ok(xml.startsWith('<?xml') && xml.includes('http://www.sitemaps.org/schemas/sitemap/0.9'))
assert.equal(buildSitemapXml(Array.from({ length: 50_005 }, (_, i) => ({ loc: `https://x/${i}` }))).match(/<url>/g)?.length, 50_000)

// robots.txt: sitemap manzili, yopiq yo'llar barcha tillarda
const robots = buildRobotsTxt('https://uzswlu.uz/')
assert.ok(robots.includes('Sitemap: https://uzswlu.uz/sitemap.xml'))
for (const p of ['/api/', '/dashboard', '/ru/dashboard', '/zh/search']) assert.ok(robots.includes(`Disallow: ${p}\n`), p)
assert.ok(robots.includes('Allow: /\n'))
assert.ok(!robots.includes('Disallow: \n'), 'hammasiga ruxsat degan bo‘sh Disallow qolmasin')

// menyu yo'llari: ichki sahifalar; tashqi, fayl va #anchor/?query tozalanadi
const paths = menuPaths([
  { url: '/yangiliklar', links: [] },
  { overview: '/brm', links: [{ url: '/stipendiyalar#x' }, { url: 'https://example.com/a' }, { url: '/files/doc.pdf' }, { url: '//evil.com' }, { url: '/staff?q=1' }] },
])
assert.deepEqual(paths, ['/yangiliklar', '/brm', '/stipendiyalar', '/staff'])

// ichki raqamlar: diapazon to'liq yoyiladi (1061–1064 → 4 ta raqam)
assert.equal(formatExtensions('1061–1064'), '1061, 1062, 1063, 1064')
assert.equal(formatExtensions('1061-1064'), '1061, 1062, 1063, 1064')
assert.equal(formatExtensions('1061, 1062, 1063, 1064'), '1061, 1062, 1063, 1064')
assert.equal(formatExtensions('1061–1062, 2000'), '1061, 1062, 2000')
assert.equal(formatExtensions('1–99999'), '1–99999')
assert.equal(formatExtensions(''), '')
assert.equal(formatExtensions(null), '')

console.log('seo: OK')
