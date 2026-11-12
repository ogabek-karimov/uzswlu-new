# 13. Yangiliklar: loyihada nima o‘zgardi

Eng yangisi tepada. **Har bir o‘zgarishdan keyin shu yerga yozing** (qoida: `CLAUDE.md`). Format: sana sarlavha, so‘ng toifa bo‘yicha qisqa punktlar; har yozuv oxirida commit.

## 2026-11-12

- **Sayt (bosh sahifa dizayni):** «Universitet haqida» ixcham qilindi — katta 2×2 raqamlar o‘rniga matn va bitta statistika tasmasi; bosh sahifadagi bo‘limlar orasidagi bo‘shliq qisqartirildi (hero, fakultetlar, yangiliklar, tadbirlar, qabul, ramzlar, hamkorlar); tillar tasmasi kichraytirildi. Ichki sahifalar, sarlavha (header) va ma’lumotlar o‘zgarmadi. Maket: Figma uslubidagi Design artifact. — `23536d1`

- **Sayt (UI):** qidiruv ikonkasi (yuqori qator, bosh sahifa, qidiruv va 404 sahifalari) endi haqiqiy tugma — bosilsa qidiradi, kursor «qo‘l»; butun saytga `button`/`summary`/`select`/`label` uchun umumiy `cursor: pointer` qoidasi (Tailwind 4 tugmalarga oddiy kursor berardi). Admin: katak/radio o‘rab turgan `label` ham «qo‘l». Test: `test:pages`.

- **Xavfsizlik:** `djangorestframework` 3.16.1 → 3.18.3 (5 ta ma’lum zaiflik yopildi: PYSEC-2026-3827/3828, CVE-2026-114136/7/8); `requirements.txt` da `>=3.18.2,<3.19`. 278 ta backend testi o‘tdi. `pip-audit` toza. — `f063971`
- **Xavfsizlik (sayt, npm):** `nuxt` 4.4.8 → 4.6.4; `vue-i18n` va `@intlify/*` 11.4.18 ga `overrides` bilan majburlandi (XSS: GHSA-8rc2-428q-7ww3, GHSA-83rm-6c8r-g728). `npm audit`: 19 → 13 ta, qolgani faqat past/o‘rta va build vositalarida (nitropack → deepmerge/glob/minimatch, tuzatishi hali chiqmagan); admin: 0 ta. — `2f41b93`, `9db1bf3`, `d22212b`

## 2026-11-11

- **Sayt:** ishonch telefoni va ichki raqamlar yuqori qatorning o‘rtasida, hamma ekranda; `1061–1064` diapazoni `1061, 1062, 1063, 1064` bo‘lib chiqadi (yuqori qator va footer). — `6121d3b`, `0bdebba`
- **Sayt SEO:** domen `NUXT_PUBLIC_SITE_URL` dan (canonical, hreflang, og:url), `/sitemap.xml` (4 til) va dinamik `/robots.txt`, har sahifada Open Graph/Twitter preview (`useSeo`), standart `og-default.jpg`. Rasmlarga `loading="lazy"`/`width`/`height`. Testlar: `test:seo`, `test:pages`. — `186ec1b`
- **Admin:** so‘rovlarda timeout (30 s; yuklash 2 min), HTML/502/504 javobga tushunarli xabar, sessiya tugaganda yozganlar yo‘qolmaydigan oyna (`SessionExpiredModal`), `RichEditor` null xatosi. Testlar: `npm test` (API qatlami, manba qoidalari). — `186ec1b`
- **Hujjat:** «Yangiliklar» bo‘limi (shu sahifa) qo‘shildi; qoida `CLAUDE.md` da; format testi `backend/tests/core/test_docs.py` da.

## 2026-11-10

- **CI:** PostgreSQL 16 serverida yangi `pg_dump` nusxasini tiklash tuzatildi; frontend `npm@11 ci`. — `439ac7f`
- **Qo‘llanma:** `docs/` (12 bo‘lim), koddan avtomatik `reference.md`, qidiriladigan `index.html`, `build_docs`, `test_docs.py`. — `48f5873`
- **Zaxira:** kun/hafta/oy/yil saqlash siyosati (GFS), qadash (`--pin`), sana bo‘yicha topish va tiklash. — `dff0504`
- **Zaxira:** baza + fayllarning zaxirasi va tiklash, kechasi avtomatik, SQLite va PostgreSQL. — `e9666a6`
- **Admin:** fakultet/profil nomi muqova chizig‘ida kesilmaydi. — `f28f85c`

## 2026-11-09

- **Admin:** muqova ostida qolgan avatar/logo, tor ekranda ustma-ust tushish, `cursor-pointer`. — `badc07a`
- **Backend:** ommaviy kesh va statistika bosimi (kesh kaliti, hit dedupe, eski hitlarni tozalash). — `9f06894`
- **Xavfsizlik:** chiqishdan oldingi audit (so‘rov tanasi, filtr xatolari, no-store/CSP, login oracle, birinchi ishga tushirish). — `c77e2f5`
- **Admin:** HEMIS sinxronlash holati kartasi. — `99fe859`
- **HEMIS:** kechki oyna, xushmuomala klient, qulf, kechki vazifalar. — `2823e18`
- **Swagger:** rollarga mos CRUD hujjati, `?role=` filtri. — `d22260d`

## 2026-11-08

- **Swagger:** ommaviy PATCH/DELETE, yopiq fayl endpointi, to‘liqlik testi. — `bc95df4`
- **Testlar:** modullarga bo‘lingan, hermetik sozlamalar, CI. — `a850cd4`
- **Xavfsizlik:** fayl yuklash va yuklab olishni chuqur himoyalash. — `0492987`
- **Sayt:** media keshi; backend o‘chganda oxirgi yaxshi javob 3 soat. — `ec71ec5`, `adb110d`
