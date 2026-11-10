# 4. Xavfsizlik: nima himoyalangan, qayerda, qanday tekshiriladi

## Tahdid → himoya → kod → test

| Tahdid | Himoya | Kod | Test |
|---|---|---|---|
| Parolni terib ko‘rish | 5 xato → 15 daqiqa blok; login uchun 10/min; mavjud bo‘lmagan loginlar ham bloklanadi (login topib bo‘lmaydi) | `apps/panel/auth.py`, `core/throttles.py` | `tests/security/test_auth.py`, `test_hardening.py` |
| Boshqa odam ma’lumotini id almashtirib olish (IDOR) | kabinet faqat sessiyadagi HEMIS ID bo‘yicha; fakultet doirasi; post egasi | `api/views_staff.py`, `panel/collections.py` | `test_access_control.py`, `test_data_theft.py` |
| `where`/`sort` orqali parol xeshini topish | faqat modelning o‘z, yashirin bo‘lmagan maydonlari; bog‘liq jadvallar bo‘ylab o‘tish rad etiladi | `apps/panel/query.py` | `test_query_injection.py` |
| Tokenni o‘g‘irlash/qayta ishlatish | JWT'da `jti`; logout/yangilash/parol o‘zgarishi/hisob yopilishida bekor | `apps/panel/jwt.py` | `test_jwt_roles.py` |
| 2FA ni aylanib o‘tish | TOTP, bir kod ikki marta ishlamaydi, kod xatolari bloklanadi | `apps/panel/twofactor.py` | `test_auth.py` |
| CSRF (cookie bilan) | yozuvchi so‘rovlar `Origin` bo‘yicha (`TRUSTED_ORIGINS`) | `apps/panel/auth.py` | `test_auth.py` |
| Zararli fayl yuklash (PDF/Office/rasm) | magic bytes, rasm qayta quriladi, PDF/OOXML faol kontent rad etiladi, zip-bomba chegaralari | `apps/core/filesafe.py`, `core/uploads.py` | `test_files.py` |
| Fuqaro murojaat fayllari ochiq qolishi | ochiq `/media/` dan tashqarida (`PRIVATE_ROOT`), faqat superadmin yuklab oladi | `apps/core/storage.py` | `test_files.py` |
| Yuklab olingan fayl brauzerda skript bajarishi | qat’iy Content-Type, `nosniff`, `sandbox` CSP, xavfli tur → `attachment` | `apps/core/middleware.py` | `test_files.py` |
| Matnga zararli HTML (XSS) | muharrir HTML'i `nh3` bilan tozalanadi | `apps/core/html.py` | `test_files.py` |
| Qalbaki/katta so‘rov tanasi | JSON faqat obyekt, chuqurlik chegarasi, NUL bayt tozalanadi, hajm yo‘l bo‘yicha cheklanadi | `apps/core/parsers.py`, `core/middleware.py` | `test_hardening.py` |
| Scraping va haddan ko‘p so‘rov | `THROTTLE_*` (IP/foydalanuvchi bo‘yicha), `NUM_PROXIES` | `apps/core/throttles.py` | `test_throttling_cache.py` |
| Keshni to‘ldirish (cache-busting) | kesh kalitiga faqat ma’lum parametrlar kiradi | `apps/api/common.py` (`CACHE_PARAMS`) | `test_cache_pressure.py` |
| Xususiy javob keshda qolishi | admin/kabinet/kirish javoblari `private, no-store`; token bilan himoyalangan — `private` | `apps/core/middleware.py`, `api/common.py` | `test_hardening.py`, `test_cache_pressure.py` |
| Statistikani soxtalashtirish | `/hit` takrorlari 10 s ichida bir marta, yuklab olish soatiga bir marta (IP) | `apps/api/hits.py`, `api/views.py` | `test_cache_pressure.py` |
| HEMIS ga ortiqcha bosim | faqat kechasi, pauza, so‘rov byudjeti, circuit breaker, OAuth global chegara | `apps/hemis/guard.py`, `hemis/schedule.py` | `tests/hemis/test_load_control.py` |
| Production'da noto‘g‘ri sozlama | ishga tushganda `manage.py check` ogohlantiradi | `apps/core/checks.py` | `test_production_checks.py` |
| Ruxsatlar hujjati kodga mos kelmay qolishi | Swagger'dagi rollar haqiqiy 403 bilan solishtiriladi | `apps/api/swagger.py` | `test_role_matrix.py`, `tests/api/test_swagger.py` |

Hammasini birga: `cd backend && python manage.py test tests.security` (≈10 s).

## Doimiy tekshiruvlar (qo‘lda yoki CI'da)

