# 9. Sayt (frontend) va admin panel kodi

## Sayt — `frontend/` (Nuxt 4)

### Ishga tushirish

```bash
cd frontend && npx npm@11 install && npm run dev      # http://localhost:3000
npm run build                                          # production build (CI'da ham)
npm test                                               # server mantiqi + SEO + sahifa qoidalari
```

Docker'da `frontend` xizmati o‘zi `npm install && npm run dev` qiladi. Node versiyasi: Nuxt `4.4.8` ga qotirilgan (Node 22 uchun).

### Backend bilan ulanish (`frontend/.env`)

| O‘zgaruvchi | Nima |
|---|---|
| `NUXT_CMS_BASE` | backendning `/api/site` manzili (`http://localhost:8000/api/site`); Docker'da compose o‘zi `http://backend:8000/api/site` qo‘yadi |
| `NUXT_API_BASE`, `NUXT_API_TOKEN` | to‘liq API manzili va **`API_TOKEN`** (backend `.env` dagi bilan bir xil). `NUXT_API_BASE` bo‘sh bo‘lsa — mock ma’lumot |
| `NUXT_STALE_IF_ERROR_SECONDS` | backend o‘chsa oxirgi javob shuncha soniya ko‘rsatiladi (3 soat; `0` — o‘chirilgan) |
| `NUXT_BACKEND_COOLDOWN_SECONDS` | backend yiqilgandan keyin shuncha soniya unga bormaydi (15) |
| `NUXT_PUBLIC_SITE_URL` | **saytning ochiq manzili** (`https://uzswlu.uz`): canonical, hreflang, `sitemap.xml`, `robots.txt`, og:url shundan yasaladi. Productionda to‘ldiring; bo‘sh bo‘lsa so‘rov manzili olinadi (nginx `Host`/`X-Forwarded-Proto` uzatsin) |
| `NUXT_MEDIA_PUBLIC_ORIGIN` | backendning brauzerga ko‘rinadigan manzili (`PUBLIC_SERVER_URL`) — rasm havolalarini sayt `/media/…` iga almashtirish uchun |

Token **faqat Nuxt serverida** turadi (`runtimeConfig`), brauzerga chiqmaydi.

### Qayerda nima

Marshrutlar va server endpointlari to‘liq ro‘yxati: [reference → Frontend](reference.md). Qisqacha:

| Vazifa | Fayl |
|---|---|
| Yangi sahifa | `app/pages/<nom>.vue` (til prefiksi avtomatik). **`useSeo({ title, description, image })`** chaqiring — Telegram/Facebook preview va qidiruv uchun (`test:pages` tekshiradi) |
| SEO: canonical, hreflang, og:*, twitter | `app/composables/useSeo.ts` (umumiy qism `app.vue` da); standart rasm `public/og-default.jpg` (1200×630) |
| `sitemap.xml`, `robots.txt` | `server/routes/` + `shared/utils/seo.ts`; yangi sahifa turi qo‘shilsa `sitemap.xml.ts` dagi `FIXED` yoki menyuga qo‘shing |
| Menyu | `app/utils/navigation.ts` va backend `site` menyusi |
| Interfeys matni (4 til) | `i18n/locales/{uz,ru,en,zh}.json` — **to‘rttasiga ham** qo‘shing |
| Bosh sahifa bloklari | `app/components/home/` |
| Backend'dan ma’lumot oladigan endpoint | `server/api/<nom>.get.ts` → `server/utils/backend.ts` |
| Ma’lumot turlari | `shared/types/api.ts` (va `frontend/docs/openapi.yaml` — ikkalasi bir xil bo‘lsin) |
| Xodim kabineti | `app/components/cabinet/`, `server/api/me/` |

### Backend o‘chganda nima bo‘ladi

`server/utils/last-good.ts` — «oxirgi yaxshi javob»: backend yiqilsa sayt oxirgi muvaffaqiyatli GET javobini `NUXT_STALE_IF_ERROR_SECONDS` davomida ko‘rsatadi va yiqilgandan keyin `NUXT_BACKEND_COOLDOWN_SECONDS` davomida backendni urmaydi. Media (`/media/…`) sayt orqali keshlanib beriladi (`media-cache.ts`).

### API shartnomasi o‘zgarsa

`frontend/docs/openapi.yaml` — frontend va backend uchun **yagona shartnoma**. O‘zgartirsangiz: `shared/types/api.ts` ni moslang, backend nusxasini yangilang (`cp frontend/docs/openapi.yaml backend/apps/api/contract/openapi.yaml`) va `python manage.py test tests.api` ni ishga tushiring ([05-swagger](05-swagger.md)).

## Admin panel — `admin/` (Vue 3 + Vite)

### Ishga tushirish

```bash
cd admin && npm install && npm run dev      # http://localhost:5173
npm run typecheck                           # vue-tsc --noEmit
npm run build                               # typecheck + vite build (CI'da ham)
```

| O‘zgaruvchi | Nima |
|---|---|
| `BACKEND_URL` | Vite proksi manzili (standart `http://localhost:8000`; Docker'da `http://backend:8000`) |
| `ADMIN_PORT` | admin porti (standart 5173) |
| `VITE_MEDIA_BASE`, `VITE_SITE_URL` | brauzer rasmlar va saytni qayerdan ochishi |

`/api` so‘rovlari Vite orqali backendga yo‘naltiriladi (cookie bitta manzildan ishlashi uchun). Admin boshqa manzilda bo‘lsa, u backend `.env` dagi `TRUSTED_ORIGINS` da bo‘lishi **shart**.

### Qayerda nima

Sahifalar va ularni kim ko‘rishi: [reference → Admin panel sahifalari](reference.md).

| Vazifa | Fayl |
|---|---|
| Yangi sahifa | `src/pages/XxxPage.vue` + `src/router.ts` ga marshrut (`meta.roles` yoki `superOnly`) + `components/AppSidebar.vue` ga menyu bandi |
| Backendga so‘rov | `src/lib/api.ts` (`api.get/post/patch`) — **faqat shu orqali** (`fetch` to‘g‘ridan-to‘g‘ri yo‘q). Timeout 30 s (fayl yuklash 2 min), HTML/502 javob tushunarli xabarga aylanadi, 401 sessiya tugashiga olib keladi |
| Sessiya tugashi, saqlanmagan ish | `src/lib/session.ts`, `components/SessionExpiredModal.vue`: foydalanuvchi yozmagan bo‘lsa — kirish sahifasiga; yozib turgan bo‘lsa (`trackUnsaved(dirty)` yoki maydonga yozgan) — sahifa o‘zgarmaydi, «Qayta kirish» yangi oynada ochiladi, kirgach «Saqlash» qayta bosiladi |
| Kirish holati, rol tekshiruvi | `src/lib/auth.ts` |
| 4 tilli maydon | `components/I18nFields.vue`, `LangTabs.vue` |
| Matn muharriri | `components/RichEditor.vue` (TipTap) |
| Rasm/fayl tanlash | `MediaPicker.vue`, `ImageField.vue`, `PdfAttachments.vue` |
| Uslublar | `src/styles.css` (Tailwind 4; tugmalar uchun global `cursor: pointer` qoidasi shu yerda) |

> **Rol yashirish faqat qulaylik.** Sahifani menyudan yashirish xavfsizlik emas — haqiqiy ruxsat backendda (`apps/panel/collections.py`). Yangi bo‘lim qo‘shsangiz, ikkalasini ham moslang ([03-ruxsatlar](03-ruxsatlar.md)).
