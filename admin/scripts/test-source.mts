// Admin manba kodi bo'yicha statik tekshiruv (lint o'rnini bosadi): npm test (Node 22.6+)
import assert from 'node:assert/strict'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const src = join(root, 'src')
const walk = (dir: string): string[] => readdirSync(dir).flatMap(n => (statSync(join(dir, n)).isDirectory() ? walk(join(dir, n)) : [join(dir, n)]))
const files = walk(src).filter(f => /\.(vue|ts)$/.test(f))
const rel = (f: string) => relative(root, f)
let failed = 0
const check = (name: string, problems: string[]) => {
  if (problems.length) { failed++; console.error(`✗ ${name}\n  ${problems.join('\n  ')}`) }
  else console.log(`✓ ${name}`)
}

const lines = (f: string) => readFileSync(f, 'utf8').split('\n').map((text, i) => ({ text, n: i + 1 }))
const grep = (re: RegExp) => files.flatMap(f => lines(f).filter(l => re.test(l.text)).map(l => `${rel(f)}:${l.n}`))

check('console.log/debugger yo‘q', grep(/\bconsole\.log\(|\bdebugger\b/))
check('`any` turi yo‘q', grep(/(:\s*any\b|\bas any\b|<any>)/))
check('TODO/FIXME qolmagan', grep(/\b(TODO|FIXME|XXX)\b/))

// Barcha marshrut komponentlari mavjud
const router = readFileSync(join(src, 'router.ts'), 'utf8')
check('router.ts dagi sahifa fayllari mavjud', [...router.matchAll(/import\('\.\/(pages\/[A-Za-z]+\.vue)'\)/g)].map(m => m[1]!).filter(p => !existsSync(join(src, p))))

// Har bir sahifa router'da ishlatiladi (yetim sahifa yo'q)
const used = new Set([...router.matchAll(/pages\/([A-Za-z]+)\.vue/g)].map(m => m[1]))
check('yetim sahifa yo‘q', readdirSync(join(src, 'pages')).map(f => f.replace('.vue', '')).filter(n => !used.has(n)))

// Har bir marshrutda sarlavha (document.title) bor; superOnly/roles faqat superadmin/editor/... qiymatlari
const ROLES = new Set(['superadmin', 'editor', 'faculty', 'pages', 'sdg'])
const bad: string[] = []
for (const m of router.matchAll(/\{ path: '([^']*)'[^\n]*\}/g)) {
  const line = m[0]
  if (/redirect:/.test(line) || /component: AdminLayout/.test(line)) continue
  if (!/meta: \{[^}]*title:/.test(line)) bad.push(`marshrut sarlavhasiz: ${m[1]}`)
  for (const r of line.match(/roles: \[([^\]]*)\]/)?.[1]?.matchAll(/'([a-z]+)'/g) ?? []) if (!ROLES.has(r[1]!)) bad.push(`noma'lum rol '${r[1]}' (${m[1]})`)
}
check('marshrutlar: sarlavha va rollar', bad)

// '@/…' importlari mavjud fayllarga ishora qiladi
const missing: string[] = []
for (const f of files) {
  for (const m of readFileSync(f, 'utf8').matchAll(/from '@\/([^']+)'/g)) {
    const p = m[1]!
    if (![p, `${p}.ts`, `${p}.vue`, `${p}/index.ts`].some(c => existsSync(join(src, c)))) missing.push(`${rel(f)} → @/${p}`)
  }
}
check('@/ importlari mavjud', missing)

// Katta sahifalar: 500 qatordan oshmasin (oshsa — bo'lish vaqti)
check('sahifa ≤ 500 qator', walk(join(src, 'pages')).filter(f => lines(f).length > 500).map(f => `${rel(f)} (${lines(f).length})`))

// Barcha so'rovlar lib/api.ts orqali (timeout, 401, xato xabari shu yerda) — to'g'ridan-to'g'ri fetch yo'q
check('fetch faqat lib/api.ts da', grep(/\bfetch\(/).filter(l => !l.startsWith('src/lib/api.ts')))

if (failed) { console.error(`\n${failed} ta tekshiruv yiqildi`); process.exit(1) }
console.log('\nadmin source: OK')
