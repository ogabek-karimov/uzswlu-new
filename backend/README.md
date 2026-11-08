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
`/api/docs/` (Swagger UI; dizayn: `SWAGGER_THEME=modern|classic`), `/api/redoc/`, `/api/schema/` (OpenAPI 3.1). Ochiq sayt API'sining tavsifi
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

## Xavfsizlik va yuklama himoyasi

**Boshqa odam ma'lumotiga id almashtirib chiqishdan himoya (IDOR)**
- Xodim kabineti (`/api/me*`): hamma amal faqat sessiyadagi xodimning HEMIS ID'si bo'yicha; id URL'dan olinmaydi. Boshqa xodim hujjati id bo'yicha ham `404`.
- Admin panel: `users` — editor/pages/sdg/faculty faqat o'zini ko'radi va o'zgartiradi (rolini oshira olmaydi). Fakultet admini (`faculty`) faqat `User.scope` dagi fakultet va uning kafedralarini o'zgartiradi; boshqasi `403`, kafedrani boshqa fakultetga ko'chirib bo'lmaydi, ommaviy (bulk) amallar ham yozuv-yozuv tekshiriladi. **`scope` bo'sh fakultet admini hech narsani o'zgartira olmaydi.**
- `where[...]` va `sort` faqat modelning o'z maydonlari bo'yicha ishlaydi: `password` va boshqa yashirin maydonlar, bog'liq jadvallar bo'ylab o'tish (`uploadedBy.password`) rad etiladi (parol xeshini harf-harf topib olishning oldi olingan). Filtr chuqurligi, shartlar soni va `limit` (`ADMIN_MAX_LIMIT`) cheklangan.
- Postlar: `faculty` va `pages` rollari faqat o'zi yozgan postni tahrirlaydi/o'chiradi/tiklaydi (muallifi yo'q eski postlar ham 403); `editor` va `superadmin` — hamma postni.
- `/api/site/staff-hidden` (yashirilgan xodimlar id'lari): `API_TOKEN` belgilangan bo'lsa token talab qilinadi.
- 2FA (TOTP, RFC 6238): Profil → "Ikki bosqichli tasdiq". Yoqilgan bo'lsa `POST /users/login` sessiya/token o'rniga `twoFactorRequired` + 5 daqiqalik `challenge` qaytaradi, `POST /users/login/2fa` (challenge + 6 xonali kod yoki zaxira kod) kirishni yakunlaydi. Kod xatolari parol xatolari bilan bir hisobda (5 ta → 15 daqiqa blok), bir kod ikki marta ishlamaydi, 8 ta bir martalik zaxira kod beriladi. `REQUIRE_2FA_ROLES=superadmin,editor` — shu rollar yoqmaguncha panel ma'lumotlariga kira olmaydi va o'chira olmaydi. Telefon yo'qolsa: zaxira kod yoki superadmin `POST /users/2fa/reset`. HEMIS orqali kirish (OAuth) HEMIS'ning o'z autentifikatsiyasiga tayanadi, TOTP so'ralmaydi. TOTP kaliti bazada ochiq saqlanadi (standart usul), API'da hech qachon ko'rinmaydi.
- Parolni almashtirish: o'z parolini o'zgartirishda `currentPassword` majburiy (noto'g'ri urinish 15 daqiqada 5 tadan keyin to'xtatiladi); superadmin boshqaning parolini tiklashi uchun shart emas.
- JWT: har tokenda `jti` bor; `POST /users/logout` va `/users/refresh-token` eski tokenni darhol bekor qiladi (bazadagi `RevokedToken`, muddati o'tgach tozalanadi). Parol o'zgarsa yoki hisob yopilsa ham token o'ladi.
- Kirish: mavjud bo'lmagan login uchun ham xesh hisoblanadi (javob vaqti bilan login mavjudligi bilinmaydi); HEMIS OAuth `state` doimiy vaqtda solishtiriladi.

**So'rov cheklovlari (rate limit)** — `apps/core/throttles.py`, qiymatlari `.env`da (`THROTTLE_*`):

| Manzil | Chegara | Hisob |
|---|---|---|
| Admin kirish / token yangilash | 10/min | IP |
| Ochiq API (`API_TOKEN`siz) | 300/min | IP (to'g'ri `API_TOKEN` bilan sayt serveri cheklanmaydi) |
| Qidiruv | 40/min | IP |
| Murojaat yuborish | 20/soat | IP (+ bir email — kuniga 3 ta) |
| Admin API | o'qish 1200/min, yozish 180/min | foydalanuvchi |
| Kabinet / fayl yuklash | 180/min / 30 soat | xodim |
| HEMIS kirish | 20/min | IP |
| Swagger/sxema | 60/min | IP/foydalanuvchi |

IP `X-Forwarded-For` dan faqat `NUM_PROXIES` (ishonchli proksilar soni) hisobga olinib olinadi — mijoz sarlavhani soxtalashtirib cheklovdan qutula olmaydi. **Nginx/Cloudflare ortida `NUM_PROXIES` ni to'g'ri qo'ying** (aks holda hamma foydalanuvchi bitta IP ko'rinadi). Sayt (Nuxt) serveri tashrifchi IP'sini `X-Forwarded-For` bilan uzatsin.

**Yuklama**
- Ochiq GET javoblari `PUBLIC_CACHE_SECONDS` (60 s) keshlanadi; admin panelda o'zgarish, xodim kabineti, media yoki HEMIS nusxasi yangilansa kesh darhol eskiradi. Kesh `API_TOKEN` va so'rov cheklovidan keyin tekshiriladi (ularni chetlab o'tmaydi). `REDIS_URL` berilsa umumiy Redis keshi, bo'lmasa fayl keshi.
- HEMIS: foydalanuvchi so'rovlari HEMIS'ga bormaydi (bazadagi nusxadan o'qiydi, `HEMIS_CACHE_SECONDS` da yangilanadi, xodimlar ro'yxati xotirada). Sinxronlashda sahifalar orasida pauza va 3 martagacha urinish; HEMIS OAuth uchun qisqa timeout (8 s), 5 ta ketma-ket xatodan keyin 30 soniya "circuit breaker" (HEMIS qulasa ham backend osilib qolmaydi) va javob hajmi chegarasi.
- Gunicorn: `WEB_CONCURRENCY`×`WEB_THREADS`, so'rov vaqti 30 s, har 1000 so'rovdan keyin jarayon yangilanadi (xotira oqishi), so'rov satri/sarlavhalari cheklangan. Yuklama oshsa — `WEB_CONCURRENCY` ni oshiring va `REDIS_URL` bering.
- Production: HSTS, `Secure`/`HttpOnly`/`SameSite` cookie, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`.

- `API_TOKEN` almashtirish to'xtovsiz: `API_TOKEN=yangi,eski` (ikkalasi ishlaydi) → frontendni yangilang → `API_TOKEN=yangi`. Production ishga tushganda zaif sozlamalar (qisqa token/SECRET_KEY, `ALLOWED_HOSTS=*`, `NUM_PROXIES=0`, ochiq Swagger) haqida ogohlantirish chiqadi (`manage.py check`); zaif `SUPERADMIN_PASSWORD` bilan productionda superadmin yaratilmaydi.
- Kutubxona zaifliklari: `requirements.txt` da Django ≥ 5.2.19. Vaqti-vaqti bilan: `pip install pip-audit && pip-audit -r requirements.txt` va admin/frontend papkalarida `npm audit`; Docker'ni `--build` bilan qayta yig'ish yangi tuzatishlarni oladi.

Testlar: `python manage.py test apps.api` (IDOR, parol oracle, so'rov cheklovi, kesh, JWT, post egaligi).


## Fayllar xavfsizligi (yuklash va yuklab olish)

Hammasi Python'da (Pillow + standart kutubxona), tashqi dastur (antivirus, ImageMagick) kerak emas. Kod: `apps/core/filesafe.py`.

**Yuklashda** (murojaat ilovasi, kabinet hujjati, panel media, xodim surati):
- Kengaytma ruxsat ro'yxatida, tarkib (magic bytes) kengaytmaga mos; mijoz fayl nomi **hech qachon saqlanmaydi** (tasodifiy nom).
- **Rasm** piksellaridan qayta quriladi: EXIF/GPS, ICC va fayl oxiriga yopishtirilgan ma'lumot (polyglot) yo'qoladi. Rasm o'lchami cheklangan (≤ 40 Mpx, ≤ 12000 px) — «decompression bomb»ga qarshi. SVG, BMP, TIFF qabul qilinmaydi.
- **PDF**: JavaScript, Launch, EmbeddedFile, SubmitForm, GoToR, RichMedia, XFA, parol (Encrypt) bo'lsa rad etiladi; `#xx` bilan yashirilgan nomlar ochiladi; `/ObjStm` oqimlari (skript yashiriladigan joy) zlib bomba chegarasi bilan ochilib skanerlanadi; `%%EOF` dan keyin qo'shimcha ma'lumot (polyglot) rad etiladi.
- **docx/pptx**: zip bomba (yozuvlar soni, hajm, siqish nisbati), xavfli yo'l nomlari (`..`, `/`), makro (`vbaProject`), ActiveX, ichki OLE/bajariladigan fayllar, hyperlinkdan boshqa tashqi ulanishlar (shablon/rasm tracker) rad etiladi.
- **doc/ppt** (eski format): VBA/Macros/ObjectPool/Ole10Native belgilari bo'lsa rad etiladi. Eski formatlar o'z tabiatiga ko'ra xavfliroq — kerak bo'lmasa `DOC_RULES` va `APPEAL_FILE_TYPES` dan olib tashlang.
- So'rov hajmi fayl o'qilishidan OLDIN cheklanadi (`UPLOAD_LIMITS`, 413/411); xodim kabinetida kvota: 100 ta fayl / 300 MB.

**Murojaat ilovalari yopiq**: `PRIVATE_ROOT` (standart `backend/private/`) da, ochiq `/media/` dan tashqarida. Faqat superadmin `/api/cms/private/<yo'l>` orqali yuklab oladi (`attachment`, `nosniff`, `no-store`). Ilgari `/media/appeals/` ga tushganlarni migratsiya o'zi ko'chiradi. Serverda `PRIVATE_ROOT` ni alohida volume qiling va zaxiralang.

**Yuklab olishda** (`/media/`): Content-Type kengaytma bo'yicha qat'iy, `X-Content-Type-Options: nosniff`; rasm/audioda `sandbox` CSP; ruxsat etilmagan tur (html, svg, ...) hech qachon brauzerda ochilmaydi — `attachment`. Django shuni `MediaHeadersMiddleware` bilan qiladi. **Productionda `/media/` ni nginx bersa**, shu qoidalarni nginx'da ham qo'ying:

```nginx
location /media/ {
    alias /srv/uzswlu/backend/media/;
    types { image/webp webp; image/jpeg jpg jpeg; image/png png; image/gif gif; audio/mpeg mp3; application/pdf pdf; }
    default_type application/octet-stream;            # noma'lum tur — hech qachon html emas
    add_header X-Content-Type-Options nosniff always;
    add_header Content-Security-Policy "default-src 'none'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'; sandbox" always;
    if ($uri !~* \.(webp|jpe?g|png|gif|mp3|pdf)$) { add_header Content-Disposition attachment always; }
    client_max_body_size 55m;                         # Django ham cheklaydi (UPLOAD_LIMITS)
    autoindex off;
}
location /private/ { return 404; }                    # yopiq fayllar nginx orqali berilmaydi
```

Cheklovlar: bu antivirus emas — noma'lum (zero-day) ekspluatatsiya yoki shifrlangan ichki yuklamani to'liq istisno qilmaydi; shuning uchun rasm qayta quriladi, faol kontent rad etiladi, fayllar `sandbox`/`attachment` bilan beriladi. Doc/ppt, docx/pptx va PDF parserlari foydalanuvchi kompyuteridagi dasturlarda ishlaydi — murojaat fayllarini ochishda ehtiyot bo'ling.


## Testlar

`python manage.py test --parallel` (≈15 s) — hamma backend testlari; tuzilma, yangi test yozish va CI haqida: [`tests/README.md`](tests/README.md).
Hamma qismlar: `scripts/test.sh` (Windows: `scripts\test.ps1`).
