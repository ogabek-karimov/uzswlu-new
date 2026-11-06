# ÖzDJTU backend (Django + DRF)

| Manzil | Nima |
|---|---|
| http://localhost:8000/api/ | Sayt API — `frontend/docs/openapi.yaml` shartnomasi (`?lang=uz\|ru\|en\|zh`) |
| http://localhost:8000/api/site/ | Payload bilan mos manzillar (`NUXT_CMS_BASE`) |
| http://localhost:8000/api/cms/ | Vue admin panel API'si (Payload REST bilan bir xil shakl) |
| http://localhost:8000/api/docs/ | Swagger UI (`/api/redoc/`, `/api/schema/`) |
| http://localhost:8000/api/auth/hemis/ | HEMIS orqali kirish (OAuth2) va holat |

Swagger: `API_DOCS_PUBLIC` (sukut — `DEBUG`) `false` bo'lsa, faqat admin panelga kirgan xodim ko'radi (sessiya yoki JWT).

## Ishga tushirish (Docker)
```
cp .env.docker.example .env.docker
cp backend/.env.example backend/.env     # SECRET_KEY, parollarni o'zgartiring
docker compose up -d                     # loyiha nomi: uzswlu-drf, backend :8000, baza :5433
```
Birinchi ishga tushishda migratsiyalar, superadmin (`SUPERADMIN_*`) va namunaviy ma'lumot o'zi yaratiladi.

