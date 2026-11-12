# Avtomatik ma’lumotnoma

> ⚙️ **Bu fayl koddan avtomatik yig‘iladi** — qo‘lda tahrirlamang: `cd backend && python manage.py build_docs`.

Bu sahifa **koddan** yig‘iladi, shuning uchun doim haqiqatga mos: rollar, manzillar, buyruqlar, sozlamalar, testlar.

### Rol × kolleksiya jadvali

`R` o‘qish · `C` yaratish · `U` tahrirlash · `D` o‘chirish · `—` ruxsat yo‘q. Obyekt darajasidagi qo‘shimcha cheklovlar jadval ostida.

| Kolleksiya | `superadmin` | `editor` | `faculty` | `pages` | `sdg` |
|---|---|---|---|---|---|
| `activity` | R | — | — | — | — |
| `categories` | RCUD | R | R | R | R |
| `departments` | RCUD | R | RCU | R | R |
| `doc-categories` | RCUD | R | R | RCU | R |
| `documents` | RCUD | R | R | RCUD | R |
| `faculties` | RCUD | R | RU | R | R |
| `leaders` | RCUD | R | R | R | R |
| `login-events` | R | — | — | — | — |
| `media` | RCUD | RCU | RCU | RCU | RCU |
| `pages` | RCUD | R | R | RCUD | R |
| `posts` | RCUD | RCUD | RCUD | RCUD | R |
| `sdg-goals` | RCUD | R | R | R | RU |
| `slides` | RCUD | R | R | R | R |
| `staff-profiles` | RCUD | R | R | R | R |
| `users` | RCUD | RU | RU | RU | RU |
| `video-categories` | RCUD | R | R | RCU | R |
| `videos` | RCUD | R | R | RCUD | R |
| `home-banner` (global) | RU | R | R | R | R |
| `sdg-page` (global) | RU | R | R | R | RU |
| `settings` (global) | RU | R | R | R | R |
| `symbols` (global) | RU | R | R | R | R |
| `video-page` (global) | RU | R | R | RU | R |

**Obyekt darajasidagi qoidalar** (rol jadvalidan tashqari):

- `departments` · **create**: `faculty` faqat **o‘z fakultetiga** kafedra qo‘sha oladi.
- `departments` · **update**: `faculty` faqat **o‘z fakultetidagi** kafedrani o‘zgartiradi.
- `faculties` · **update**: `faculty` faqat **o‘z fakultetini** (`User.scope`) o‘zgartiradi; doirasi belgilanmagan bo‘lsa — hech narsani.
- `posts` · **update**: `faculty` va `pages` faqat **o‘zi yozgan** postni o‘zgartiradi; `superadmin` va `editor` — hammasini.
- `posts` · **delete**: `faculty` va `pages` faqat **o‘zi yozgan** postni o‘chiradi; `superadmin` va `editor` — hammasini.

### `manage.py` buyruqlari (loyihaniki)

Docker'da: `docker compose exec backend python manage.py <buyruq>`. Parametrlar: `python manage.py <buyruq> --help`.

| Buyruq | Nima qiladi | Fayl |
|---|---|---|
| `python manage.py backup` | Baza va yuklangan fayllarning zaxira nusxasini olish / tekshirish / ro‘yxati | `apps/core/management/commands/backup.py` |
| `python manage.py build_docs` | Qo‘llanmani yig‘ish: docs/reference.md (koddan avtomatik) va docs/index.html (qidiriladigan bitta fayl) | `apps/core/management/commands/build_docs.py` |
| `python manage.py import_payload` | Payload CMS bazasidagi ma’lumot va fayllarni shu backend’ga ko‘chiradi | `apps/core/management/commands/import_payload.py` |
| `python manage.py issue_staff_session` | Xodim kabineti uchun sessiya tokenini yaratadi | `apps/core/management/commands/issue_staff_session.py` |
| `python manage.py restore` | Zaxira nusxadan bazani va fayllarni tiklash | `apps/core/management/commands/restore.py` |
| `python manage.py run_nightly` | Kechki vazifalar: HEMIS sinxronlash, eski sessiya va yozuvlarni tozalash | `apps/core/management/commands/run_nightly.py` |
| `python manage.py seed_demo` | Boshlang‘ich ma’lumotlarni yuklaydi (bo‘sh bo‘limlarga) | `apps/core/management/commands/seed_demo.py` |
| `python manage.py sync_hemis` | HEMIS’dan xodimlar, bo‘limlar va sonlarni olib bazaga yozadi (kechki oynada) | `apps/hemis/management/commands/sync_hemis.py` |

### Sozlamalar (.env)

Fayllar: `backend/.env` (namuna: `backend/.env.example`), `.env.docker` (namuna: `.env.docker.example`, faqat PostgreSQL), `frontend/.env` (namuna: `frontend/.env.example`), ildiz `.env` (ixtiyoriy: portlar).

#### Backend — `backend/.env.example`

