# 12. Qanday qilaman: kodni kengaytirish retseptlari

Har retsept: **nimani o‘zgartirasiz → qaysi faylda → nimani tekshirasiz**. Oxirida doim: `cd backend && python manage.py test` va (hujjatga ta’sir qilsa) `python manage.py build_docs`.

## Yangi admin kolleksiyasi (masalan, «Yangi bo‘lim»)

1. **Model**: tegishli ilovada (`backend/apps/<ilova>/models.py`); matnlar uchun 4 tilli `JSONField` (`apps/core/fields.py`, `LANGS`). So‘ng `python manage.py makemigrations`.
2. **Kolleksiya sinfi**: `backend/apps/panel/collections.py` — `Collection` dan meros oling: `slug`, `model`, `access` (kim nima qila oladi), `out()` (model → JSON), `write()` (JSON → model), kerak bo‘lsa `can()`/`scope()` (obyekt darajasidagi qoida) va `rules` (Swagger uchun matn).
3. **Ro‘yxatga qo‘shing**: shu faylning oxiridagi `REGISTRY` ga. URL alohida yozilmaydi — `/api/cms/<slug>` avtomatik ishlaydi.
4. **Admin sahifasi**: `admin/src/pages/<Nom>Page.vue`, `admin/src/router.ts` (`roles`/`superOnly`) va menyu.
5. **Test**: `backend/tests/panel/test_collections.py` va ruxsat uchun `tests/security/test_access_control.py` ga misol qo‘shing.
6. **Tekshiruv**: rol jadvali (`docs/reference.md`) o‘zi yangilanadi — `build_docs` ni ishga tushiring; Swagger'da (`/api/docs/?role=editor`) yangi amallar ko‘rinadi.

## Mavjud modelga maydon qo‘shish

1. Modelga maydon → `makemigrations` → `migrate`.
2. Kolleksiyaning `out()` va `write()` metodlariga qo‘shing (`apps/panel/collections.py`). Matn bo‘lsa — HTML tozalash `core/html.py` orqali.
3. Ochiq saytda kerak bo‘lsa: `apps/api/builders.py` (javob shakli) va `frontend/docs/openapi.yaml` + `frontend/shared/types/api.ts` (shartnoma). Shartnoma testi: `tests/api/test_contract.py`.
4. Admin formasi: tegishli `admin/src/pages/*Page.vue`.

## Yangi ochiq API endpoint

1. View: `backend/apps/api/views.py` (yoki `staff.py` — kabinet uchun). Ro‘yxat/GET bo‘lsa `CachedGetMixin` (`apps/api/common.py`) keshni beradi.
2. Manzil: `backend/apps/api/urls.py`.
3. `throttle_scope` belgilang (`public`, `search`, `appeals`, …) — ro‘yxat `settings.py → DEFAULT_THROTTLE_RATES`. Yangi toifa kerak bo‘lsa shu yerga qo‘shing va `.env.example` ga `THROTTLE_<NOM>`.
4. `@extend_schema` bilan Swagger tavsifi (`tags`, `summary`).
5. Sayt tomoni: `frontend/server/api/…` (brauzer shu yerga murojaat qiladi) va turlari `frontend/shared/types/api.ts`.
6. Test: `tests/api/test_flows.py` (oqim), `tests/api/test_swagger.py` (hujjatda bormi).
7. **Xavfsizlik**: ob’yektni ID bilan beradigan bo‘lsa — `tests/security/test_data_theft.py` dagi kabi «boshqa odamning yozuvi» testini qo‘shing.

## Saytga yangi sahifa qo‘shish

1. `frontend/app/pages/<nom>.vue` — ichida **`useSeo({ title: () => t('…'), description: () => t('…') })`** (rasm bo‘lsa `image`). Yopiq sahifa bo‘lsa `noindex: true`.
2. Matnlar — `i18n/locales/{uz,ru,en,zh}.json` ga **to‘rttasiga** (tekshiradi: `npm run test:pages`).
3. Menyuga chiqsa — backend menyusi; menyudagi ichki havolalar `sitemap.xml` ga o‘zi tushadi. Menyuda yo‘q bo‘lsa — `server/routes/sitemap.xml.ts` dagi `FIXED` ga qo‘shing.
4. `cd frontend && npm test`.

