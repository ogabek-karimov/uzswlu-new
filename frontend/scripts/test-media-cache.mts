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

import { safeMediaHeaders } from '../server/utils/media-cache.ts'
const h1 = safeMediaHeaders('image/webp', '/media/a/b.webp')
assert.equal(h1['content-type'], 'image/webp'); assert.equal(h1['x-content-type-options'], 'nosniff'); assert.match(h1['content-security-policy']!, /sandbox/)
const h2 = safeMediaHeaders('application/pdf', '/media/x.pdf')
assert.equal(h2['content-type'], 'application/pdf'); assert.equal(h2['content-security-policy'], undefined)
for (const evil of ['text/html', 'image/svg+xml', 'application/xhtml+xml', 'text/javascript', '', undefined, 'text/html; charset=utf-8']) {
  const h = safeMediaHeaders(evil as string, '/media/we ird"na%me.html')
  assert.equal(h['content-type'], 'application/octet-stream', String(evil))
  assert.match(h['content-disposition']!, /^attachment; filename="[\w.\-]+"$/)
}
assert.equal(safeMediaHeaders('image/PNG; charset=x', '/media/a.png')['content-type'], 'image/png')
safeMediaHeaders('text/html', '/media/%E0%A4%A.html') // noto'g'ri %-kodlash xato bermaydi
console.log('MEDIA HEADERS O‘TDI')
