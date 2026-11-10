# 3. Ruxsatlar: rollar, kirish turlari, 2FA

## Besh rol

| Rol | Kim | Nima qila oladi (qisqacha) |
|---|---|---|
| `superadmin` | texnik rahbar | hamma narsa: foydalanuvchilar, sozlamalar, statistika, kirish tarixi, faollik jurnali, yopiq murojaat fayllari |
| `editor` | kontent muharriri | postlar (yangilik/e’lon/tadbir), media |
| `faculty` | fakultet admini | **faqat o‘z fakulteti** (`scope`) va uning kafedralari; postlar (faqat o‘zinikini tahrirlaydi) |
| `pages` | sahifalar muharriri | statik sahifalar, hujjatlar, video, postlar (faqat o‘zinikini) |
| `sdg` | BRM menejeri | faqat BRM (17 maqsad): matn, rasm, PDF hisobotlar |

**To‘liq jadval (har kolleksiya × har rol: o‘qish/yaratish/tahrirlash/o‘chirish)** koddan avtomatik yig‘iladi: [reference → Rol × kolleksiya](reference.md). Jadvalning manbasi — `backend/apps/panel/collections.py` (`access` va `rules`) va `globals_.py`.

Foydalanuvchi holati (`status`): `active`, `invited`, `disabled`. **`disabled` bo‘lsa tokenlari ham darhol ishlamay qoladi** — xodim ketganda eng tez yo‘l: Foydalanuvchilar → holatini «Yopilgan» qiling.

## Obyekt darajasidagi qoidalar (rol jadvalidan tashqari)

- **Fakultet admini** (`faculty`) faqat `User.scope` dagi fakultet va uning kafedralarini o‘zgartiradi; boshqasi `403`; kafedrani boshqa fakultetga ko‘chira olmaydi. **`scope` bo‘sh fakultet admini hech narsani o‘zgartira olmaydi** (xavfsiz sukut) — yangi `faculty` foydalanuvchi yaratganda `scope` ni to‘ldirishni unutmang.
- **Postlar**: `faculty` va `pages` faqat o‘zi yozganini tahrirlaydi/o‘chiradi/tiklaydi; `editor` va `superadmin` — hammasini.
- **Foydalanuvchilar**: `superadmin`dan boshqalar faqat o‘zini ko‘radi va o‘zgartiradi; rolini oshira olmaydi.
- **Xodim kabineti** (`/api/me*`): faqat sessiyadagi xodimning o‘z HEMIS ID'si; id URL'dan olinmaydi (IDOR yo‘q).

## Kirish turlari (kim qanday kiradi)

| Tur | Kim uchun | Qanday | Muddat | Kod |
|---|---|---|---|---|
| Sessiya cookie | admin panel (brauzer) | `POST /api/cms/users/login` | 12 soat | `apps/panel/auth.py` |
| JWT (`Authorization: Bearer …`) | Swagger, Postman, skriptlar | shu login javobidagi `token` | `JWT_TTL_SECONDS` (8 soat) | `apps/panel/jwt.py` |
| `API_TOKEN` | **sayt serveri** (Nuxt) → ochiq API | `Authorization: Bearer <API_TOKEN>` | doimiy (almashtiriladi) | `apps/api/common.py` |
| Xodim sessiyasi | xodim kabineti (`/api/me*`) | HEMIS (my.gov) OAuth orqali | 12 soat | `apps/api/staff_auth.py`, `apps/hemis/views.py` |

Muhim tafsilotlar:

- Cookie bilan yozuvchi so‘rovlar (`POST/PATCH/DELETE`) `Origin` bo‘yicha tekshiriladi: admin panel manzili `TRUSTED_ORIGINS` da bo‘lishi shart. JWT bilan bu shart emas.
- **JWT bekor qilinadi**: `logout`, `refresh-token`, parol o‘zgarishi, hisob yopilishi (`RevokedToken`).
- **Kirishni bloklash**: 5 ta noto‘g‘ri parol → 15 daqiqa (mavjud bo‘lmagan loginlarga ham xuddi shunday — loginni topib bo‘lmaydi). Superadmin Foydalanuvchilar sahifasidan «Blokdan chiqarish» qiladi.
- `API_TOKEN` ni to‘xtovsiz almashtirish: `API_TOKEN=yangi,eski` → frontendni yangilang → `API_TOKEN=yangi`.
- Xodim kabineti tokenini sinash uchun yaratish: `python manage.py issue_staff_session <hemis_id>`.

## 2FA (ikki bosqichli tasdiq)

- Foydalanuvchi **Profil → «Ikki bosqichli tasdiq»** da yoqadi (Google/Microsoft Authenticator, 1Password …). 8 ta bir martalik zaxira kod beriladi.
- Yoqilgan bo‘lsa login ikki bosqichli: `POST /users/login` → `twoFactorRequired` + `challenge`; `POST /users/login/2fa` yakunlaydi. Kod xatolari ham 5 ta → blok; bir kod ikki marta ishlamaydi.
- **Majburiy qilish**: `backend/.env` → `REQUIRE_2FA_ROLES=superadmin,editor`. Bu rollar 2FA yoqmaguncha panel ma’lumotlariga kira olmaydi.
- **Telefon yo‘qolsa**: zaxira kod bilan kiring yoki superadmin Foydalanuvchilar sahifasidan foydalanuvchi uchun 2FA ni tiklaydi (`POST /users/2fa/reset`).
- HEMIS orqali kirishda TOTP so‘ralmaydi (HEMIS'ning o‘z autentifikatsiyasiga tayaniladi). Kod: `apps/panel/twofactor.py`.

## Ruxsatni qanday tekshirish

| Savol | Javob |
|---|---|
| «`editor` roli X ni qila oladimi?» | [reference](reference.md) jadvali; yoki Swagger → rol filtri (`?role=editor`) ([05-swagger](05-swagger.md)) |
| Avtomatik tekshiruv | `python manage.py test tests.security.test_role_matrix` — har rol × har amal Swagger tavsifi va haqiqiy javob bilan solishtiriladi |
| IDOR, fakultet doirasi, post egasi | `tests/security/test_access_control.py` |
| JWT va rol | `tests/security/test_jwt_roles.py`, `tests/security/test_auth.py` |

## Ruxsat o‘zgartirmoqchimisiz

1. `backend/apps/panel/collections.py` da kolleksiyaning `access` lug‘atini o‘zgartiring (obyekt qoidasi bo‘lsa — `can()`/`scope()` va `rules` matni).
2. Admin panelda sahifani ko‘rsatish/yashirish: `admin/src/router.ts` → `meta.roles` (bu faqat qulaylik; **haqiqiy himoya — backend**).
3. `cd backend && python manage.py test tests.security` va `python manage.py build_docs` (jadval yangilanadi).

Batafsil retsept: [12-qanday-qilaman](12-qanday-qilaman.md).
