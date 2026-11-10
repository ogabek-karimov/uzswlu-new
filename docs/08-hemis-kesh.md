# 8. HEMIS, kechki vazifalar, kesh va yuklama himoyasi

## Asosiy g‘oya

**Foydalanuvchi so‘rovi HEMIS'ga hech qachon bormaydi.** HEMIS'dan nusxa **kechasi**, tinch oynada olinadi va bazaga (`HemisSnapshot`) yoziladi; sayt va admin panel faqat shu nusxadan o‘qiydi. Yagona istisno — HEMIS orqali kirish (OAuth), u ham cheklangan.

## Kechki vazifalar (`nightly` xizmati)

`docker compose` dagi `nightly` konteyneri `python manage.py run_nightly` ni doimiy ishlatadi (cron/Celery kerak emas). Har kuni `HEMIS_SYNC_AT` (+ tasodifiy kechikish) da, tinch oyna ichida **tartib bilan** bajaradi (biri yiqilsa qolganlari davom etadi):

| Vazifa | Nima qiladi |
|---|---|
| `backup` | zaxira nusxa → tekshirish → eskilarini tozalash ([07-zaxira](07-zaxira.md)) |
| `hemis` | HEMIS sinxronlash (`HEMIS_API_URL` bo‘sh bo‘lsa o‘tkazib yuboriladi) |
| `sessions` | muddati o‘tgan xodim sessiyalari va bekor qilingan JWT'larni tozalash |
| `login_events` | `LOGIN_EVENT_RETENTION_DAYS` (365) dan eski kirish tarixi |
| `hits` | `HIT_RETENTION_DAYS` (730) dan eski sayt statistikasi |

| Maqsad | Buyruq |
|---|---|
| Hozir hammasini bir marta | `python manage.py run_nightly --once` |
| Bitta vazifa | `python manage.py run_nightly --once --only backup` (`hemis`, `sessions`, …) |
| Oynadan tashqarida majburan | `… --force` |
| Faqat HEMIS | `python manage.py sync_hemis` (kunduzi rad etadi; `--force` bilan mumkin) |
| Natijani ko‘rish | `docker compose logs nightly` |

Qoidalar: qayta ishga tushsa sinxronlash **darhol boshlanmaydi**; ish tinch oynadan tashqarida boshlanmaydi; HEMIS yiqilsa oyna tugamaguncha 20 daqiqada bir marta, ko‘pi bilan 3 marta qayta uriniladi; ikki sinxronlash bir vaqtda ishlamaydi (bazada qulf); xato bo‘lsa oldingi nusxa saqlanadi.

## HEMIS ulash

`backend/.env`:

```
HEMIS_API_URL=https://hemis.<universitet>.uz/rest/v1
HEMIS_API_TOKEN=...
HEMIS_FACULTY_TYPES=11     # department-list → structureType.code (universitetda tekshiring)
HEMIS_CHAIR_TYPES=12
```

Ulanmagan paytda `backend/seed_data/hemis-snapshot.json` (namunaviy ma’lumot) ishlatiladi — admin panelda «HEMIS hali ulanmagan — namuna ma’lumot» ko‘rinadi.

Yuklama qoidalari (hammasi `.env` da, standart qiymatlar [reference → Sozlamalar](reference.md)):

| O‘zgaruvchi | Ma’nosi |
|---|---|
| `HEMIS_SYNC_AT` / `HEMIS_SYNC_JITTER_MINUTES` | har kuni shundan boshlab, +tasodifiy kechikish (har kuni boshqa daqiqa) |
| `HEMIS_SYNC_WINDOW` | HEMIS'ga faqat shu oynada chiqiladi (`TIME_ZONE` bo‘yicha) |
| `HEMIS_REQUEST_DELAY` | ikki so‘rov orasida pauza |
| `HEMIS_MAX_REQUESTS` | bitta sinxronlashda so‘rovlar byudjeti |
| `HEMIS_MAX_CONSECUTIVE_FAILURES` | ketma-ket shuncha xatoda to‘xtaydi (`429/503` da `Retry-After` kutiladi) |
| `HEMIS_OAUTH_GLOBAL_PER_MIN` | HEMIS orqali kirish: hamma IP uchun umumiy chegara |
| `HEMIS_CACHE_SECONDS` | bazadagi nusxani xotiraga qayta o‘qish oralig‘i |

