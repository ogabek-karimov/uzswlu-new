# Loyiha qoidalari (Claude va dasturchilar uchun)

Foydalanuvchi bilan **o‘zbekcha** gaplashing.

## Git
- Faqat `azik` filialiga push qiling (`git push origin HEAD:azik`). `main` ga tegmang; `azik → main` faqat foydalanuvchi so‘rasa.
- Commit xabari oxirida: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` va `Claude-Session: <sessiya havolasi>`.

## Har o‘zgarishdan keyin (majburiy)
1. **`docs/13-yangiliklar.md` ga yozuv qo‘shing** (bugungi sana ostida, toifa + qisqa matn + commit). Yangi kun bo‘lsa — yangi `## YYYY-MM-DD` sarlavha tepaga.
2. Qo‘llanma bo‘limi o‘zgargan bo‘lsa (`docs/01…12`) — uni ham yangilang; kodga bog‘liq qismlar uchun: `cd backend && python manage.py build_docs`.
3. Testlar: `cd backend && python manage.py test`; frontend/admin: `npm test`.
4. Commit → `git push origin HEAD:azik` → `git ls-remote origin azik` bilan push borligini tekshiring → CI natijasini kuzating (`gh run list --branch azik`).
5. Foydalanuvchiga hisobotda: nima o‘zgardi, push qilindimi (commit raqami), CI holati.
