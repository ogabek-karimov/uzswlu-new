// Sahifalar va tarjimalar bo'yicha statik tekshiruv: npm run test:pages (Node 22.6+)
// Brauzer/Nuxt kerak emas: manba fayllarni o'qib, qoidalar buzilmaganini tekshiradi.
import assert from 'node:assert/strict'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const walk = (dir: string): string[] => readdirSync(dir).flatMap(n => (statSync(join(dir, n)).isDirectory() ? walk(join(dir, n)) : [join(dir, n)]))
const rel = (f: string) => relative(root, f)
const vue = walk(join(root, 'app')).filter(f => f.endsWith('.vue'))
let failed = 0
const check = (name: string, problems: string[]) => {
  if (problems.length) { failed++; console.error(`✗ ${name}\n  ${problems.join('\n  ')}`) }
  else console.log(`✓ ${name}`)
}

// 1. Har bir sahifa useSeo() chaqiradi (title/description/preview) — yoki uni chaqiradigan komponentni ko'rsatadi / boshqa sahifaga yo'naltiradi.
//    Bosh sahifa umumiy qiymatdan foydalanadi
const NO_SEO = new Set(['app/pages/index.vue'])
check('har sahifada useSeo()', vue.filter(f => rel(f).startsWith('app/pages/') && !NO_SEO.has(rel(f)) && !/useSeo\(|<PostArticle|<ProgramsView|navigateTo\(/.test(readFileSync(f, 'utf8'))).map(rel))

// 2. Yopiq sahifalar (kabinet, qidiruv) indekslanmaydi
check('dashboard/search noindex', ['dashboard', 'search'].filter(n => !/noindex:\s*true/.test(readFileSync(join(root, `app/pages/${n}.vue`), 'utf8'))))

// 3. Har bir <img> da alt bor (bo'sh alt — bezak rasmi uchun ruxsat)
const noAlt: string[] = []
const noLoading: string[] = []
const EAGER_OK = new Set(['BrandMark.vue', 'ImageViewer.vue', 'rektorat.vue', '[slug].vue', 'PostArticle.vue', 'Carousel.vue', 'Avatar.vue'])
for (const f of vue) {
  for (const m of readFileSync(f, 'utf8').matchAll(/<img\b[^>]*>/gs)) {
    const tag = m[0]
    if (!/(^|\s):?alt=/.test(tag)) noAlt.push(rel(f))
    if (!/loading=/.test(tag) && !EAGER_OK.has(f.split('/').pop()!)) noLoading.push(rel(f))
  }
}
check('<img alt> bor', noAlt)
check('<img loading> bor (ekranning yuqori qismidagilardan tashqari)', noLoading)

// 4. Domen kodga qattiq yozilmagan: canonical/sitemap muhitdan olinadi
const config = readFileSync(join(root, 'nuxt.config.ts'), 'utf8')
check('siteUrl bo‘sh yoki muhitdan', /siteUrl:\s*''/.test(config) ? [] : ['nuxt.config.ts: public.siteUrl standart qiymati bo‘sh bo‘lishi kerak'])
check('i18n.baseUrl muhitdan', /baseUrl:\s*process\.env\.NUXT_PUBLIC_SITE_URL/.test(config) ? [] : ['i18n.baseUrl NUXT_PUBLIC_SITE_URL dan olinsin'])

// 5. Tarjima kalitlari 4 tilda bir xil (yetishmaydigan kalit sahifada xom kalit bo'lib chiqadi)
const keys = (o: unknown, p = ''): string[] => (o && typeof o === 'object' && !Array.isArray(o)
  ? Object.entries(o).flatMap(([k, v]) => keys(v, p ? `${p}.${k}` : k))
  : [p])
const locales = Object.fromEntries(['uz', 'ru', 'en', 'zh'].map(l => [l, new Set(keys(JSON.parse(readFileSync(join(root, `i18n/locales/${l}.json`), 'utf8'))))]))
const missing: string[] = []
for (const [l, set] of Object.entries(locales)) {
  for (const k of locales.uz!) if (!set.has(k)) missing.push(`${l}: ${k}`)
}
check('tarjima kalitlari uz bilan teng', missing.slice(0, 30))

// 5a. Bosiladigan elementlarda «qo'l» kursori: global qoida bor; qidiruv ikonkasi tugma (submit) ichida
const css = readFileSync(join(root, 'app/assets/css/main.css'), 'utf8')
check('main.css: button uchun cursor: pointer qoidasi', /button:not\(:disabled\)[\s\S]{0,400}cursor:\s*pointer/.test(css) ? [] : ['global cursor-pointer qoidasi yo‘q'])
const bareSearchIcons: string[] = []
for (const f of vue) {
  const text = readFileSync(f, 'utf8')
  for (const m of text.matchAll(/<form\b[^>]*role="search"[\s\S]*?<\/form>/g)) {
    for (const ic of m[0].matchAll(/<Icon name="lucide:search"[^>]*\/>/g)) {
      const before = m[0].slice(0, ic.index)
      if (!/<button[^>]*>\s*$/.test(before)) bareSearchIcons.push(`${rel(f)}: qidiruv ikonkasi tugma ichida emas`)
    }
  }
}
check('qidiruv formalarida ikonka — submit tugmasi', bareSearchIcons)

// 6. og-default.jpg mavjud (ijtimoiy tarmoq uchun standart rasm)
check('public/og-default.jpg', statSync(join(root, 'public/og-default.jpg'), { throwIfNoEntry: false })?.size ? [] : ['yo‘q'])

if (failed) { console.error(`\n${failed} ta tekshiruv yiqildi`); process.exit(1) }
console.log('\npages: OK')