| O‘zgaruvchi | Namuna | Izoh | Holat |
|---|---|---|---|
| `DEBUG` | `true` | Nusxa oling: backend/.env (parol va kalitlarni o'zgartiring!) |  |
| `SECRET_KEY` | `change-me-uzun-tasodifiy-satr` |  |  |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` |  |  |
| `DATABASE_URL` | `postgres://uzswlu:bu-yerga-kuchli-parol@db:5432/uzswlu` | Baza: .env.docker dagi foydalanuvchi va parol bilan bir xil |  |
| `PUBLIC_SERVER_URL` | `http://localhost:8000` |  |  |
| `TRUSTED_ORIGINS` | `http://localhost:5173,http://localhost:5174,http://localhost:3000` | Cookie bilan so'rov yubora oladigan manzillar: Vue admin panel va sayt |  |
| `ADMIN_PANEL_URL` | `http://localhost:5173` |  |  |
| `SITE_URL` | `http://localhost:3000` |  |  |
| `API_TOKEN` | *(bo‘sh)* | Bo'sh bo'lsa token tekshirilmaydi; frontendda NUXT_API_TOKEN bilan bir xil bo'lsin |  |
| `SERVE_MEDIA` | `true` |  |  |
| `HIDE_UNTRANSLATED_POSTS` | `true` |  |  |
| `API_DOCS_PUBLIC` | `true` | Productionda: uzun tasodifiy qiymat (python -c "import secrets; print(secrets.token_urlsafe(32))"). Almashtirish: API_TOKEN=yangi,eski Swagger (/api/docs/) hamma uchun ochiqmi (productionda false — faqat admin panelga kirganlar) |  |
| `SUPERADMIN_USERNAME` | `superadmin` | Birinchi ishga tushishda yaratiladigan superadmin |  |
| `SUPERADMIN_PASSWORD` | `change-me-please` |  |  |
| `HEMIS_API_URL` | *(bo‘sh)* | HEMIS (universitet IT bo'limi beradi). Bo'sh bo'lsa — namuna ma'lumot ishlatiladi |  |
| `HEMIS_API_TOKEN` | *(bo‘sh)* |  |  |
| `HEMIS_FACULTY_TYPES` | `11` |  |  |
| `HEMIS_CHAIR_TYPES` | `12` |  |  |
| `HEMIS_OAUTH_URL` | *(bo‘sh)* |  |  |
| `HEMIS_OAUTH_CLIENT_ID` | *(bo‘sh)* |  |  |
| `HEMIS_OAUTH_CLIENT_SECRET` | *(bo‘sh)* |  |  |
| `PAYLOAD_DATABASE_URL` | *(bo‘sh)* | Payload CMS'dan ko'chirish (bir marta): python manage.py import_payload --replace |  |
| `PAYLOAD_MEDIA_URL` | *(bo‘sh)* |  |  |
| `JWT_TTL_SECONDS` | `28800` | Admin panel JWT amal qilish muddati (soniya), sukut — 8 soat |  |
| `SWAGGER_THEME` | `modern` | Swagger sahifasi dizayni: modern (sukut: yumshoq ranglar, sarlavhada qo‘llanma) yoki classic |  |
| `NUM_PROXIES` | `0` | Backend oldida nechta proksi (nginx, Cloudflare…) bo'lsa shuncha. 0 bo'lsa X-Forwarded-For ishonchsiz deb hisoblanadi (so'rov cheklovi REMOTE_ADDR bo'yicha). Nginx orqasida — 1, Cloudflare + nginx — 2. |  |
| `THROTTLE_LOGIN` | `10/min` | So'rov cheklovlari (son/vaqt: sec, min, hour, day). Bo'sh qoldirsangiz — sukut qiymatlar |  |
| `THROTTLE_PUBLIC` | `300/min` |  |  |
| `THROTTLE_SEARCH` | `40/min` |  |  |
| `THROTTLE_APPEALS` | `20/hour` |  |  |
| `THROTTLE_HEMIS_AUTH` | `20/min` |  |  |
| `PUBLIC_CACHE_SECONDS` | `60` | Ochiq GET javoblari keshi (soniya, 0 — o'chirilgan). Admin panelda o'zgarish bo'lsa kesh darhol yangilanadi |  |
| `HEMIS_CACHE_SECONDS` | `300` | HEMIS nusxasini bazadan qayta o'qish oralig'i (soniya) va sinxronlashda sahifalar orasidagi pauza |  |
| `HEMIS_REQUEST_DELAY` | `0.2` |  |  |
| `HEMIS_OAUTH_TIMEOUT` | `8` |  |  |
| `ADMIN_MAX_LIMIT` | `5000` | Admin ro'yxatida bir so'rovda ko'pi bilan nechta yozuv |  |
| `REDIS_URL` | *(bo‘sh)* | Bir nechta server/jarayon bo'lsa umumiy kesh (so'rov cheklovi hisobi uchun); bo'sh bo'lsa fayl keshi |  |
| `WEB_CONCURRENCY` | `3` | Gunicorn: jarayonlar, oqimlar va so'rov vaqti chegarasi |  |
| `WEB_THREADS` | `2` |  |  |
| `WEB_TIMEOUT` | `30` |  |  |
| `REQUIRE_2FA_ROLES` | *(bo‘sh)* | Ikki bosqichli tasdiq (2FA, Google/Microsoft Authenticator) majburiy rollar, vergul bilan. Bo'sh — hamma uchun ixtiyoriy (Profil bo'limida yoqiladi) |  |
| `BACKUP_ENABLED` | `true` | Kechasi avtomatik: baza + yuklangan fayllar → BACKUP_DIR/uzswlu-YYYYMMDD-HHMMSS.tar.gz. Serverda BACKUP_DIR alohida diskda bo'lsin. |  |
| `BACKUP_DIR` | `/app/backups` |  | ixtiyoriy (izohda) |
| `BACKUP_COPY_TO` | *(bo‘sh)* | Ikkinchi joyga ham nusxa (boshqa disk yoki ulangan tarmoq papkasi). Productionda tavsiya etiladi |  |
| `BACKUP_KEEP_DAYS` | `14` | Saqlash siyosati: oxirgi 14 kun — hammasi; keyin har haftadan bittadan (8 hafta), har oydan bittadan (12 oy), har yildan bittadan (0 — abadiy) |  |
| `BACKUP_KEEP_WEEKS` | `8` |  |  |
| `BACKUP_KEEP_MONTHS` | `12` |  |  |
| `BACKUP_KEEP_YEARS` | `0` |  |  |
| `BACKUP_KEEP_MIN` | `3` |  |  |
| `BACKUP_DB_FORMAT` | `auto` | auto: PostgreSQL'da pg_dump, SQLite'da ichki zaxira; json — ko'chma format (bazadan bazaga o'tkazish uchun) |  |
| `PRIVATE_ROOT` | `/app/private` | Yopiq fayllar (fuqarolar murojaati ilovalari) — ochiq /media dan tashqarida. Serverda alohida volume. | ixtiyoriy (izohda) |

#### PostgreSQL — `.env.docker.example`

| O‘zgaruvchi | Namuna | Izoh | Holat |
|---|---|---|---|
| `POSTGRES_USER` | `uzswlu` | PostgreSQL (docker-compose) — nusxa oling: .env.docker |  |
| `POSTGRES_PASSWORD` | `bu-yerga-kuchli-parol` |  |  |
| `POSTGRES_DB` | `uzswlu` |  |  |

#### Frontend — `frontend/.env.example`

