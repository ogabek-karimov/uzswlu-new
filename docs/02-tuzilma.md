# 2. Tuzilma: papkalar, arxitektura, ma’lumot oqimi

## Repozitoriy xaritasi

| Papka / fayl | Nima | Kirish nuqtasi |
|---|---|---|
| `backend/` | Django 5.2 + DRF: API, admin panel API'si, HEMIS, zaxira | `backend/manage.py`, `backend/config/settings.py` |
| `frontend/` | Nuxt 4 sayt (Tailwind 4, 4 til) + Nuxt server qatlami | `frontend/nuxt.config.ts`, `frontend/app/pages/` |
| `admin/` | Vue 3 admin panel (Vite, Tailwind 4, TipTap muharriri) | `admin/src/router.ts`, `admin/src/pages/` |
| `docs/` | shu qo‘llanma | `docs/README.md`, `docs/index.html` |
| `scripts/` | hamma testlarni bitta buyruqda: `test.sh`, `test.ps1` | — |
| `docker-compose.yml` | lokal muhit: db, backend, nightly, frontend, admin | — |
| `.github/workflows/ci.yml` | CI: backend (SQLite+PostgreSQL), frontend, admin, audit, hujjat | — |
| `.env.docker.example`, `backend/.env.example`, `frontend/.env.example` | sozlama namunalari | — |
| `backend/seed_data/` | boshlang‘ich kontent va namunaviy HEMIS nusxasi | `seed_demo` buyrug‘i |

## Arxitektura

```
Brauzer ──► Nuxt server (frontend :3000) ──► Backend /api/…  ──► PostgreSQL
              │   token (API_TOKEN) faqat shu yerda               ▲
              │   oxirgi yaxshi javob keshi, /media keshi          │
              ▼                                                    │
        brauzerga HTML                                  Admin panel (:5173) ──► Backend /api/cms/…
                                                         (cookie yoki JWT)
Kechasi:  nightly konteyneri ──► zaxira → HEMIS sinxronlash → tozalash
                                       └──► HEMIS REST API (faqat tinch oynada; foydalanuvchi so‘rovi HEMIS'ga bormaydi)
```

Asosiy qoidalar:

- **Brauzer backendga to‘g‘ridan-to‘g‘ri chiqmaydi** (sayt uchun): `brauzer → Nuxt server → backend`. `API_TOKEN` faqat Nuxt serverida turadi.
- **Admin panel** backendga `/api/cms/*` orqali boradi; Vite dev serveri `/api` ni backendga proksi qiladi (cookie bitta manzildan ishlashi uchun). Serverda buni nginx qiladi.
- **HEMIS** — faqat o‘qiladi va faqat kechasi nusxa olinadi. Sayt va admin bazadagi nusxadan o‘qiydi ([08-hemis-kesh](08-hemis-kesh.md)).
- **Kontent** admin panelda o‘zgarsa → baza → ochiq API keshi versiyasi oshadi (`bump_content_version`) → sayt yangi ma’lumotni oladi.

## Ma’lumot oqimi: «admin yangilik qo‘shdi → saytda ko‘rindi»

1. Admin panel (`admin/src/pages/PostEditPage.vue`) `POST /api/cms/posts` yuboradi (JWT/cookie + `Origin` tekshiruvi).
2. `backend/apps/panel/views.py` → rol/ob’yekt ruxsati (`collections.py: can()`), HTML tozalanadi (`core/html.py`), rasm WebP'ga o‘giriladi (`core/uploads.py`), versiya va faollik jurnali yoziladi (`core/activity.py`).
3. `purge_site_cache()` → ochiq API kesh versiyasi oshadi (`SITE_PURGE_URL` berilsa, sayt serveriga ham xabar yuboriladi; ixtiyoriy).
4. Sayt `GET /api/posts` ni so‘raydi (`frontend/server/api/posts/…`) → `backend/apps/api/views.py` → `builders.py` javobni shartnoma shaklida yig‘adi.

## Kesh qatlamlari (muammo qidirganda foydali)

