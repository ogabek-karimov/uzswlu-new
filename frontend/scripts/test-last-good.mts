// Backend o‘chganda eski javob berish qatlamini sinash: npm run test:last-good (Node 22.6+)
import { createLastGood, isBackendFailure } from '../server/utils/last-good.ts'
import assert from 'node:assert/strict'
let t = 0
const mk = (o = {}) => createLastGood({ maxStaleMs: 3 * 3600e3, cooldownMs: 15e3, maxEntries: 3, now: () => t, ...o })
const err = (status?: number) => Object.assign(new Error('x'), status === undefined ? {} : { status })
let calls = 0
const ok = (v: string) => async () => { calls++; return v }
const bad = (s?: number) => async () => { calls++; throw err(s) }

// 1. oddiy: muvaffaqiyat saqlanadi, backend yiqilsa eskisi qaytadi
let lg = mk()
assert.deepEqual(await lg.run('a', ok('v1')), { value: 'v1' })
t += 60e3
let r = await lg.run('a', bad(503))
assert.equal(r.value, 'v1'); assert.equal(r.staleAgeMs, 60e3)

// 2. cooldown: backendga bormaydi
calls = 0; t += 5e3
r = await lg.run('a', bad(503)); assert.equal(calls, 0); assert.equal(r.value, 'v1')
// cooldown tugagach — bitta tekshiruv, yana yiqilsa eskisi
t += 20e3; r = await lg.run('a', bad()); assert.equal(calls, 1); assert.equal(r.value, 'v1')

// 3. backend tiklandi — yangi javob
t += 20e3; r = await lg.run('a', ok('v2')); assert.deepEqual(r, { value: 'v2' })
r = await lg.run('a', bad(500)); assert.equal(r.value, 'v2')

// 4. 3 soatdan keyin eski javob yaroqsiz — xato uzatiladi
t += 3 * 3600e3 + 1
await assert.rejects(lg.run('a', bad(502)), (e: any) => e.status === 502)

// 5. 3 soat ichida hali yaroqli
lg = mk(); await lg.run('b', ok('x')); t += 3 * 3600e3 - 1
assert.equal((await lg.run('b', bad(504))).value, 'x')

// 6. 4xx haqiqiy javob: eski nusxa berilmaydi, cooldown ham boshlanmaydi
lg = mk(); await lg.run('c', ok('x'))
await assert.rejects(lg.run('c', bad(404)), (e: any) => e.status === 404)
calls = 0; assert.deepEqual(await lg.run('c', ok('y')), { value: 'y' }); assert.equal(calls, 1)

// 7. keep=false: saqlanmaydi, eskisi ishlatilmaydi
lg = mk(); await lg.run('s', ok('x'), false); assert.equal(lg.size, 0)
await assert.rejects(lg.run('s', bad(503), false))

// 8. eski nusxa yo'q kalit — xato o'tadi
lg = mk(); await assert.rejects(lg.run('new', bad(503)))

// 9. LRU chegarasi
lg = mk({ maxEntries: 3 }); for (const k of ['1', '2', '3', '4']) await lg.run(k, ok(k))
assert.equal(lg.size, 3)
await assert.rejects(lg.run('1', bad(503)))      // eng eskisi chiqarilgan
assert.equal((await lg.run('4', bad(503))).value, '4')

// 10. onWarn cooldown ichida bir marta
lg = mk(); await lg.run('w', ok('x')); let warns = 0
await lg.run('w', bad(503), true, () => warns++); await lg.run('w', bad(503), true, () => warns++)
assert.equal(warns, 1)

// 11. xato turlari
assert.equal(isBackendFailure(err()), true)
assert.equal(isBackendFailure(err(0)), true)
assert.equal(isBackendFailure(err(500)), true)
assert.equal(isBackendFailure(err(429)), true)
assert.equal(isBackendFailure(err(404)), false)
assert.equal(isBackendFailure(err(401)), false)
assert.equal(isBackendFailure({ response: { status: 503 } }), true)
console.log('HAMMASI O‘TDI')
