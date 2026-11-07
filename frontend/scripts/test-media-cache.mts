// Media keshi mantig‘ini sinash: npm run test:last-good
import { rewriteMediaUrls, safeMediaPath, createByteCache } from '../server/utils/media-cache.ts'
import assert from 'node:assert/strict'
const O = ['http://localhost:8000', 'http://backend:8000']
assert.equal(rewriteMediaUrls('http://localhost:8000/media/a/b.jpg', O), '/media/a/b.jpg')
assert.deepEqual(rewriteMediaUrls({ x: [{ image: 'http://backend:8000/media/p.png', t: 'salom' }], n: 3, z: null }, O), { x: [{ image: '/media/p.png', t: 'salom' }], n: 3, z: null })
assert.equal(rewriteMediaUrls('<p><img src="http://localhost:8000/media/i.jpg"> matn</p>', O), '<p><img src="/media/i.jpg"> matn</p>')
assert.equal(rewriteMediaUrls('http://localhost:8000/api/documents/1/file', O), 'http://localhost:8000/api/documents/1/file') // media emas — tegilmaydi
assert.equal(rewriteMediaUrls('http://evil.com/media/a.jpg', O), 'http://evil.com/media/a.jpg')
assert.equal(rewriteMediaUrls('http://localhost:8000/media/a.jpg', []), 'http://localhost:8000/media/a.jpg')
assert.equal(safeMediaPath('a/b.jpg'), 'a/b.jpg')
assert.equal(safeMediaPath('a%20b/c d.jpg'), 'a%20b/c%20d.jpg')
for (const bad of ['../etc/passwd', 'a/../b', '%2e%2e/x', 'a//b', '/abs', 'a\\b', 'a%00b', '', undefined, 'x'.repeat(301), '%E0%A4%A']) assert.equal(safeMediaPath(bad as any), null, String(bad))
const c = createByteCache(10)
c.set('a', { body: new Uint8Array(4), type: 't' }); c.set('b', { body: new Uint8Array(4), type: 't' })
c.get('a'); c.set('c', { body: new Uint8Array(4), type: 't' })
assert.equal(c.get('b'), undefined); assert.ok(c.get('a')); assert.ok(c.get('c')); assert.equal(c.bytes, 8)
c.set('big', { body: new Uint8Array(11), type: 't' }); assert.equal(c.get('big'), undefined)
console.log('MEDIA HAMMASI O‘TDI')
