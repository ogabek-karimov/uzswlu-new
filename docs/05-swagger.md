# 5. Swagger va API shartnomasi

## Qayerda

| Manzil | Nima |
|---|---|
| http://localhost:8000/api/docs/ | Swagger UI (dizayn: `SWAGGER_THEME=modern` yoki `classic`) |
| http://localhost:8000/api/redoc/ | ReDoc |
| http://localhost:8000/api/schema/ | OpenAPI 3.1 JSON/YAML |
| `/api/schema/?role=editor` | faqat shu rolga ruxsat etilgan amallar |

Productionda `API_DOCS_PUBLIC=false`: hujjatni faqat admin panelga kirgan xodim ko‘radi.

## Swagger'da sinash (admin API)

1. Sahifa tepasidagi **«Sinash uchun kirish»** paneliga login va parolni kiriting (2FA yoqilgan bo‘lsa kodni ham). Token avtomatik **Authorize → `panelJwt`** ga qo‘yiladi.
2. Qo‘lda: `POST /api/cms/users/login` → «Try it out» → javobdagi `token` ni **Authorize** ga kiriting.
3. Rolingizga ruxsat etilmagan amallar xiralashadi; «faqat menga ruxsat etilganlar» filtri bor.
4. Ochiq sayt API'si uchun: **Authorize → `bearerAuth`** ga `API_TOKEN` ni kiriting (`API_TOKEN` bo‘sh bo‘lsa shart emas). Xodim kabineti (`/api/me*`): `userSession` (cookie) yoki `staffBearer` (token: `manage.py issue_staff_session <hemis_id>`).
5. Har admin amalining tavsifida: qaysi rollar qila oladi (`x-roles`) va obyekt darajasidagi qoidalar («Qoida: …»).

## Hujjat qanday yig‘iladi

| Qism | Manba | Kod |
|---|---|---|
| Ochiq sayt API'si (`/api/home`, `/api/posts`…) | **shartnoma** `frontend/docs/openapi.yaml` (Docker'da ulangan; bo‘lmasa `backend/apps/api/contract/openapi.yaml` nusxasi) | `apps/api/swagger.py: merge_contract` |
| Admin API (`/api/cms/*`) | kolleksiya kodidan **avtomatik** (qo‘lda yozilgan ro‘yxat yo‘q) | `apps/api/swagger_fields.py`, `swagger.py: _expand_admin` |
| Rollar (`x-roles`) | `Collection.access` va ko‘rinishlardagi tekshiruvlardan | `swagger.py: _probe`, `_tag_roles` |
| Rol filtri `?role=` | schema postprocessing | `swagger.py: filter_by_role` |
| Sahifa dizayni va kirish paneli | `backend/apps/api/templates/api/swagger_modern.html` | — |

Shartnoma o‘zgarsa nusxani yangilang: `cp frontend/docs/openapi.yaml backend/apps/api/contract/openapi.yaml`.

## Hujjat va kod bir-biriga mosligini kim kafolatlaydi

- `tests/api/test_swagger.py` — kodda ishlaydigan **har bir** endpoint/amal hujjatda bor (yangisini qo‘shib, hujjatni unutib bo‘lmaydi).
- `tests/security/test_role_matrix.py` — Swagger'dagi rollar haqiqiy javoblar bilan solishtiriladi (hujjat «ruxsat bor» desa, server 403 bermaydi va aksincha).
- `tests/api/test_contract.py` — haqiqiy API javoblari `openapi.yaml` sxemasiga mos (4 til × hamma endpoint) — `slow` tegli.

## Qanday qilib ...

| Maqsad | Yo‘l |
|---|---|
| Yangi admin kolleksiya Swagger'da ko‘rinsin | `collections.py` ga qo‘shsangiz o‘zi chiqadi; `tests.api.test_swagger` tekshiradi |
| Ochiq endpoint tavsifini o‘zgartirish | `frontend/docs/openapi.yaml` ni tahrirlang (frontend va backend uchun yagona shartnoma), nusxani yangilang |
| Swagger ko‘rinishini o‘zgartirish | `SWAGGER_THEME=classic` yoki `swagger_modern.html` |
| Hamma manzillarni jadvalda ko‘rish | [reference → Manzillar](reference.md) |
