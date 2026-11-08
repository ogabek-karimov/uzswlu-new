# Backend testlari

```
backend/tests/
├── support.py              umumiy yordamchilar: Base, SeededTestCase, jwt_for, api, loose
├── api/                    ochiq API
│   ├── test_contract.py      javoblar frontend/docs/openapi.yaml sxemasiga mos (4 til × barcha endpoint)   [slow]
│   ├── test_flows.py         sanoqlar, eski /api/site/*, API token, xodim kabineti, murojaat, statistika
│   └── openapi_check.py      sxema tekshiruvchi (test emas)
├── panel/                  admin panel API (/api/cms/*)
│   ├── test_collections.py   har kolleksiya: o'qish → PATCH → nusxa → o'chirish, globallar, versiyalar, sessiya   [slow]
│   ├── test_pagination.py    barcha sahifalar to'liq va takrorsiz; noto'g'ri limit/page                          [slow]
│   └── test_spa_queries.py   admin SPA yuboradigan murakkab where/sort so'rovlari
└── security/               xavfsizlik
    ├── test_access_control.py  IDOR, fakultet doirasi, postlar egasi
    ├── test_auth.py            parol, JWT bekor qilish, 2FA (TOTP), bloklash
    ├── test_jwt_roles.py       JWT va rollar
    ├── test_query_injection.py where/sort orqali parol xeshini topishga urinish
    ├── test_throttling_cache.py so'rov cheklovi va ommaviy kesh
    ├── test_production_checks.py production sozlama ogohlantirishlari
    └── test_files.py           fayl tekshiruvi, yopiq saqlash, yuklab olish sarlavhalari
```

## Ishga tushirish

```bash
cd backend
python manage.py test                          # hammasi (≈30 s)
python manage.py test --parallel               # parallel (≈15 s)
python manage.py test --exclude-tag=slow       # tez to'plam (≈7 s, parallel bilan)
python manage.py test tests.security           # bitta paket
python manage.py test tests.security.test_files.PdfTests.test_active_content_rejected   # bitta test
```

Hamma papkadagi testlar (backend + frontend + admin): `scripts/test.sh [--fast]` yoki Windows'da `.\scripts\test.ps1 [-Fast]`.

`manage.py test` avtomatik `config.settings_test` ni ishlatadi, shuning uchun testlar **hermetik**: `.env` o'qilmaydi,
baza — xotiradagi SQLite, kesh — jarayon ichida, `MEDIA_ROOT`/`PRIVATE_ROOT` — vaqtinchalik papka (haqiqiy fayllarga tegilmaydi),
parol xeshi tez. PostgreSQL bilan sinash: `TEST_DATABASE_URL=postgres://user:pass@localhost/db python manage.py test`
(`/panel/stats` faqat PostgreSQL'da 200 qaytaradi). Qamrov: `pip install -r requirements-dev.txt`, so'ng `coverage run manage.py test && coverage report`.

## Yangi test yozish

- Bo'sh baza yetarli bo'lsa — `tests.support.Base` (2 foydalanuvchi, 2 fakultet, 2 kafedra; juda tez).
- Demo ma'lumot kerak bo'lsa (shartnoma, sanoqlar, sahifalash) — `SeededTestCase` (seed sinf boshida bir marta, `self.superadmin` bor).
- Panelga kirish: `jwt_for('ed')` (Bearer sarlavhasi) yoki `self.client.force_login(user)`; so'rov: `api('get', url, headers)`.
- Login ko'p urinadigan test cheklovga (429) tushsa — `@loose('login')`.
- Sekin (>2 s) yoki juda ko'p so'rov qiladigan sinfga `@tag('slow')` qo'ying.
- Fayl yuklash testlarida namunalarni kodda yasang (`tests/security/test_files.py` dagi `pdf()`, `ooxml()`, `png()`) — tashqi fayl kerak emas.
- Testda `time.sleep` o'rniga vaqtni boshqaring (`now=` parametri yoki `override_settings`); tasodifiy qiymatga bog'liq shart yozmang.

## CI

`.github/workflows/ci.yml`: backend (SQLite va PostgreSQL 16), migratsiyalar modelga mosligi, qamrov hisoboti,
frontend (`test:last-good` + build), admin (`vue-tsc` + build), zaif bog'liqliklar (`pip-audit`, `npm audit` — ma'lumot uchun).
