// Admin API qatlamini sinash: npm test (Node 22.6+). fetch soxtalashtiriladi — brauzer/backend kerak emas.
import assert from 'node:assert/strict'
import { ApiError, api, httpMessage, qs, setUnauthorizedHandler, TIMEOUT_MS } from '../src/lib/api.ts'
import { onSessionExpired } from '../src/lib/session-policy.ts'
import { detectPostDate, findDate } from '../src/lib/textdate.ts'
import { onToast, savedMessage } from '../src/lib/toast.ts'

const realFetch = globalThis.fetch
const reply = (status: number, body: string, type = 'application/json') => async () => new Response(status === 204 ? null : body, { status, headers: { 'content-type': type } })
const use = (fn: typeof fetch) => { globalThis.fetch = fn as typeof fetch }
const fails = async (p: Promise<unknown>) => { try { await p } catch (e) { return e as ApiError } throw new Error('xato kutilgan edi') }

// 1. oddiy muvaffaqiyat va bo'sh javob (204)
use(reply(200, '{"a":1}'))
assert.deepEqual(await api.get('/x'), { a: 1 })
use(reply(204, ''))
assert.equal(await api.del('/x'), null)

// 2. server xabari ustun: {errors:[{message}]} va {message}
use(reply(400, '{"errors":[{"message":"Sarlavha majburiy"}]}'))
assert.equal((await fails(api.post('/x', {}))).message, 'Sarlavha majburiy')
use(reply(409, '{"message":"Band"}'))
assert.equal((await fails(api.post('/x', {}))).message, 'Band')

// 3. nginx HTML xato sahifasi: «Unexpected token <» emas, tushunarli xabar
for (const status of [502, 503, 504]) {
  use(reply(status, '<html><body><h1>Bad Gateway</h1></body></html>', 'text/html'))
  const e = await fails(api.get('/x'))
  assert.equal(e.status, status)
  assert.match(e.message, /vaqtincha javob bermayapti/)
  assert.ok(!/Unexpected|<html/.test(e.message))
}
use(reply(500, 'Internal Server Error', 'text/plain'))
assert.match((await fails(api.get('/x'))).message, /Serverda xatolik \(500\)/)
use(reply(413, '<html>Request Entity Too Large</html>', 'text/html'))
assert.match((await fails(api.post('/x', {}))).message, /hajmi juda katta/)

// 4. 200, lekin JSON emas (proksi HTML qaytardi) — tushunarli xato
use(reply(200, '<html>login</html>', 'text/html'))
assert.match((await fails(api.get('/x'))).message, /kutilmagan javob/)

// 5. tarmoq uzilishi
use(async () => { throw new TypeError('Failed to fetch') })
const net = await fails(api.get('/x'))
assert.equal(net.status, 0); assert.match(net.message, /aloqa yo‘q/)

// 6. timeout: javob kelmasa abort qilinadi (tez sinash uchun sozlamani qisqartiramiz)
TIMEOUT_MS.default = 30
use(((_url: string, init?: RequestInit) => new Promise((_, reject) => {
  init?.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })))
})) as unknown as typeof fetch)
const t0 = Date.now()
const slow = await fails(api.get('/x'))
assert.equal(slow.status, 0); assert.match(slow.message, /vaqt tugadi/)
assert.ok(Date.now() - t0 < 2000)

// 7. 401: himoyalangan so'rovda handler chaqiriladi; login/2FA/me da — chaqirilmaydi
let calls = 0
setUnauthorizedHandler(() => { calls++ })
use(reply(401, '{"message":"Unauthorized"}'))
await fails(api.get('/posts'))
assert.equal(calls, 1)
for (const path of ['/users/login', '/users/login/2fa', '/users/me', '/users/logout']) await fails(api.post(path, {}))
assert.equal(calls, 1, 'login/me 401 sessiya tugadi emas')
// 401 + JSON xabar: LoginPage 2FA «Vaqt tugadi» matniga tayanadi — server xabari saqlanadi
use(reply(401, '{"message":"Vaqt tugadi"}'))
assert.equal((await fails(api.post('/users/login/2fa', {}))).message, 'Vaqt tugadi')
setUnauthorizedHandler(null)
await fails(api.get('/posts')) // handler yo'q — yiqilmaydi

// 8. httpMessage va qs
assert.match(httpMessage(429), /Juda ko‘p so‘rov/)
assert.equal(httpMessage(418), 'Xato (418)')
assert.equal(qs({ a: 1, b: '', c: undefined, w: { x: { equals: 'y' } } }), 'a=1&w%5Bx%5D%5Bequals%5D=y')