## Vue admin panel
Admin panel o'zgarishsiz ishlaydi — faqat backend manzili: `admin/` da `npm run dev`
(`BACKEND_URL=http://localhost:8000` — sukut bo'yicha shu; boshqa port kerak bo'lsa `ADMIN_PORT=5174`).
Admin so'rovlari `/api/cms/*` ga boradi: login (5 marta xato → 15 daqiqa blok, kirish tarixi), kolleksiyalar
(`where`, `sort`, `limit`, `page`, `depth`), fayl yuklash (WebP), versiyalar va qaytarish, postlar savati,
ommaviy amallar, sozlamalar tarixi, statistika, HEMIS ma'lumoti. Rollar: superadmin, editor, faculty, pages, sdg.
Admin panel boshqa manzilda bo'lsa, u `TRUSTED_ORIGINS` da bo'lishi shart (POST/PATCH/DELETE `Origin` bo'yicha tekshiriladi).

## Payload'dan ma'lumot ko'chirish (bir marta)
```
docker compose exec backend python manage.py import_payload --replace
```
`.env`: `PAYLOAD_DATABASE_URL` (Payload bazasi, faqat o'qiladi) va `PAYLOAD_MEDIA_URL` (…/api/media/file/) yoki
`--media-dir`. Fayllar, foydalanuvchilar (parollari bilan — birinchi kirishda Django usuliga o'tadi), postlar,
sahifalar, BRM, tuzilma, sozlamalar, faollik jurnali va kirish tarixi ko'chadi. Matndagi eski fayl manzillari
yangilanadi; `/api/media/file/<nom>` eski havolalar ham yangi faylga yo'naltiriladi.

## HEMIS
Hozir ulanmagan — `seed_data/hemis-snapshot.json` (namuna) ishlatiladi. Ulash uchun `.env`:
```
HEMIS_API_URL=https://hemis.<universitet>.uz/rest/v1
HEMIS_API_TOKEN=...
HEMIS_FACULTY_TYPES=11      # department-list → structureType.code (universitetda tekshiring)
HEMIS_CHAIR_TYPES=12
```
keyin har kuni (cron, 06:00): `python manage.py sync_hemis` — xodimlar, bo'limlar, dekan/mudirlar va talaba soni
bazaga (`HemisSnapshot`) yoziladi; sayt va admin panel shu nusxadan o'qiydi. Fakultet bog'lanishi — `Faculty.hemis_id`
(bo'lmasa nomi bo'yicha).

HEMIS orqali kirish (OAuth2): `HEMIS_OAUTH_URL`, `HEMIS_OAUTH_CLIENT_ID`, `HEMIS_OAUTH_CLIENT_SECRET`.
OAuth client'da qaytish manzili: `<PUBLIC_SERVER_URL>/api/auth/hemis/callback`.
- Admin panel: `/api/auth/hemis/login?next=admin` — faqat superadmin HEMIS ID biriktirgan xodim kiradi; F.I.Sh., lavozim
  va bo'lim HEMIS'dan yangilanadi.
- Xodim kabineti: `/api/auth/hemis/login?next=cabinet` — sayt sessiyasi cookie'da.

Holat: `GET /api/auth/hemis/status`. Sinov uchun kabinet tokeni: `python manage.py issue_staff_session <hemis_id>`
→ `Authorization: Bearer <token>`.

## Lokal (Postgres'siz)
```
cd backend && pip install -r requirements.txt
export DEBUG=true DATABASE_URL=sqlite:///db.sqlite3 SUPERADMIN_PASSWORD=...
python manage.py migrate && python manage.py seed_demo && python manage.py runserver 8000
```
(Statistika va Payload'dan ko'chirish faqat PostgreSQL bilan.)

## Frontend sozlamasi
`NUXT_API_BASE=http://localhost:8000/api`, `NUXT_API_TOKEN=<API_TOKEN>`,
`NUXT_CMS_BASE=http://localhost:8000/api/site`.

## Docker compose xizmatlari
`db` (PostgreSQL), `backend` (Django, healthcheck `/healthz`), `hemis-sync` (HEMIS'ni har 24 soatda yangilaydi),
`frontend` (Nuxt, :3000), `admin` (Vue, :5173). Port band bo'lsa (sababini `netstat -ano | findstr ":8000"` ko'rsatadi; ko'pincha `netsh interface portproxy` qoidasi) — ildiz `.env` ga `BACKEND_PORT=3001`
yozing va `backend/.env` da `PUBLIC_SERVER_URL=http://localhost:3001` qiling.
Frontend kaliti: `frontend/.env` dagi `NUXT_API_TOKEN` = `backend/.env` dagi `API_TOKEN`.

## Swagger
`/api/docs/` (Swagger UI; dizayn: `SWAGGER_THEME=classic|creative`), `/api/redoc/`, `/api/schema/` (OpenAPI 3.1). Ochiq sayt API'sining tavsifi
`frontend/docs/openapi.yaml` dan olinadi (Docker'da ulangan; bo'lmasa `apps/api/contract/openapi.yaml` nusxasi),
`/api/site/*`, `/api/me*`, admin panel (`/api/cms/*`) va HEMIS manzillari backenddan hosil qilinadi.
Shartnoma o'zgarsa nusxani yangilang: `cp frontend/docs/openapi.yaml backend/apps/api/contract/openapi.yaml`.
Productionda `API_DOCS_PUBLIC=false` — faqat admin panelga kirganlar ko'radi.

## Avtorizatsiya (Swagger'da ham ishlaydi)
- **Admin panel (Vue)**: `POST /api/cms/users/login` — sessiya cookie qo'yadi va javobda `token` (JWT) qaytaradi.
  Cookie'siz: `Authorization: Bearer <token>`. Yangilash: `POST /api/cms/users/refresh-token`. Muddat: `JWT_TTL_SECONDS` (8 soat).
  JWT parol o'zgarganda, hisob yopilganda yoki muddati tugaganda bekor bo'ladi.
- **Ochiq sayt API'si**: `Authorization: Bearer <API_TOKEN>` (`API_TOKEN` bo'sh bo'lsa shart emas).
- **Xodim kabineti** (`/api/me*`): HEMIS sessiyasi (cookie) yoki `issue_staff_session` tokeni.
- **Rollar**: `superadmin`, `editor`, `faculty`, `pages`, `sdg` — har kolleksiya uchun jadval Swagger'dagi tegishli amalning tavsifida.
- Swagger'da: `/api/cms/users/login` → "Try it out" → javobdagi `token` ni **Authorize** → `panelJwt` ga kiriting.
- Django admin (Jazzmin) olib tashlangan: boshqarish faqat Vue admin panel orqali (`http://localhost:5173`).
