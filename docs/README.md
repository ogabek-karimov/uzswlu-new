# ÖzDJTU loyihasi — qo‘llanma

Bu — loyiha bo‘yicha **yagona kirish nuqtasi**: «nimani qayerdan topaman», «nima bilan ishga tushiraman / tekshiraman / boshqaraman». Qidirish uchun [index.html](index.html) ni brauzerda oching (`/` tugmasi — qidiruv).

> Loyiha uchta qismdan iborat: **sayt** (`frontend/`, Nuxt), **admin panel** (`admin/`, Vue) va **backend** (`backend/`, Django + DRF + PostgreSQL). Hammasi Docker Compose bilan bitta buyruqda ishga tushadi.

| Nima | Manzil (lokal) | Papka |
|---|---|---|
| Sayt (4 til: uz, ru, en, zh) | http://localhost:3000 | `frontend/` |
| Admin panel | http://localhost:5173 (kirish: `/kirish`) | `admin/` |
| Backend API | http://localhost:8000/api/ | `backend/` |
| Swagger (API hujjati) | http://localhost:8000/api/docs/ | `backend/apps/api/swagger.py` |
| PostgreSQL | `localhost:5433` | Docker volume `pgdata` |

## Tez topish: «men … qilmoqchiman»

### Ishga tushirish va kundalik ish

| Maqsad | Buyruq / joy | Batafsil |
|---|---|---|
| Hammasini ishga tushirish | `docker compose up -d` | [01-boshlash](01-boshlash.md) |
| Nima ishlayotganini ko‘rish | `docker compose ps` | [01-boshlash](01-boshlash.md) |
| Xatoni qidirish (log) | `docker compose logs -f backend` | [11-muammolar](11-muammolar.md) |
| To‘xtatish (ma’lumot saqlanadi) | `docker compose down` | [01-boshlash](01-boshlash.md) |
| Port band, sayt ochilmayapti | ildiz `.env` → `BACKEND_PORT=3001` | [11-muammolar](11-muammolar.md) |
| Superadmin parolini unutdim | `docker compose exec backend python manage.py changepassword superadmin` | [11-muammolar](11-muammolar.md) |

### Kirish, rollar, ruxsatlar

| Maqsad | Qayerda | Batafsil |
|---|---|---|
| Kim nima qila oladi (rol jadvali) | `docs/reference.md` → «Rol × kolleksiya» | [03-ruxsatlar](03-ruxsatlar.md) |
| Yangi xodim/muharrir qo‘shish | Admin panel → Foydalanuvchilar | [03-ruxsatlar](03-ruxsatlar.md) |
| Bloklangan foydalanuvchini ochish | Foydalanuvchilar → «Blokdan chiqarish» | [11-muammolar](11-muammolar.md) |
| 2FA (ikki bosqichli tasdiq) yoqish/majburiy qilish | Profil; `REQUIRE_2FA_ROLES` | [03-ruxsatlar](03-ruxsatlar.md) |
| Fakultet adminini bitta fakultetga bog‘lash | Foydalanuvchi → «ruxsat doirasi» (`scope`) | [03-ruxsatlar](03-ruxsatlar.md) |
| Token turlari (JWT, API_TOKEN, xodim sessiyasi) | `apps/panel/jwt.py`, `apps/api/common.py` | [03-ruxsatlar](03-ruxsatlar.md) |

### API va Swagger

| Maqsad | Qayerda | Batafsil |
|---|---|---|
| API ni brauzerda sinash | http://localhost:8000/api/docs/ | [05-swagger](05-swagger.md) |
| Faqat o‘z roliga tegishli amallarni ko‘rish | Swagger → rol tanlash (`?role=editor`) | [05-swagger](05-swagger.md) |
| Admin API ga Swagger'dan kirish | `/api/cms/users/login` → token → **Authorize** | [05-swagger](05-swagger.md) |
| Sayt API shartnomasi (frontend ↔ backend) | `frontend/docs/openapi.yaml` | [05-swagger](05-swagger.md) |
| Barcha manzillar ro‘yxati | `docs/reference.md` → «Manzillar» | [reference](reference.md) |

### Testlar va sifat

| Maqsad | Buyruq | Batafsil |
|---|---|---|
| Hamma testlar (backend + frontend + admin) | `scripts/test.sh` (Windows: `scripts\test.ps1`) | [06-testlar](06-testlar.md) |
| Faqat backend, tez | `cd backend && python manage.py test --parallel --exclude-tag=slow` | [06-testlar](06-testlar.md) |
| Xavfsizlik testlari | `python manage.py test tests.security` | [04-xavfsizlik](04-xavfsizlik.md) |
| PostgreSQL bilan sinash | `TEST_DATABASE_URL=postgres://… python manage.py test` | [06-testlar](06-testlar.md) |
| Production sozlamalari to‘g‘rimi | `python manage.py check` | [04-xavfsizlik](04-xavfsizlik.md) |
| Zaif kutubxonalar | `pip-audit -r requirements.txt`, `npm audit` | [04-xavfsizlik](04-xavfsizlik.md) |

### Zaxira (backup)