// 9. sessiya qarori: yozayotgan foydalanuvchi sahifasi saqlanadi, bo'sh sahifa yo'naltiriladi
const base = { loggedIn: true, expired: false, unsaved: 0, touched: false }
assert.equal(onSessionExpired(base), 'redirect')
assert.equal(onSessionExpired({ ...base, touched: true }), 'modal')
assert.equal(onSessionExpired({ ...base, unsaved: 1 }), 'modal')
assert.equal(onSessionExpired({ ...base, expired: true }), 'ignore')
assert.equal(onSessionExpired({ ...base, loggedIn: false }), 'ignore')

// 10. «Saqlandi» bildirişi: saqlaş/naşr/öçirişda çiqadi, kiriş, 2FA va GET da — yöq; xato javobda — yöq
assert.equal(savedMessage('GET', '/posts'), null)
assert.equal(savedMessage('POST', '/users/login', {}), null)
assert.equal(savedMessage('POST', '/users/2fa/enable', {}), null)
assert.equal(savedMessage('POST', '/panel/notifications', {}), null)
assert.equal(savedMessage('PATCH', '/pages/5', { title: {} })?.text, 'Saqlandi')
assert.equal(savedMessage('PATCH', '/posts/5', { status: 'published' })?.text, 'Naşr qilindi')
assert.equal(savedMessage('POST', '/posts', { status: 'draft' })?.text, 'Qoralama saqlandi')
assert.deepEqual(savedMessage('DELETE', '/pages/5'), { text: 'Öçirildi', kind: 'delete' })
assert.equal(savedMessage('POST', '/media', new FormData())?.text, 'Fayl yuklandi')
const seen: string[] = []
const stop = onToast(t => seen.push(t.text))
use(reply(200, '{"doc":{}}'))
await api.patch('/pages/1', { title: {} })
await api.get('/pages')
use(reply(400, '{"message":"Xato"}'))
await fails(api.patch('/pages/1', {}))
stop()
assert.deepEqual(seen, ['Saqlandi'])

// 11. Matndan sana (nashr vaqti): har xil til va yozuv; yetishmagan yil/vaqt taxmin qilinadi
const NOW = new Date('2026-11-25T10:00:00+05:00')
const on = (text: string) => { const r = findDate(text, NOW); return r && `${r.date} ${r.time} ${r.guessed.join(',')}` }
assert.equal(on('2026-yil 20-oktabr kuni soat 14:30 da anjuman bo‘lib o‘tdi'), '2026-10-20 14:30 ')
assert.equal(on('Universitetda 5-noyabr kuni tadbir bo‘ldi'), '2026-11-05 09:00 year,time')
assert.equal(on('Kecha, 28-dekabr kuni…'), '2025-12-28 09:00 year,time') // yil yöq, kelajakka tuşadi → ötgan yil
assert.equal(on('Ötgan yili 2025 йил 3 сентябр куни соат 10:00 да'), '2025-09-03 10:00 ')
assert.equal(on('20 октября 2026 г. в 11:00 состоялась конференция'), '2026-10-20 11:00 ')
assert.equal(on('On October 7, 2026 the university hosted…'), '2026-10-07 09:00 time')
assert.equal(on('The forum was held on 3rd of March 2025.'), '2025-03-03 09:00 time')
assert.equal(on('2026年10月20日，我校举办了会议'), '2026-10-20 09:00 time')
assert.equal(on('Sana: 12.09.2026, soat 16:00'), '2026-09-12 16:00 ')
assert.equal(on('Hujjat 2026-04-01 da tasdiqlangan'), '2026-04-01 09:00 time')
assert.equal(on('oktabrning 15-kuni seminar'), '2026-10-15 09:00 year,time')
assert.equal(on('Sentyabr 2026 da qabul yakunlandi'), '2026-09-01 09:00 day,time')
assert.equal(on('Hech qanday sana yöq, faqat 2.5 ming talaba'), null)
assert.equal(on('31-fevral 2026'), null) // mavjud emas
assert.equal(findDate('20-oktabr 2026', NOW)?.snippet, '20-oktabr 2026')
assert.equal(findDate('20-oktabr 2026 soat 10:00', NOW)?.iso, '2026-10-20T05:00:00.000Z') // Toshkent → UTC
// Post: özbekça böş bölsa — boşqa tildan; HTML teglari xalaqit bermaydi
const det = detectPostDate({ title: { uz: 'Anjuman' }, body: { uz: '<p>Matn</p>', ru: '<p><b>15</b> мая 2026 года</p>' } }, NOW)
assert.equal(det?.lang, 'ru')
assert.equal(det?.date, '2026-05-15')
assert.equal(detectPostDate({ title: { uz: 'Sanasiz' } }, NOW), null)

globalThis.fetch = realFetch
console.log('admin api: OK')