| Nima | Buyruq | Qachon |
|---|---|---|
| Production sozlamalari | `python manage.py check` (`DEBUG=false` bilan) — [reference → tekshiruvlar](reference.md) | har deployda |
| Zaif Python kutubxonalari | `pip install pip-audit && pip-audit -r backend/requirements.txt` | oyiga kamida bir marta (CI'da ham bor, ma’lumot uchun) |
| Zaif Node kutubxonalari | `cd frontend && npm audit --audit-level=high` · `cd admin && npm audit --audit-level=high` | shu |
| Xavfsizlik testlari | `python manage.py test tests.security` | har o‘zgarishda |
| Kirish tarixi va faollik | Admin panel → «Kirish tarixi», «Faollik jurnali» (faqat superadmin) | shubha bo‘lsa |

## Production uchun majburiy sozlamalar

| O‘zgaruvchi | Qiymat | Nega |
|---|---|---|
| `DEBUG` | `false` | aks holda Swagger ochiq, xatolar ko‘rinadi |
| `SECRET_KEY` | ≥ 50 belgi, tasodifiy | JWT va sessiyalar shunga tayanadi (`W003`) |
| `API_TOKEN` | ≥ 24 belgi, tasodifiy (frontendda `NUXT_API_TOKEN` bilan bir xil) | ochiq API'ni faqat sayt serveri ochadi (`W001`, `W002`) |
| `ALLOWED_HOSTS` | faqat o‘z domeningiz | `*` bo‘lmasin (`W004`) |
| `TRUSTED_ORIGINS` | faqat admin panel va sayt domenlari (**localhost'siz**) | cookie bilan so‘rov yuboradigan manzillar (`W007`) |
| `NUM_PROXIES` | nginx ortida `1`, Cloudflare + nginx ortida `2` | aks holda hamma foydalanuvchi bitta IP ko‘rinadi, cheklov ishlamaydi (`W005`) |
| `API_DOCS_PUBLIC` | `false` | Swagger faqat admin panelga kirganlarga (`W006`) |
| `SUPERADMIN_PASSWORD` | ≥ 12 belgi, oddiy emas | aks holda superadmin yaratilmaydi |
| `REQUIRE_2FA_ROLES` | `superadmin,editor` | majburiy ikki bosqichli tasdiq |
| `REDIS_URL` | bir nechta jarayon/server bo‘lsa majburiy | bloklash va cheklov hisobi umumiy bo‘lishi uchun |
| `BACKUP_COPY_TO` | boshqa disk/tarmoq papkasi | disk buzilsa zaxira ham yo‘qolmasin (`W009`) |

Nginx tomoni (HTTPS, `X-Forwarded-Proto`, `/media/` qoidalari, `/private/` yopiq): [10-server](10-server.md).

## Hodisaga javob (nima qilish kerak)

| Holat | Qadamlar |
|---|---|
| Xodim ketdi yoki hisob buzilgan | Admin panel → Foydalanuvchilar → holati **«Yopilgan»** (tokenlari darhol o‘ladi); parolini almashtiring |
| Superadmin paroli sizdi | `docker compose exec backend python manage.py changepassword <login>`; Kirish tarixi'ni ko‘rib chiqing; 2FA yoqing |
| `API_TOKEN` sizdi | `API_TOKEN=yangi,eski` → frontend `NUXT_API_TOKEN` ni yangilang → `API_TOKEN=yangi` (to‘xtovsiz almashtirish) |
| `SECRET_KEY` sizdi | yangisini qo‘ying, backendni qayta ishga tushiring — barcha sessiya va JWT bekor bo‘ladi, hamma qayta kiradi |
| Shubhali yuklama (DoS/scraping) | `docker compose logs backend`; `THROTTLE_*` ni pasaytiring; nginx darajasida IP'ni bloklang |
| Ma’lumot buzildi/o‘chirildi | [07-zaxira](07-zaxira.md): `backup --find <sana>` → `restore <sana> --yes` |
| Xodim kabineti tokeni sizdi | `StaffSession` yozuvlarini o‘chiring (`manage.py shell`) yoki muddati (12 soat) tugashini kuting |

## Ataylab qoldirilgan joylar (bilib turing)

- Docker image `root` bilan ishlaydi (lokal/oddiy deploy uchun; qattiqroq muhitda `USER` qo‘shing).
- `?trash=true` postlarni o‘qiy oladigan rollarga ochiq (savatni ko‘rish).
- HTTP → HTTPS yo‘naltirishni nginx qiladi (`SECURE_SSL_REDIRECT` Docker healthcheck'ni buzmasligi uchun yoqilmagan).
- `/api/site/*` (Payload bilan mos) `API_TOKEN`siz ochiq — frontend uchun; maxfiy ma’lumot bermaydi.
- TOTP kaliti bazada ochiq saqlanadi (standart usul), API'da hech qachon ko‘rinmaydi.
- Fayl tekshiruvi antivirus emas (zero-day'ni istisno qilmaydi) — [`backend/README.md`](../backend/README.md) «Fayllar xavfsizligi».
