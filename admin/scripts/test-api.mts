// Admin API qatlamini sinash: npm test (Node 22.6+). fetch soxtalashtiriladi — brauzer/backend kerak emas.
import assert from 'node:assert/strict'
import { ApiError, api, httpMessage, qs, setUnauthorizedHandler, TIMEOUT_MS } from '../src/lib/api.ts'
import { onSessionExpired } from '../src/lib/session-policy.ts'

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

globalThis.fetch = realFetch
console.log('admin api: OK')
