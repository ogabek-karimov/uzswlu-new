# 6. Testlar

## Eng tez yo‘l

| Maqsad | Buyruq |
|---|---|
| **Hamma** testlar (backend + frontend + admin tur tekshiruvi) | `scripts/test.sh` · Windows: `.\scripts\test.ps1` |
| Tez to‘plam (sekinlarsiz) | `scripts/test.sh --fast` · `.\scripts\test.ps1 -Fast` |
| Faqat backend | `cd backend && python manage.py test --parallel` (≈ 30 s) |
| Backend, tez | `python manage.py test --parallel --exclude-tag=slow` (≈ 7 s) |
| Bitta paket / fayl / test | `python manage.py test tests.security` · `tests.security.test_files` · `tests.security.test_files.PdfTests.test_active_content_rejected` |
| Frontend (hammasi) | `cd frontend && npm test` = `test:last-good` (backend o‘chganda eski javob, media keshi) + `test:seo` (sitemap, robots, havolalar) + `test:pages` (har sahifada `useSeo`, `<img alt>`, 4 tilda kalitlar teng) |
| Admin (API qatlami + manba qoidalari) | `cd admin && npm test` (timeout, 401, HTML xato; `console.log`/`any` yo‘q, marshrutlar, ≤ 500 qator) |
| Admin (tur tekshiruvi + build) | `cd admin && npm run typecheck` · `npm run build` |

Testlar **hermetik**: `manage.py test` o‘zi `config.settings_test` ni oladi — `.env` o‘qilmaydi, baza xotiradagi SQLite, kesh jarayon ichida, `MEDIA_ROOT`/`PRIVATE_ROOT`/`BACKUP_DIR` vaqtinchalik papka (haqiqiy fayllarga tegilmaydi), avtomatik zaxira o‘chiq.

## PostgreSQL bilan

`/panel/stats` faqat PostgreSQL'da ishlaydi, shuning uchun CI ikkala bazada ham sinaydi.

```bash
cd backend
TEST_DATABASE_URL=postgres://uzswlu:parol@localhost:5432/uzswlu python manage.py test --parallel
```

Docker ichida: `requirements-dev.txt` (PyYAML, coverage, pip-audit) image'da yo‘q — avval `docker compose exec backend pip install -r requirements-dev.txt`.

## Qamrov (coverage)

```bash
cd backend && pip install -r requirements-dev.txt
coverage run manage.py test && coverage report --skip-empty --show-missing --include='apps/*'
```

## Test xaritasi

Har fayl nimani tekshirishi va nechta test borligi — avtomatik jadval: [reference → Backend testlari xaritasi](reference.md). Qisqacha:

| Papka | Nima |
|---|---|
| `backend/tests/api/` | ochiq API: shartnoma (`openapi.yaml`), oqimlar, Swagger to‘liqligi |
| `backend/tests/panel/` | admin API: har kolleksiya (o‘qish → PATCH → nusxa → o‘chirish), sahifalash, SPA so‘rovlari |
| `backend/tests/security/` | xavfsizlik: rol matritsasi, IDOR, JWT, 2FA, fayllar, hujum simulyatsiyasi, kesh bosimi |
| `backend/tests/hemis/` | HEMIS yuklama nazorati (jadval, pauza, circuit breaker, qulf) |
| `backend/tests/core/` | zaxira/tiklash/saqlash siyosati, **hujjat** (`test_docs.py`) |
| `frontend/scripts/test-*.mts` | «oxirgi yaxshi javob» va media keshi (Node, ramkasiz) |

`slow` tegli testlar (>2 s yoki juda ko‘p so‘rov): `--exclude-tag=slow` bilan o‘tkazib yuboriladi.

## Yangi test yozish

- Bo‘sh baza yetarli: `tests.support.Base` (2 foydalanuvchi, 2 fakultet, 2 kafedra — juda tez).
- Namunaviy ma’lumot kerak: `SeededTestCase` (sinf boshida bir marta; `self.superadmin` bor).
- Panelga kirish: `jwt_for('ed')` (Bearer sarlavhasi) yoki `self.client.force_login(user)`; so‘rov: `api('get', url, headers)`.
- Ko‘p login qilgan test cheklovga (429) tushsa — `@loose('login')`.
- Sekin sinfga `@tag('slow')` qo‘ying.
- Fayl testlarida namunalarni kodda yasang (`tests/security/test_files.py`: `pdf()`, `ooxml()`, `png()`).
- Bazaga yozuvchi, fayl yoki zaxirani tekshiradigan testda `TransactionTestCase` (`tests/core/test_backup.py` namunasi).
- `time.sleep` o‘rniga vaqtni boshqaring (`now=` parametri yoki `override_settings`).

Batafsil: [`backend/tests/README.md`](../backend/tests/README.md).

## CI (GitHub Actions)

`.github/workflows/ci.yml` — `azik` branchiga push va har pull request'da:

| Job | Nima qiladi |
|---|---|
| `backend` | `makemigrations --check` (migratsiya modelga mosmi), testlar + qamrov — **SQLite va PostgreSQL 16** matritsasida, `build_docs --check` (hujjat eskirmaganmi) |
| `frontend` | `npm ci`, `npm test`, `npm run build` |
| `admin` | `npm ci`, `npm test`, `npm run build` (`vue-tsc` + `vite build`) |
| `audit` | `pip-audit`, `npm audit` — ma’lumot uchun (yiqitmaydi) |

CI qizil bo‘lsa avval **qaysi job** yiqilganini ko‘ring: migratsiya → modelni o‘zgartirib `makemigrations` qilmagansiz; hujjat → `cd backend && python manage.py build_docs` va commit; tur xatosi → `cd admin && npm run typecheck`.