| Qatlam | Qayerda | Muddat | Qanday tozalanadi |
|---|---|---|---|
| Backend ochiq API keshi | `apps/api/common.py` (`CachedGetMixin`), Redis yoki fayl keshi | `PUBLIC_CACHE_SECONDS` (60 s) | admin o‘zgartirsa o‘zi (`bump_content_version`) |
| HEMIS nusxasi (xotirada) | `apps/hemis/cache.py` | `HEMIS_CACHE_SECONDS` (300 s) | sinxronlashdan keyin o‘zi |
| Nuxt «oxirgi yaxshi javob» | `frontend/server/utils/last-good.ts` | backend o‘chsa 3 soatgacha eski javob | `NUXT_STALE_IF_ERROR_SECONDS` |
| Nuxt media keshi | `frontend/server/utils/media-cache.ts` | vaqtinchalik | server qayta ishga tushsa |
| Brauzer | API `Cache-Control` | ≤ 30 s (token bilan himoyalangan — `private`) | — |
| So‘rov cheklovi hisobi | `core/throttles.py` | `THROTTLE_*` oynasi | `cache.clear()` |

## Backend ilovalari (`backend/apps/`)

| Ilova | Vazifasi | Asosiy modellar |
|---|---|---|
| `core` | umumiy: media, sozlamalar, faollik, fayl xavfsizligi, middleware, kechki vazifalar, zaxira, so‘rov cheklovi | `Media`, `SiteSettings`, `Activity`, `Hit` |
| `accounts` | admin foydalanuvchilar va xodim kabineti sessiyalari | `User`, `StaffSession` |
| `content` | postlar (yangilik/e’lon/tadbir), slayd, rahbariyat, hujjat, video, ramzlar | `Post`, `Slide`, `Document`, `Video`, … |
| `structure` | fakultet, kafedra, xodim profili, dasturlar, qabul, murojaat | `Faculty`, `Department`, `StaffProfile`, `Appeal` |
| `pages` | statik sahifalar va BRM (barqaror rivojlanish maqsadlari) | `Page`, `SdgGoal` |
| `hemis` | HEMIS klienti, nusxa, OAuth kirish, jadval | `HemisSnapshot` |
| `api` | **ochiq** sayt API'si, kabinet (`/me`), Swagger | — |
| `panel` | **admin panel** API'si (`/api/cms/*`), JWT, 2FA, kirish tarixi, versiyalar | `LoginEvent`, `Version`, `RevokedToken` |

Har bir fayl nima qiladi — avtomatik jadval: [reference → fayllar xaritasi](reference.md).

## Frontend (`frontend/`)

| Joy | Nima |
|---|---|
| `app/pages/` | sahifalar (fayl nomi = marshrut); til prefiksi: `/ru`, `/en`, `/zh` |
| `app/components/` | `home/*` bosh sahifa bloklari, `staff/*`, `cabinet/*`, `The*.vue` (sarlavha, footer) |
| `app/composables/` | `useSiteData`, `useTrack` (statistika), `useA11y` (ko‘rish qiyin foydalanuvchilar uchun) … |
| `i18n/locales/*.json` | interfeys matnlari: `uz`, `ru`, `en`, `zh` |
| `server/api/` | Nuxt server qatlami: brauzer shu yerga murojaat qiladi, u backendga boradi |
| `server/utils/backend.ts` | backendga so‘rov + oxirgi yaxshi javob + media havolalarini almashtirish |
| `server/utils/mock-*.ts` | `NUXT_API_BASE` bo‘sh bo‘lsa — namunaviy ma’lumot |
| `shared/types/api.ts` | API turlari (`frontend/docs/openapi.yaml` bilan bir xil) |
| `scripts/test-*.mts` | frontend testlari (`npm run test:last-good`) |

## Admin (`admin/`)

| Joy | Nima |
|---|---|
| `src/router.ts` | marshrutlar va rol bo‘yicha kirish (`roles`, `superOnly`) |
| `src/pages/*Page.vue` | har bo‘lim: Postlar, Media, Foydalanuvchilar, Statistika, BRM … |
| `src/lib/api.ts` | backendga so‘rovlar (`/api/cms/*`) |
| `src/lib/auth.ts` | kirish holati, `me()`, rol tekshiruvi |
| `src/components/` | `RichEditor` (TipTap), `MediaPicker`, `ImageField`, `LangTabs` (4 til) … |
| `vite.config.ts` | `/api` proksi (`BACKEND_URL`), port (`ADMIN_PORT`) |

## Keyingi qadam

Rollar va kirish: [03-ruxsatlar](03-ruxsatlar.md). Kodni kengaytirish: [12-qanday-qilaman](12-qanday-qilaman.md).