Kod: `apps/hemis/` (`api.py` — mijoz, `guard.py` — circuit breaker, `schedule.py` — oyna, `sync.py`, `cache.py`). Testlar: `tests/hemis/test_load_control.py`.

### HEMIS orqali kirish (OAuth2)

`.env`: `HEMIS_OAUTH_URL`, `HEMIS_OAUTH_CLIENT_ID`, `HEMIS_OAUTH_CLIENT_SECRET`. OAuth client'da qaytish manzili: `<PUBLIC_SERVER_URL>/api/auth/hemis/callback`.

- Admin panel: `/api/auth/hemis/login?next=admin` — faqat superadmin HEMIS ID biriktirgan xodim kiradi.
- Xodim kabineti: `/api/auth/hemis/login?next=cabinet`.
- Holat: `GET /api/auth/hemis/status`. Kabinetni sinash: `python manage.py issue_staff_session <hemis_id>`.

## HEMIS holatini qayerda ko‘raman

- Admin panel → **Boshqaruv paneli** → HEMIS kartasi: oxirgi muvaffaqiyatli sinxronlash, eskirganmi (`stale`), oxirgi xato.
- Backend API: `GET /api/cms/panel/hemis` (superadmin/muharrir).
- Log: `docker compose logs nightly`.

## Kesh

Qatlamlar xaritasi: [02-tuzilma → Kesh qatlamlari](02-tuzilma.md).

| Savol | Javob |
|---|---|
| Admin o‘zgartirdi, saytda ko‘rinmayapti | ochiq API keshi o‘zi yangilanadi (`bump_content_version`); Nuxt tomonida eski javob `NUXT_STALE_IF_ERROR_SECONDS` faqat **backend o‘chganda** ko‘rsatiladi. Brauzerni `Ctrl+F5` bilan yangilang |
| Keshni qo‘lda tozalash | `docker compose exec backend python manage.py shell -c "from django.core.cache import cache; cache.clear()"` |
| Keshni o‘chirish (sinash uchun) | `.env` → `PUBLIC_CACHE_SECONDS=0` |
| Bir nechta jarayon/server | `REDIS_URL` bering (aks holda fayl keshi: `CACHE_DIR`) — bloklash va cheklov hisobi umumiy bo‘ladi |

## So‘rov cheklovlari (rate limit)

`apps/core/throttles.py`; qiymatlar `.env` da (`THROTTLE_*`, format: `son/vaqt` — `sec`, `min`, `hour`, `day`). Standartlar:

| Manzil | Chegara | Hisob |
|---|---|---|
| Admin kirish / token yangilash | 10/min | IP |
| Ochiq API (`API_TOKEN`siz) | 300/min | IP (to‘g‘ri `API_TOKEN` bilan sayt serveri cheklanmaydi) |
| Qidiruv | 40/min | IP |
| Murojaat yuborish | 20/soat (+ bir email — kuniga 3 ta) | IP |
| Admin API | o‘qish 1200/min, yozish 180/min | foydalanuvchi |
| Kabinet / fayl yuklash | 180/min / 30 soat | xodim |
| HEMIS kirish | 20/min | IP |
| Swagger/sxema | 60/min | IP/foydalanuvchi |

**`NUM_PROXIES` ni to‘g‘ri qo‘ying** (nginx ortida `1`): aks holda hamma foydalanuvchi bitta IP bo‘lib ko‘rinadi va birinchi 300 so‘rovdan keyin hamma uchun `429` boshlanadi. Sayt (Nuxt) serveri tashrifchi IP'sini `X-Forwarded-For` bilan uzatsin.

`429` olsangiz: kutib turing yoki (sinov uchun) `THROTTLE_*` ni oshiring; kesh tozalansa hisob ham nolga tushadi.

## Gunicorn (production)

`WEB_CONCURRENCY` (jarayonlar, 3), `WEB_THREADS` (oqimlar, 2), `WEB_TIMEOUT` (30 s). Har 1000 so‘rovdan keyin jarayon yangilanadi (xotira oqishiga qarshi). Yuklama oshsa — `WEB_CONCURRENCY` ni oshiring va `REDIS_URL` bering.