## Yangi til qo‘shish (masalan, `kk`)

1. Backend: `apps/core/fields.py` → `LANGS`.
2. Sayt: `frontend/nuxt.config.ts` → `i18n.locales` va `frontend/i18n/locales/kk.json` (`uz.json` dan nusxa).
3. Admin: 4 tilli maydonlar (`admin/src/components/LangTabs.vue`) tillar ro‘yxatini oladi — shu faylni tekshiring.
4. Mavjud yozuvlarda yangi til bo‘sh bo‘ladi; `HIDE_UNTRANSLATED_POSTS` tarjimasiz postlarni yashiradi.

## Yangi rol qo‘shish

1. `backend/apps/accounts/models.py` → `ROLES` (+ migratsiya; `role` maydoni uzunligi 12 belgi).
2. `backend/apps/panel/collections.py` → rol to‘plami (`EDITORS`, `SDG` kabi) va kerakli kolleksiyalarning `access` ga.
3. `admin/src/router.ts` — sahifa `roles` ga; menyu ko‘rinishi.
4. Testlar: `tests/security/test_access_control.py`, `tests/security/test_jwt_roles.py`.
5. `build_docs` — rol × kolleksiya jadvali yangilanadi.

## So‘rov cheklovini o‘zgartirish

`.env` da `THROTTLE_<NOM>=son/vaqt` (`sec`, `min`, `hour`, `day`), so‘ng backendni qayta ishga tushiring: `docker compose restart backend`. Ro‘yxat: [reference → Sozlamalar](reference.md).

## Superadmin parolini tiklash

```bash
docker compose exec backend python manage.py changepassword superadmin
```

Superadmin yo‘qolgan bo‘lsa (masalan, hammasi o‘chib ketgan): foydalanuvchilar **bo‘sh** bo‘lgandagina `seed_demo --first-run` yangisini `SUPERADMIN_*` sozlamalaridan yaratadi; aks holda `manage.py shell` orqali mavjud foydalanuvchining `role` ini `superadmin` qiling.

## Yangi buyruq (`manage.py`) qo‘shish

`backend/apps/<ilova>/management/commands/<nom>.py` — `BaseCommand`, `help` matni **albatta** yozilsin: `reference.md` buyruqlar jadvali shu matndan avtomatik chiqadi. Keyin `build_docs`.

## Kechki vazifa qo‘shish

`backend/apps/core/nightly.py` → `TASKS` ro‘yxatiga (tartib muhim: zaxira birinchi). Vazifa xatosi qolganlarni to‘xtatmasligini tekshiring (`tests/hemis/…`, `tests/core/test_backup.py` dagi misollar).

## Yangi `.env` sozlamasi

1. `settings.py` da `env('NOM', 'sukut')` (yoki `env_bool`, `env_list`).
2. `backend/.env.example` ga izoh bilan qo‘shing. 
3. `build_docs` — «Sozlamalar» jadvali o‘zi yangilanadi.

## Yangi test yozish

- Fayl: `backend/tests/<soha>/test_<nom>.py`; asos sinflar `tests/support.py` (`Base`, `SeededTestCase`, `jwt_for`, `api`, `loose`).
- Sekin test bo‘lsa `@tag('slow')`.
- Faqat bitta test: `python manage.py test tests.panel.test_collections.NomTest.test_x`.
- Batafsil: [06-testlar](06-testlar.md).

## Yangi qo‘llanma sahifasi

`docs/NN-nom.md` yozing → `docs/README.md` dagi «Hujjatlar xaritasi» ga qo‘shing → `cd backend && python manage.py build_docs`. Havolalar va fayl yo‘llari testda tekshiriladi.

## Keyingi qadam

Muammo chiqsa: [11-muammolar](11-muammolar.md).