| O‘zgaruvchi | Namuna | Izoh | Holat |
|---|---|---|---|
| `NUXT_CMS_BASE` | `http://localhost:8000/api/site` | Nusxa oling: frontend/.env O'zimizning CMS (Docker'dagi backend) ochiq API'si |  |
| `NUXT_STALE_IF_ERROR_SECONDS` | `10800` | Backend o'chib qolsa, sayt oxirgi muvaffaqiyatli javobni shuncha soniya ko'rsatadi (standart 10800 = 3 soat; 0 — o'chirilgan) | ixtiyoriy (izohda) |
| `NUXT_BACKEND_COOLDOWN_SECONDS` | `15` | Backend yiqilgandan keyin shuncha soniya unga bormaydi (standart 15) | ixtiyoriy (izohda) |
| `NUXT_MEDIA_PUBLIC_ORIGIN` | `http://localhost:8000` | Rasm/fayllar sayt orqali beriladi (/media/...) va keshlanadi. Backendning brauzerga ko'rinadigan manzili (backend/.env dagi PUBLIC_SERVER_URL): | ixtiyoriy (izohda) |
| `NUXT_PUBLIC_SITE_URL` | `https://uzswlu.uz` | Saytning ochiq manzili — canonical, hreflang, sitemap.xml, robots.txt va ijtimoiy tarmoq preview'i shundan yasaladi. Productionda ALBATTA to'ldiring. Bo'sh bo'lsa so'rov kelgan manzil olinadi (nginx Host va X-Forwarded-Proto ni uzatishi shart). | ixtiyoriy (izohda) |

#### Namunada ko‘rsatilmagan, lekin `settings.py` o‘qiydigan o‘zgaruvchilar

Standart qiymat bilan ishlaydi; kerak bo‘lsa `backend/.env` ga qo‘shing.

| O‘zgaruvchi | Standart | Qayerda |
|---|---|---|
| `BACKUP_MAX_AGE_HOURS` | `'36'` | `backend/config/settings.py:283` |
| `BACKUP_MEDIA` | `True` | `backend/config/settings.py:281` |
| `CACHE_DIR` | `'/tmp/uzswlu-cache'` | `backend/config/settings.py:202` |
| `COOKIE_SECURE` | `True` | `backend/config/settings.py:188` |
| `HEMIS_CLIENT` | `'apps.hemis.cache.CachedHemis' if HEMIS_API_URL else 'apps.hemis.snapshot.SnapshotHemis'` | `backend/config/settings.py:284` |
| `HEMIS_MAX_CONSECUTIVE_FAILURES` | `'5'` | `backend/config/settings.py:266` |
| `HEMIS_MAX_REQUESTS` | `'3000'` | `backend/config/settings.py:265` |
| `HEMIS_OAUTH_AUTHORIZE_PATH` | `'/oauth/authorize'` | `backend/config/settings.py:289` |
| `HEMIS_OAUTH_GLOBAL_PER_MIN` | `'120'` | `backend/config/settings.py:267` |
| `HEMIS_OAUTH_TOKEN_PATH` | `'/oauth/access-token'` | `backend/config/settings.py:290` |
| `HEMIS_OAUTH_USER_PATH` | `'/oauth/api/user'` | `backend/config/settings.py:291` |
| `HEMIS_SNAPSHOT` | `str(BASE_DIR / 'seed_data' / 'hemis-snapshot.json')` | `backend/config/settings.py:318` |
| `HEMIS_SYNC_AT` | `'02:30'` | `backend/config/settings.py:263` |
| `HEMIS_SYNC_JITTER_MINUTES` | `'20'` | `backend/config/settings.py:264` |
| `HEMIS_SYNC_WINDOW` | `'01:00-05:00'` | `backend/config/settings.py:262` |
| `HEMIS_TIMEOUT` | `'20'` | `backend/config/settings.py:258` |
| `HIT_RETENTION_DAYS` | `'730'` | `backend/config/settings.py:268` |
| `HSTS_SECONDS` | `'31536000'` | `backend/config/settings.py:191` |
| `LOGIN_EVENT_RETENTION_DAYS` | `'365'` | `backend/config/settings.py:269` |
| `LOG_LEVEL` | `'INFO'` | `backend/config/settings.py:324` |
| `SITE_PURGE_TOKEN` | `''` | `backend/config/settings.py:252` |
| `SITE_PURGE_URL` | `''` | `backend/config/settings.py:251` |
| `STAFF_SESSION_COOKIE` | `'session'` | `backend/config/settings.py:246` |
| `STAFF_SESSION_TTL_HOURS` | `'12'` | `backend/config/settings.py:247` |
| `THROTTLE_CABINET` | `'180/min'` | `backend/config/settings.py:228` |
| `THROTTLE_CABINET_UPLOAD` | `'30/hour'` | `backend/config/settings.py:229` |
| `THROTTLE_DOCS` | `'60/min'` | `backend/config/settings.py:232` |
| `THROTTLE_HIT` | `'240/min'` | `backend/config/settings.py:231` |
| `THROTTLE_OPEN` | `'1200/min'` | `backend/config/settings.py:222` |
| `THROTTLE_PANEL_READ` | `'1200/min'` | `backend/config/settings.py:226` |
| `THROTTLE_PANEL_WRITE` | `'180/min'` | `backend/config/settings.py:227` |

### Production tekshiruvlari (`python manage.py check`)

DEBUG o‘chiq bo‘lganda ishga tushishda chiqadi (Docker'da `docker compose logs backend`). Hammasi yo‘qolishi kerak.

| Kod | Nima noto‘g‘ri | Qanday tuzatiladi |
|---|---|---|
| `uzswlu.W001` | API_TOKEN bo‘sh: ochiq API tokensiz hamma uchun ochiq. | backend/.env da uzun tasodifiy API_TOKEN belgilang (frontendda NUXT_API_TOKEN bilan bir xil). |
| `uzswlu.W002` | API_TOKEN 24 belgidan qisqa. | python -c "import secrets; print(secrets.token_urlsafe(32))" |
| `uzswlu.W003` | SECRET_KEY qisqa yoki taxminiy. | Kamida 50 belgili tasodifiy qiymat qo‘ying: JWT va sessiyalar shunga tayanadi. |
| `uzswlu.W004` | ALLOWED_HOSTS da "*" bor. | Faqat o‘z domeningizni yozing. |
| `uzswlu.W005` | NUM_PROXIES=0: so‘rov cheklovi REMOTE_ADDR bo‘yicha ishlaydi. | Nginx/Cloudflare ortida bo‘lsangiz NUM_PROXIES=1 (yoki 2) qo‘ying, aks holda hamma foydalanuvchi bitta IP ko‘rinadi. |
| `uzswlu.W006` | API_DOCS_PUBLIC=true: Swagger productionda hamma uchun ochiq. | API_DOCS_PUBLIC=false qiling — hujjat faqat admin panelga kirganlarga ko‘rinadi. |
| `uzswlu.W007` | TRUSTED_ORIGINS da localhost bor: u manzillardan cookie/token bilan so‘rov yuborish mumkin. | Productionda faqat admin panel va sayt domenlarini yozing: TRUSTED_ORIGINS=https://admin.sizning.uz,https://sizning.uz |
| `uzswlu.W008` | BACKUP_ENABLED=0: avtomatik zaxira nusxa o‘chirilgan. | Zaxirasiz server — bitta disk buzilishi hamma ma’lumotni yo‘qotadi. BACKUP_ENABLED=1 qiling. |
| `uzswlu.W009` | BACKUP_COPY_TO bo‘sh: zaxira faqat shu serverning o‘zida saqlanadi. | Disk buzilsa zaxira ham yo‘qoladi. BACKUP_COPY_TO ga boshqa disk/ulangan tarmoq papkasini yozing yoki backups/ papkasini tashqariga (rsync/rclone) ko‘chiring. |

### Manzillar (URL xaritasi)

Batafsil parametr va javoblar — Swagger: `http://localhost:8000/api/docs/`. Pastda: manzil → view → fayl → so‘rov cheklovi doirasi (`THROTTLE_*`).

#### Ochiq sayt API (`/api/…`)

| Manzil | View | Fayl | Cheklov |
|---|---|---|---|
| `/api/admission` | `AdmissionView` | `apps/api/views.py` | `public` |
| `/api/appeals` | `AppealView` | `apps/api/views.py` | `appeals` |
| `/api/contact` | `ContactView` | `apps/api/views.py` | `public` |
| `/api/documents/<int:pk>/file` | `DocumentFileView` | `apps/api/views.py` | `open` |
| `/api/documents` | `DocumentsView` | `apps/api/views.py` | `public` |
| `/api/events` | `EventsView` | `apps/api/views.py` | `public` |
| `/api/faculties/<slug:slug>` | `FacultyDetailView` | `apps/api/views.py` | `public` |
| `/api/faculties` | `FacultyListView` | `apps/api/views.py` | `public` |
| `/api/hit` | `HitView` | `apps/api/views.py` | `hit` |
| `/api/home` | `HomeView` | `apps/api/views.py` | `public` |
| `/api/leadership` | `LeadershipView` | `apps/api/views.py` | `public` |
| `/api/me/avatar` | `MeAvatarView` | `apps/api/views_staff.py` | `cabinet-upload` |
| `/api/me/documents/<str:section>/<str:pk>` | `MeDocumentDetailView` | `apps/api/views_staff.py` | `cabinet` |
| `/api/me/documents/<str:section>` | `MeDocumentsView` | `apps/api/views_staff.py` | `cabinet` |
| `/api/me` | `MeView` | `apps/api/views_staff.py` | `cabinet` |
| `/api/pages/<slug:slug>` | `PageView` | `apps/api/views.py` | `public` |
| `/api/posts/<str:type>/<str:slug>` | `PostDetailView` | `apps/api/views.py` | `public` |
| `/api/posts` | `PostListView` | `apps/api/views.py` | `public` |
| `/api/programs` | `ProgramsView` | `apps/api/views.py` | `public` |
| `/api/sdg/<int:n>` | `SdgGoalView` | `apps/api/views.py` | `public` |
| `/api/sdg` | `SdgOverviewView` | `apps/api/views.py` | `public` |
| `/api/search` | `SearchView` | `apps/api/views.py` | `search` |
| `/api/site` | `SiteView` | `apps/api/views.py` | `public` |
| `/api/staff/<str:pk>` | `StaffDetailView` | `apps/api/views_staff.py` | `public` |
| `/api/staff` | `StaffListView` | `apps/api/views_staff.py` | `public` |
| `/api/videos` | `VideosView` | `apps/api/views.py` | `public` |

#### Payload bilan mos (`/api/site/…`)

| Manzil | View | Fayl | Cheklov |
|---|---|---|---|
| `/api/site/documents/<int:pk>/file` | `DocumentFileView` | `apps/api/views.py` | `open` |
| `/api/site/documents` | `DocumentsView` | `apps/api/views.py` | `public` |
| `/api/site/events` | `EventsView` | `apps/api/views.py` | `public` |
| `/api/site/faculties/<slug:slug>` | `FacultyDetailView` | `apps/api/views.py` | `public` |
| `/api/site/faculties` | `FacultyListView` | `apps/api/views.py` | `public` |
| `/api/site/hit` | `HitView` | `apps/api/views.py` | `hit` |
| `/api/site/index` | `PostIndexView` | `apps/api/views.py` | `public` |
| `/api/site/latest` | `LatestView` | `apps/api/views.py` | `public` |
| `/api/site/leadership` | `LeadershipView` | `apps/api/views.py` | `public` |
| `/api/site/menu` | `MenuView` | `apps/api/views.py` | `public` |
| `/api/site/pages/<slug:slug>` | `PageView` | `apps/api/views.py` | `public` |
| `/api/site/posts/<str:type>/<str:slug>` | `PostDetailView` | `apps/api/views.py` | `public` |
| `/api/site/posts` | `PostListView` | `apps/api/views.py` | `public` |
| `/api/site/sdg-goals` | `SdgGoalsView` | `apps/api/views.py` | `public` |
| `/api/site/sdg/<int:n>` | `SdgGoalView` | `apps/api/views.py` | `public` |
| `/api/site/settings` | `SettingsView` | `apps/api/views.py` | `public` |
| `/api/site/slides` | `SlidesView` | `apps/api/views.py` | `public` |
| `/api/site/staff-hidden` | `StaffHiddenView` | `apps/api/views_staff.py` | `public` |
| `/api/site/staff/<str:pk>` | `StaffOverlayView` | `apps/api/views_staff.py` | `public` |
| `/api/site/symbols` | `SymbolsView` | `apps/api/views.py` | `public` |
| `/api/site/videos` | `VideosView` | `apps/api/views.py` | `public` |

#### Admin panel (`/api/cms/…`)

| Manzil | View | Fayl | Cheklov |
|---|---|---|---|
| `/api/cms/<slug:slug>/<int:pk>` | `DocView` | `apps/panel/views.py` |  |
| `/api/cms/<slug:slug>/count` | `CollectionCountView` | `apps/panel/views.py` |  |
| `/api/cms/<slug:slug>/versions/<int:vid>` | `VersionsView` | `apps/panel/views.py` |  |
| `/api/cms/<slug:slug>/versions` | `VersionsView` | `apps/panel/views.py` |  |
| `/api/cms/<slug:slug>` | `CollectionView` | `apps/panel/views.py` |  |
| `/api/cms/globals/<slug:slug>/versions/<int:vid>` | `GlobalVersionsView` | `apps/panel/views.py` |  |
| `/api/cms/globals/<slug:slug>/versions` | `GlobalVersionsView` | `apps/panel/views.py` |  |
| `/api/cms/globals/<slug:slug>` | `GlobalView` | `apps/panel/views.py` |  |
| `/api/cms/panel/hemis` | `HemisView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/media-stats` | `MediaStatsView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/media-usage/<int:pk>` | `MediaUsageView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/media-used` | `MediaUsedView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/overview` | `OverviewView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/sdg-counts` | `SdgCountsView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/stats` | `StatsView` | `apps/panel/dashboard.py` |  |
| `/api/cms/panel/youtube` | `YoutubeView` | `apps/panel/dashboard.py` |  |
| `/api/cms/private/<path:name>` | `PrivateFileView` | `apps/panel/views.py` | `panel-read` |
| `/api/cms/users/2fa/disable` | `DisableView` | `apps/panel/twofactor.py` | `login` |
| `/api/cms/users/2fa/enable` | `EnableView` | `apps/panel/twofactor.py` | `login` |
| `/api/cms/users/2fa/recovery` | `RecoveryView` | `apps/panel/twofactor.py` | `login` |
| `/api/cms/users/2fa/reset` | `ResetView` | `apps/panel/twofactor.py` | `login` |
| `/api/cms/users/2fa/setup` | `SetupView` | `apps/panel/twofactor.py` | `login` |
| `/api/cms/users/login/2fa` | `LoginTwoFactorView` | `apps/panel/twofactor.py` | `login` |
| `/api/cms/users/login` | `LoginView` | `apps/panel/auth.py` | `login` |
| `/api/cms/users/logout` | `LogoutView` | `apps/panel/auth.py` |  |
| `/api/cms/users/me` | `MeView` | `apps/panel/auth.py` |  |
| `/api/cms/users/refresh-token` | `RefreshTokenView` | `apps/panel/auth.py` | `login` |
| `/api/cms/users/unlock` | `UnlockView` | `apps/panel/auth.py` |  |

#### HEMIS kirish (`/api/auth/hemis/…`)

| Manzil | View | Fayl | Cheklov |
|---|---|---|---|
| `/api/auth/hemis/callback` | `CallbackView` | `apps/hemis/views.py` | `hemis-auth` |
| `/api/auth/hemis/login` | `LoginView` | `apps/hemis/views.py` | `hemis-auth` |
| `/api/auth/hemis/status` | `StatusView` | `apps/hemis/views.py` | `open` |

#### Boshqa

| Manzil | View | Fayl | Cheklov |
|---|---|---|---|
| `/` | `RedirectView` | `django/views/generic/base.py` |  |
| `/api/docs/` | `SwaggerView` | `config/urls.py` | `docs` |
| `/api/media/file/<path:name>` | `MediaFileCompat` | `apps/panel/views.py` | `open` |
| `/api/redoc/` | `RedocView` | `config/urls.py` | `docs` |
| `/api/schema/` | `SchemaView` | `config/urls.py` | `docs` |
| `/healthz` | `healthz` | `config/urls.py` |  |

### Admin panel sahifalari

Marshrut → fayl → kim ko‘radi (`admin/src/router.ts`; server tomonidagi ruxsat alohida — yuqoridagi jadval).

| Manzil | Fayl | Rollar |
|---|---|---|
| `//kirish` | `admin/src/pages/LoginPage.vue` | hamma kirgan xodim |
| `/` | `admin/src/pages/DashboardPage.vue` | hamma kirgan xodim |
| `/postlar/:type(news\|announcements\|events)` | `admin/src/pages/PostsPage.vue` | `superadmin`, `editor`, `faculty`, `pages` |
| `/postlar/:type(news\|announcements\|events)/yangi` | `admin/src/pages/PostEditPage.vue` | `superadmin`, `editor`, `faculty`, `pages` |
| `/postlar/:type(news\|announcements\|events)/:id(\\d+)` | `admin/src/pages/PostEditPage.vue` | `superadmin`, `editor`, `faculty`, `pages` |
| `/foydalanuvchilar` | `admin/src/pages/UsersPage.vue` | faqat `superadmin` |
| `/kirish-tarixi` | `admin/src/pages/LoginHistoryPage.vue` | faqat `superadmin` |
| `/faollik` | `admin/src/pages/ActivityPage.vue` | faqat `superadmin` |
| `/sozlamalar` | `admin/src/pages/SettingsPage.vue` | faqat `superadmin` |
| `/profil` | `admin/src/pages/ProfilePage.vue` | hamma kirgan xodim |
| `/karusel` | `admin/src/pages/CarouselPage.vue` | `superadmin` |
| `/media` | `admin/src/pages/MediaPage.vue` | hamma kirgan xodim |
| `/hujjatlar` | `admin/src/pages/DocumentsPage.vue` | `superadmin`, `pages` |
| `/video` | `admin/src/pages/VideosPage.vue` | `superadmin`, `pages` |
| `/rahbariyat` | `admin/src/pages/LeadersPage.vue` | `superadmin` |
| `/ramzlar` | `admin/src/pages/SymbolsPage.vue` | `superadmin` |
| `/fakultetlar` | `admin/src/pages/FacultiesPage.vue` | `superadmin`, `faculty` |
| `/kafedralar` | `admin/src/pages/DepartmentsPage.vue` | `superadmin`, `faculty` |
| `/xodimlar` | `admin/src/pages/StaffPage.vue` | `superadmin` |
| `/brm` | `admin/src/pages/BrmPage.vue` | `superadmin`, `sdg` |
| `/sahifalar` | `admin/src/pages/PagesPage.vue` | `superadmin`, `pages` |
| `/statistika` | `admin/src/pages/StatsPage.vue` | faqat `superadmin` |

### Frontend (Nuxt)

#### Sahifalar (til prefiksi: `/ru`, `/en`, `/zh`; o‘zbekcha — prefikssiz)

| Marshrut | Fayl |
|---|---|
| `/:...slug` | `frontend/app/pages/[...slug].vue` |
| `/aloqa` | `frontend/app/pages/aloqa.vue` |
| `/announcements/:slug` | `frontend/app/pages/announcements/[slug].vue` |
| `/announcements` | `frontend/app/pages/announcements/index.vue` |
| `/bakalavriat` | `frontend/app/pages/bakalavriat.vue` |
| `/brm` | `frontend/app/pages/brm/index.vue` |
| `/brm-:slug` | `frontend/app/pages/brm-[slug].vue` |
| `/dashboard` | `frontend/app/pages/dashboard.vue` |
| `/events/:slug` | `frontend/app/pages/events/[slug].vue` |
| `/events` | `frontend/app/pages/events/index.vue` |
| `/faculty/:slug` | `frontend/app/pages/faculty/[slug].vue` |
| `/fakultetlar-va-kafedralar` | `frontend/app/pages/fakultetlar-va-kafedralar.vue` |
| `/` | `frontend/app/pages/index.vue` |
| `/magistratura` | `frontend/app/pages/magistratura.vue` |
| `/meyoriy-hujjatlar` | `frontend/app/pages/meyoriy-hujjatlar.vue` |
| `/news/:slug` | `frontend/app/pages/news/[slug].vue` |
| `/qabul-20262027` | `frontend/app/pages/qabul-20262027.vue` |
| `/rektorat` | `frontend/app/pages/rektorat.vue` |
| `/search` | `frontend/app/pages/search.vue` |
| `/staff` | `frontend/app/pages/staff/index.vue` |
| `/teacher/:id` | `frontend/app/pages/teacher/[id].vue` |
| `/video-darsliklar` | `frontend/app/pages/video-darsliklar.vue` |
| `/yangiliklar` | `frontend/app/pages/yangiliklar.vue` |

#### Nuxt server qatlami (brauzer → shu yerga → backend)

| Manzil | Fayl |
|---|---|
| `GET /api/admission` | `frontend/server/api/admission.get.ts` |
| `POST /api/appeals` | `frontend/server/api/appeals.post.ts` |
| `GET /api/contact` | `frontend/server/api/contact.get.ts` |
| `GET /api/documents` | `frontend/server/api/documents.get.ts` |
| `GET /api/events` | `frontend/server/api/events.get.ts` |
| `GET /api/faculties/:slug` | `frontend/server/api/faculties/[slug].get.ts` |
| `GET /api/faculties` | `frontend/server/api/faculties/index.get.ts` |
| `POST /api/hit` | `frontend/server/api/hit.post.ts` |
| `GET /api/home` | `frontend/server/api/home.get.ts` |
| `GET /api/leadership` | `frontend/server/api/leadership.get.ts` |
| `DELETE /api/me/avatar` | `frontend/server/api/me/avatar.delete.ts` |
| `POST /api/me/avatar` | `frontend/server/api/me/avatar.post.ts` |
| `DELETE /api/me/documents/:section/:id` | `frontend/server/api/me/documents/[section]/[id].delete.ts` |
| `GET /api/me/documents/:section` | `frontend/server/api/me/documents/[section].get.ts` |
| `POST /api/me/documents/:section` | `frontend/server/api/me/documents/[section].post.ts` |
| `GET /api/me` | `frontend/server/api/me/index.get.ts` |
| `PATCH /api/me` | `frontend/server/api/me/index.patch.ts` |
| `GET /api/pages/:slug` | `frontend/server/api/pages/[slug].get.ts` |
| `GET /api/posts/:type/:slug` | `frontend/server/api/posts/[type]/[slug].get.ts` |
| `GET /api/posts` | `frontend/server/api/posts/index.get.ts` |
| `GET /api/programs` | `frontend/server/api/programs.get.ts` |
| `GET /api/sdg/:n` | `frontend/server/api/sdg/[n].get.ts` |
| `GET /api/sdg` | `frontend/server/api/sdg/index.get.ts` |
| `GET /api/search` | `frontend/server/api/search.get.ts` |
| `GET /api/site` | `frontend/server/api/site.get.ts` |
| `GET /api/staff/:id` | `frontend/server/api/staff/[id].get.ts` |
| `GET /api/staff` | `frontend/server/api/staff/index.get.ts` |
| `GET /api/videos` | `frontend/server/api/videos.get.ts` |

### Backend fayllar xaritasi (qaysi fayl nima qiladi)

Har faylning boshidagi izohdan olinadi.

| Fayl | Vazifasi |
|---|---|
| `backend/apps/accounts/backends.py` | Payload'dan ko'chirilgan eski parollar bilan kirish (authenticate) ham ishlasin. |
| `backend/apps/accounts/hashers.py` | Payload CMS'dan ko'chirilgan foydalanuvchilarning parollari (pbkdf2-sha256, 25000 marta, 512 bayt). |
| `backend/apps/accounts/models.py` | — |
| `backend/apps/api/builders.py` | Model → API shakli (frontend/docs/openapi.yaml). Hamma matnli maydon so'ralgan tilda, bo'lmasa o'zbekcha. |
| `backend/apps/api/builders_site.py` | Ochiq sayt API'si javoblarini yig'ish (frontend/docs/openapi.yaml shartnomasi). |
| `backend/apps/api/builders_staff.py` | Xodimlar: ommaviy ro'yxat/profil (HEMIS + saytdagi qo'shimcha ma'lumot) va xodim kabineti. |
| `backend/apps/api/common.py` | Ochiq API uchun umumiy yordamchilar: til, rasm/fayl manzillari, biriktirmalar, token tekshiruvi. |
| `backend/apps/api/hits.py` | Sayt statistikasi — cookie'siz va shaxsiy ma'lumotsiz (Umami usulida). |
| `backend/apps/api/schema.py` | Swagger: ochiq API ko'rinishlari serializer'siz yozilgan — javob umumiy JSON obyekt sifatida ko'rsatiladi, teglar manzildan. |
| `backend/apps/api/staff_auth.py` | Xodim kabineti autentifikatsiyasi: HEMIS (my.gov) orqali kirgan xodimning sessiyasi. |
| `backend/apps/api/swagger.py` | Swagger: ochiq sayt API'sining aniq tavsifi `frontend/docs/openapi.yaml` shartnomasidan olinadi. |
| `backend/apps/api/swagger_fields.py` | Admin panel (`/api/cms/*`) sxemalari: kolleksiya kodidan avtomatik olinadi — qo'lda yozilgan ro'yxat yo'q. |
| `backend/apps/api/urls.py` | API manzillari. Asosiy shartnoma — frontend/docs/openapi.yaml (`/api/home`, `/api/posts` …). |
| `backend/apps/api/views.py` | Ochiq sayt API'si (frontend/docs/openapi.yaml). Hamma javob `?lang=uz\|ru\|en\|zh` bo'yicha. |
| `backend/apps/api/views_staff.py` | Xodimlar (ommaviy) va xodim kabineti (/me — faqat HEMIS orqali kirgan xodim). |
| `backend/apps/content/models.py` | — |
| `backend/apps/core/activity.py` | Faollik jurnali va sayt keshini yangilash. |
| `backend/apps/core/backup.py` | Zaxira nusxa (backup) va tiklash — faqat Python, cron/tashqi dastur shart emas (PostgreSQL uchun `pg_dump` bo'lsa u ishlatiladi). |
| `backend/apps/core/checks.py` | Ishga tushganda xavfsizlik sozlamalarini tekshiradi (`manage.py check`, gunicorn/Docker ishga tushishida chiqadi). |
| `backend/apps/core/docsgen.py` | Loyiha qo'llanmasi (docs/) generatori — faqat Python. |
| `backend/apps/core/fields.py` | 4 tilli maydon: { "uz": "...", "ru": "...", "en": "...", "zh": "..." } (JSON). |
| `backend/apps/core/filesafe.py` | Yuklangan fayllarni chuqur tekshirish va tozalash — faqat Python (Pillow + standart kutubxona). |
| `backend/apps/core/html.py` | Admin muharriridan kelgan HTML'ni tozalash (XSS'dan himoya) va manzil (slug) yasash. |
| `backend/apps/core/middleware.py` | Fayl xavfsizligi middleware'lari (faqat Python/Django). |
| `backend/apps/core/models.py` | — |
| `backend/apps/core/nightly.py` | Kechki vazifalar: har biri mustaqil, biri yiqilsa qolganlari ishlayveradi. `run_nightly` shularni tinch oynada ishga tushiradi. |
| `backend/apps/core/parsers.py` | So'rov tanasi parserlari: hamma endpoint (panel, kabinet, murojaat, kirish) shu orqali o'tadi. |
| `backend/apps/core/signals.py` | — |
| `backend/apps/core/storage.py` | Yopiq saqlash: ochiq `/media/` dan tashqarida turadigan fayllar (fuqarolar murojaati ilovalari). |
| `backend/apps/core/throttles.py` | So'rov cheklovlari (rate limit) — tizimga yuklama tushmasligi va parol terib ko'rishdan himoya. |
| `backend/apps/core/uploads.py` | Foydalanuvchi yuklagan fayllar: umumiy kirish nuqtalari. Chuqur tekshiruv — `filesafe.py` da (faqat Python). |
| `backend/apps/core/utils.py` | — |
| `backend/apps/hemis/api.py` | HEMIS REST API (v1) bilan ishlash: universitetning o'z HEMIS serveri, token bilan, faqat o'qish. |
| `backend/apps/hemis/base.py` | HEMIS (faqat o'qish) klienti interfeysi. |
| `backend/apps/hemis/cache.py` | HEMIS klienti: bazadagi oxirgi nusxadan o'qiydi (HemisSnapshot). Nusxa hali bo'lmasa — namunaga qaytadi. |
| `backend/apps/hemis/guard.py` | HEMIS serveriga bosim tushmasligi uchun himoya ("circuit breaker"). |
| `backend/apps/hemis/models.py` | — |
| `backend/apps/hemis/schedule.py` | Kechki jadval: og'ir ishlar (HEMIS sinxronlash va b.) faqat «tinch oyna»da — server ham, HEMIS ham bo'sh vaqtda. |
| `backend/apps/hemis/snapshot.py` | Namuna HEMIS klienti: `seed_data/hemis-snapshot.json` dan o'qiydi (haqiqiy API ulanguncha). |
| `backend/apps/hemis/sync.py` | HEMIS → sayt uchun nusxa (seed_data/hemis-snapshot.json bilan bir xil tuzilma). |
| `backend/apps/hemis/urls.py` | — |
| `backend/apps/hemis/views.py` | HEMIS orqali kirish (OAuth2): xodim universitet login-paroli bilan kiradi. |
| `backend/apps/pages/models.py` | — |
| `backend/apps/panel/auth.py` | Vue admin panel kirishi: Django sessiyasi + Payload'dagi kabi Origin tekshiruvi, bloklash va kirish tarixi. |
| `backend/apps/panel/collections.py` | Vue admin panel kolleksiyalari: Django modeli ↔ Payload shaklidagi JSON. |
| `backend/apps/panel/dashboard.py` | Admin panel yig'ma ma'lumotlari (/api/cms/panel/*): bosh sahifa, statistika, media, YouTube, HEMIS, BRM. |
| `backend/apps/panel/globals_.py` | Vue admin panel global sozlamalari (bitta yozuvli): sayt sozlamalari, video sahifasi, ramzlar, BRM sahifasi. |
| `backend/apps/panel/jwt.py` | JWT (HS256) — admin panel API'sini Swagger, Postman va boshqa dasturlardan cookie'siz chaqirish uchun. |
| `backend/apps/panel/models.py` | — |
| `backend/apps/panel/query.py` | Payload CMS so'rov formati → Django ORM. |
| `backend/apps/panel/request.py` | So'rovdan IP, tarmoq turi, brauzer, OS va qurilma (kirish tarixi uchun, kutubxonasiz). |
| `backend/apps/panel/twofactor.py` | Ikki bosqichli tasdiq (TOTP, RFC 6238): Google/Microsoft Authenticator, 1Password, Authy va h.k. |
| `backend/apps/panel/urls.py` | Vue admin panel API'si: /api/cms/* (Payload REST bilan bir xil manzillar va javoblar). |
| `backend/apps/panel/usage.py` | Media fayli qayerda ishlatilgan: "Qayerda ishlatilgan" ro'yxati va ishlatilayotgan faylni o'chirishdan himoya. |
| `backend/apps/panel/views.py` | Vue admin panel API'si (/api/cms/*): kolleksiyalar, globallar, versiyalar — Payload REST bilan bir xil shakl. |
| `backend/apps/structure/maps.py` | Bino xaritasi: koordinatani matndan yoki Google Maps havolasidan ajratish va xarita manzillarini qurish. |
| `backend/apps/structure/models.py` | — |
| `backend/config/settings.py` | ÖzDJTU sayti — backend (Django + DRF) sozlamalari. Hamma narsa .env orqali boshqariladi. |
| `backend/config/settings_test.py` | Test sozlamalari — `python manage.py test` avtomatik shuni ishlatadi (manage.py). |
| `backend/config/urls.py` | — |

### Backend testlari xaritasi (284 ta test)

Ishga tushirish: `cd backend && python manage.py test --parallel` · bitta fayl: `python manage.py test tests.security.test_files`.

| Fayl | Testlar | Nimani tekshiradi |
|---|---|---|
| `backend/tests/api/test_contract.py` | 6 | Shartnoma testi: ochiq API javoblari `frontend/docs/openapi.yaml` sxemalariga mos bo'lishi shart (4 til × barcha endpoint). |
| `backend/tests/api/test_flows.py` | 13 | Ochiq API oqimlari (demo ma'lumot bilan): sanoqlar, eski /api/site/* manzillari, API token, xodim kabineti, murojaat, statistika. |
| `backend/tests/api/test_swagger.py` | 11 | Swagger to'liqligi: kodda ishlaydigan har bir amal hujjatda bo'lishi shart (yangi endpoint/kolleksiya qo'shilganda |
| `backend/tests/core/test_backup.py` | 41 | Zaxira va tiklash: yaratish, tekshirish, tiklash (SQLite va PostgreSQL — qaysi baza bilan ishlayotgan bo'lsa), ko'chma JSON, |
| `backend/tests/core/test_docs.py` | 10 | Qo'llanma (docs/) eskirmasligi: avtomatik fayllar kodga mos, havolalar/anchorlar/yo'llar/buyruqlar mavjud. |
| `backend/tests/core/test_page_cleanup.py` | 4 | «Toshkent haqida» / «Kontingent» sahifalarini o'chiruvchi migratsiya (0002_remove_toshkent_kontingent). |
| `backend/tests/hemis/test_load_control.py` | 25 | HEMIS'ga va serverga bosim: tinch oyna, qulf, so'rov byudjeti, ketma-ket xatoda to'xtash, kechki jadval. |
| `backend/tests/panel/test_collections.py` | 11 | Admin panel API (`/api/cms/*`): har bir kolleksiya uchun o'qish → o'zini PATCH → nusxa yaratish → o'chirish aylanishi, · `slow` |
| `backend/tests/panel/test_pagination.py` | 5 | Sahifalash: har bir kolleksiyada barcha sahifalarni aylanib chiqqanda yozuvlar yo'qolmaydi va takrorlanmaydi; · `slow` |
| `backend/tests/panel/test_spa_queries.py` | 4 | Admin SPA yuboradigan murakkab so'rovlar (`where[and][0][...]`, `like`, `not_in`, `exists`, `trash` ...): |
| `backend/tests/security/test_access_control.py` | 22 | Ob‘ekt darajasidagi ruxsat: id almashtirib begona ma’lumot olish (IDOR), kabinet izolyatsiyasi, post egaligi. |
| `backend/tests/security/test_auth.py` | 22 | Kirish: JWT, parol almashganda bekor qilish, 2FA (TOTP). |
| `backend/tests/security/test_cache_pressure.py` | 15 | Kesh va bosim: cache-busting, kesh to'qnashuvi, token bilan himoyalangan javob keshi, statistika/yuklab olish suiiste'moli. |
| `backend/tests/security/test_data_theft.py` | 17 | Hujum simulyatsiyasi: ma'lumot o'g'irlash (oracle, enumeration, IDOR, draft sizishi, token/rol), scraping va suiiste'mol. |
| `backend/tests/security/test_files.py` | 30 | Fayl xavfsizligi testlari: yuklash (tekshiruv, tozalash), yopiq saqlash, yuklab olish sarlavhalari, hajm cheklovi. |
| `backend/tests/security/test_hardening.py` | 17 | Chiqishdan oldingi audit topilmalari: har biri uchun regressiya testi (hujum so'rovi → xavfsiz javob). |
| `backend/tests/security/test_jwt_roles.py` | 8 | JWT va rollar: soxta/muddati o'tgan token, rol cheklovlari, yopilgan hisob, Swagger ruxsati. |
| `backend/tests/security/test_production_checks.py` | 2 | API_TOKEN almashtirish va production sozlama ogohlantirishlari. |
| `backend/tests/security/test_query_injection.py` | 6 | Soʻrov xavfsizligi: `where`/`sort` orqali yashirin maydonlarni tekshirib bo‘lmaydi. |
| `backend/tests/security/test_role_matrix.py` | 6 | Swagger'dagi `x-roles` haqiqatga mosligi: har rol × amal uchun server 403 qaytaradi ⇔ rol `x-roles` da yo'q. |
| `backend/tests/security/test_throttling_cache.py` | 9 | So‘rov cheklovi (throttle) va ochiq API keshi. |

### Ma'lumotlar modellari

| Ilova | Model | Nomi | Fayl |
|---|---|---|---|
| `core` | `Media` | Fayl | `apps/core/models.py` |
| `core` | `SiteSettings` | Sayt sozlamalari | `apps/core/models.py` |
| `core` | `Activity` | Faollik | `apps/core/models.py` |
| `core` | `Hit` | Tashrif | `apps/core/models.py` |
| `accounts` | `User` | Foydalanuvchi | `apps/accounts/models.py` |
| `accounts` | `StaffSession` | Xodim sessiyasi | `apps/accounts/models.py` |
| `content` | `Category` | Kategoriya | `apps/content/models.py` |
| `content` | `Post` | Post | `apps/content/models.py` |
| `content` | `PostAttachment` | Fayl (PDF) | `apps/content/models.py` |
| `content` | `PostGalleryImage` | Galereya rasmi | `apps/content/models.py` |
| `content` | `Slide` | Slayd | `apps/content/models.py` |
| `content` | `Leader` | Rahbar | `apps/content/models.py` |
| `content` | `DocCategory` | Hujjat toifasi | `apps/content/models.py` |
| `content` | `Document` | Hujjat | `apps/content/models.py` |
| `content` | `VideoCategory` | Video toifasi | `apps/content/models.py` |
| `content` | `Video` | Video | `apps/content/models.py` |
| `content` | `VideoPage` | Video sahifasi | `apps/content/models.py` |
| `content` | `HomeBanner` | Bayram banneri | `apps/content/models.py` |
| `content` | `StateSymbol` | Davlat ramzi | `apps/content/models.py` |
| `content` | `Partner` | Hamkor | `apps/content/models.py` |
| `content` | `TaughtLanguage` | O‘qitiladigan til | `apps/content/models.py` |
| `structure` | `Faculty` | Fakultet | `apps/structure/models.py` |
| `structure` | `Department` | Kafedra | `apps/structure/models.py` |
| `structure` | `StaffProfile` | Xodim profili | `apps/structure/models.py` |
| `structure` | `StaffDocument` | Xodim hujjati | `apps/structure/models.py` |
| `structure` | `ProgramGroup` | Yo‘nalishlar guruhi | `apps/structure/models.py` |
| `structure` | `Program` | Ta’lim yo‘nalishi | `apps/structure/models.py` |
| `structure` | `AdmissionSettings` | Qabul sozlamalari | `apps/structure/models.py` |
| `structure` | `AdmissionDate` | Muhim sana | `apps/structure/models.py` |
| `structure` | `AdmissionFaq` | Ko‘p so‘raladigan savol | `apps/structure/models.py` |
| `structure` | `Campus` | Bino / kampus | `apps/structure/models.py` |
| `structure` | `ContactEmail` | E-pochta (aloqa) | `apps/structure/models.py` |
| `structure` | `Appeal` | Murojaat | `apps/structure/models.py` |
| `pages` | `Page` | Sahifa | `apps/pages/models.py` |
| `pages` | `PageFact` | Raqam | `apps/pages/models.py` |
| `pages` | `PageTimeline` | Vaqt chizig‘i | `apps/pages/models.py` |
| `pages` | `PageAttachment` | PDF hujjat | `apps/pages/models.py` |
| `pages` | `SdgGoal` | BRM maqsadi | `apps/pages/models.py` |
| `pages` | `SdgSection` | Ichki bo‘lim | `apps/pages/models.py` |
| `pages` | `SdgGoalReport` | Hisobot | `apps/pages/models.py` |
| `pages` | `SdgPage` | BRM sahifasi | `apps/pages/models.py` |
| `pages` | `SdgCategory` | GreenMetric yo‘nalishi | `apps/pages/models.py` |
| `pages` | `SdgOverviewReport` | Hisobot | `apps/pages/models.py` |
| `hemis` | `HemisSnapshot` | HEMIS nusxasi | `apps/hemis/models.py` |
| `panel` | `LoginEvent` | Kirish urinishi | `apps/panel/models.py` |
| `panel` | `Version` | Versiya | `apps/panel/models.py` |
| `panel` | `RevokedToken` | Bekor qilingan token | `apps/panel/models.py` |

### Middleware tartibi (yuqoridan pastga)

1. `django.middleware.security.SecurityMiddleware`
2. `apps.core.middleware.UploadSizeLimitMiddleware`
3. `apps.core.middleware.ApiHeadersMiddleware`
4. `apps.core.middleware.MediaHeadersMiddleware`
5. `whitenoise.middleware.WhiteNoiseMiddleware`
6. `corsheaders.middleware.CorsMiddleware`
7. `django.contrib.sessions.middleware.SessionMiddleware`
8. `django.middleware.common.CommonMiddleware`
9. `django.middleware.csrf.CsrfViewMiddleware`
10. `django.contrib.auth.middleware.AuthenticationMiddleware`
11. `django.contrib.messages.middleware.MessageMiddleware`
12. `django.middleware.clickjacking.XFrameOptionsMiddleware`