| Maqsad | Buyruq | Batafsil |
|---|---|---|
| Hozir zaxira olish | `docker compose exec backend python manage.py backup` | [07-zaxira](07-zaxira.md) |
| Zaxiralar ro‘yxati va nima o‘chishi | `backup --list` / `backup --plan` | [07-zaxira](07-zaxira.md) |
| Katta o‘zgarish oldidan nusxani qadash | `backup --pin FAYL` | [07-zaxira](07-zaxira.md) |
| Eski sanadagi holatni topish va tiklash | `backup --find 2026-08-15` → `restore 2026-08-15 --yes` | [07-zaxira](07-zaxira.md) |
| Zaxira yangimi (monitoring) | `backup --status` | [07-zaxira](07-zaxira.md) |

### HEMIS, kesh, yuklama

| Maqsad | Qayerda | Batafsil |
|---|---|---|
| HEMIS ulash | `backend/.env` → `HEMIS_API_URL`, `HEMIS_API_TOKEN` | [08-hemis-kesh](08-hemis-kesh.md) |
| HEMIS oxirgi marta qachon yangilandi | Admin panel → Boshqaruv paneli (HEMIS kartasi) | [08-hemis-kesh](08-hemis-kesh.md) |
| HEMIS'ni qo‘lda yangilash | `python manage.py sync_hemis --force` | [08-hemis-kesh](08-hemis-kesh.md) |
| So‘rov cheklovlarini o‘zgartirish | `.env` → `THROTTLE_*` | [08-hemis-kesh](08-hemis-kesh.md) |
| Keshni tozalash | `python manage.py shell -c "from django.core.cache import cache; cache.clear()"` | [08-hemis-kesh](08-hemis-kesh.md) |

### Kod yozish

| Maqsad | Qayerda | Batafsil |
|---|---|---|
| Qaysi fayl nima qiladi | `docs/reference.md` → «Backend fayllar xaritasi» | [02-tuzilma](02-tuzilma.md) |
| Yangi kolleksiya, maydon, endpoint, til, rol qo‘shish | — | [12-qanday-qilaman](12-qanday-qilaman.md) |
| Frontend yoki admin sahifasi qo‘shish | `frontend/app/pages/`, `admin/src/pages/` | [09-front-admin](09-front-admin.md) |
| Sozlama (`.env`) nima qiladi | `docs/reference.md` → «Sozlamalar» | [reference](reference.md) |

### Serverga chiqarish

| Maqsad | Qayerda | Batafsil |
|---|---|---|
| Serverga chiqishdan oldin tekshiruv ro‘yxati | — | [10-server](10-server.md) |
| nginx sozlamasi (media, sarlavhalar) | — | [10-server](10-server.md) |
| Yangilash va orqaga qaytarish tartibi | — | [10-server](10-server.md) |

## Hujjatlar xaritasi

1. [01-boshlash](01-boshlash.md) — o‘rnatish, birinchi kirish, kundalik buyruqlar
2. [02-tuzilma](02-tuzilma.md) — papkalar, arxitektura, ma’lumot oqimi, kesh qatlamlari
3. [03-ruxsatlar](03-ruxsatlar.md) — rollar, kirish turlari, 2FA, ruxsatni qanday tekshirish
4. [04-xavfsizlik](04-xavfsizlik.md) — tahdid → himoya → kod → test, tekshiruvlar, hodisaga javob
5. [05-swagger](05-swagger.md) — Swagger, rol bo‘yicha ko‘rinish, shartnoma
6. [06-testlar](06-testlar.md) — testlarni ishga tushirish, xarita, CI
7. [07-zaxira](07-zaxira.md) — zaxira, tiklash, vaziyatlar
8. [08-hemis-kesh](08-hemis-kesh.md) — HEMIS, kechki vazifalar, kesh, yuklama himoyasi
9. [09-front-admin](09-front-admin.md) — sayt va admin panel kodi
10. [10-server](10-server.md) — serverga chiqish
11. [11-muammolar](11-muammolar.md) — xato → sabab → yechim
12. [12-qanday-qilaman](12-qanday-qilaman.md) — kodni kengaytirish retseptlari
13. [reference](reference.md) — **koddan avtomatik**: rollar jadvali, manzillar, buyruqlar, sozlamalar, testlar, fayllar xaritasi

Eski, chuqur hujjatlar: [`backend/README.md`](../backend/README.md) (HEMIS, xavfsizlik, fayllar), [`backend/tests/README.md`](../backend/tests/README.md), [`frontend/README.md`](../frontend/README.md).

## Bu hujjat qanday yangilanadi

- `docs/*.md` — qo‘lda yoziladi. Yangi qo‘llanma qo‘shsangiz: `NN-nom.md` (raqam tartibni belgilaydi) va yuqoridagi xaritaga qo‘shing.
- `docs/reference.md` va `docs/index.html` — **avtomatik**: `cd backend && python manage.py build_docs`.
- Hujjat eskirmasligi testlar bilan kafolatlanadi (`backend/tests/core/test_docs.py`): havolalar, `manage.py` buyruqlari va `backend/…` yo‘llari mavjudligi, `reference.md` kodga mosligi tekshiriladi. Kodni o‘zgartirib, `build_docs` ni ishga tushirishni unutsangiz — CI yiqiladi.
