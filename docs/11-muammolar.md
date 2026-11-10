# 11. Muammolar: xato → sabab → yechim

Avval **logni** ko‘ring: `docker compose logs --tail=100 backend` (yoki `nightly`, `frontend`, `admin`, `db`). Holat: `docker compose ps`.

## Ishga tushirish

| Belgi | Sabab | Yechim |
|---|---|---|
| `ports are not available: ... 8000` | port band (ko‘pincha `netsh portproxy` yoki boshqa dastur) | `netstat -ano \| findstr ":8000"`; ildiz `.env` ga `BACKEND_PORT=3001`, `backend/.env` da `PUBLIC_SERVER_URL=http://localhost:3001` |
| `docker-entrypoint.sh: no such file or directory` | Windows CRLF | `.sh` fayllar LF bo‘lsin (`.gitattributes` bor); `git add --renormalize .` va qayta build |
| `backend` doim `unhealthy` | migratsiya/DB xatosi | `docker compose logs backend`; baza parolini `.env.docker` va `backend/.env` (`DATABASE_URL`) da tenglang |
| `password authentication failed` | `pgdata` eski parol bilan yaratilgan | parolni qaytaring yoki (ma’lumot kerak emas bo‘lsa) `docker compose down -v` ⚠️ — **avval zaxira!** |
| Sayt ochiladi, lekin ma’lumot namunaviy | `NUXT_API_BASE` bo‘sh → mock | `frontend/.env` da `NUXT_API_BASE=http://backend:8000` |
| O‘zgartirgan kodim ko‘rinmayapti | konteyner eski; yoki kutubxona o‘zgargan | `docker compose up -d --build <xizmat>` |

## Kirish va ruxsatlar

| Belgi | Sabab | Yechim |
|---|---|---|
| Admin panelga kirolmayapman, «bloklangan» | 5 ta noto‘g‘ri urinish → 15 daqiqa blok | 15 daqiqa kuting yoki superadmin: Foydalanuvchilar → «Blokdan chiqarish» |
| Superadmin parolini unutdim | — | `docker compose exec backend python manage.py changepassword superadmin` |
| 2FA qurilmasi yo‘qoldi | telefon ham, zaxira kodlar ham yo‘q | superadmin: Foydalanuvchilar → foydalanuvchi qatoridagi «2FA» tugmasi (bekor qiladi, u qaytadan sozlaydi). Superadminning o‘zida bo‘lsa — serverda: `manage.py shell -c "from apps.accounts.models import User; u=User.objects.get(username='NOM'); u.totp_enabled=False; u.totp_secret=''; u.recovery_hashes=[]; u.save()"` |
| `401` ochiq API'da | `API_TOKEN` mos emas | backend `API_TOKEN` = frontend `NUXT_API_TOKEN` |
| `401` admin API'da | JWT muddati tugagan (8 soat) yoki chiqarib yuborilgan | qayta kiring |
| `403` + «Origin» | so‘rov `TRUSTED_ORIGINS` da yo‘q manzildan | domenni `TRUSTED_ORIGINS` ga qo‘shing (`https://…` aniq, oxirida `/` siz) |
| `403` boshqa fakultet ma’lumoti | foydalanuvchi `scope` bilan cheklangan | [03-ruxsatlar](03-ruxsatlar.md): scope ni o‘zgartiring |
| Muharrir «Foydalanuvchilar» bo‘limini ko‘rmaydi | bu faqat `superadmin` roli | normal holat; rol jadvali — [reference](reference.md) |

## So‘rovlar va yuklama

| Belgi | Sabab | Yechim |
|---|---|---|
| `429 Too Many Requests` hamma uchun birdan | `NUM_PROXIES=0`, nginx ortida hamma bitta IP | `NUM_PROXIES=1` |
| `429` bitta foydalanuvchida | haqiqatan ko‘p so‘rov | `THROTTLE_*` ni ko‘paytiring ([08-hemis-kesh](08-hemis-kesh.md)) yoki kesh tozalang |
| `413` | tana/fayl chegarasidan katta | `DATA_UPLOAD_MAX_MEMORY_SIZE`, `BODY_LIMITS`/`UPLOAD_LIMITS`, nginx `client_max_body_size` |
| `415` | ruxsat etilmagan `Content-Type` | JSON/multipart yuboring |
| Javoblar sekin | kesh o‘chiq yoki bitta jarayon | `PUBLIC_CACHE_SECONDS`, `REDIS_URL`, `WEB_CONCURRENCY` |

Keshni tozalash: `docker compose exec backend python manage.py shell -c "from django.core.cache import cache; cache.clear()"`.

## HEMIS

| Belgi | Sabab | Yechim |
|---|---|---|
| Ma’lumot eskirgan | kechasi sinxron ishlamagan | Boshqaruv paneli (HEMIS kartasi); `docker compose logs nightly`; `sync_hemis --force` |
| `sync_hemis` xato beradi | URL/token noto‘g‘ri yoki HEMIS ishlamayapti | `HEMIS_API_URL`, `HEMIS_API_TOKEN`; sayt eski nusxadan ishlashda davom etadi |
| Fakultet/kafedra ro‘yxati bo‘sh | `HEMIS_FACULTY_TYPES`/`HEMIS_CHAIR_TYPES` mos emas | HEMIS tashkilot turi kodlarini tekshiring |
| `nightly` ishlamayapti | konteyner yiqilgan | `docker compose up -d nightly`; `run_nightly` buyrug‘ini qo‘lda ishga tushiring |

## Zaxira

| Belgi | Sabab | Yechim |
|---|---|---|
| `backup --status` ≠ 0 | oxirgi zaxira `BACKUP_MAX_AGE_HOURS` (36 s) dan eski | `docker compose logs nightly`; qo‘lda `backup`; disk to‘lganmi (`df -h`) |
| `pg_dump: not found` | konteynerda `postgresql-client` yo‘q | `docker compose build backend` (Dockerfile'da bor) |
| `restore` rad etdi | `--yes` yo‘q yoki arxiv buzuq | `--yes`; `backup --list` da fayl butunligini tekshiring |
| Disk to‘ldi | `backups/` o‘sdi | `backup --plan` (nima o‘chadi), `BACKUP_KEEP_*` ni kamaytiring, `backup --prune` |

Batafsil: [07-zaxira](07-zaxira.md).

## Testlar

| Belgi | Yechim |
|---|---|
| `test_docs` yiqildi: «reference.md eskirgan» | `cd backend && python manage.py build_docs` va natijani commit qiling |
| `test_docs`: «havola/yo‘l topilmadi» | hujjatdagi fayl/anchor nomini to‘g‘rilang |
| PostgreSQL testlari ulanmayapti | `TEST_DATABASE_URL=postgres://…` ni tekshiring ([06-testlar](06-testlar.md)) |
| `/panel/stats` testi SQLite'da o‘tkazib yuborilgan | normal: bu faqat PostgreSQL'da |

## Hech narsa yordam bermasa

1. `docker compose logs --since 30m backend > log.txt` — xatoning aniq matni.
2. `docker compose exec backend python manage.py check` — sozlama ogohlantirishlari.
3. `python manage.py showmigrations | grep "\[ \]"` — qo‘llanmagan migratsiya bormi.
4. Eng oxirgi ishlaydigan holatga: [07-zaxira](07-zaxira.md) orqali `restore`.
