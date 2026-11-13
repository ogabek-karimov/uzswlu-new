# 13. Yangiliklar: loyihada nima o‘zgardi

Eng yangisi tepada. **Har bir o‘zgarishdan keyin shu yerga yozing** (qoida: `CLAUDE.md`). Format: sana sarlavha, so‘ng toifa bo‘yicha qisqa punktlar; har yozuv oxirida commit.

## 2026-11-13

- **Server (prod compose: admin kirishi):** `docker-compose.prod.yml` backendga domenlarni (`ALLOWED_HOSTS`, `TRUSTED_ORIGINS`, `PUBLIC_SERVER_URL`, `ADMIN_PANEL_URL`, `SITE_URL`) ildiz `.env` dagi `SITE_HOST`/`ADMIN_HOST`/`API_HOST`/`HTTP_PORT` dan beradi — avval `api.localhost` Host’i rad etilib, admin panel «Server bilan aloqa yo‘q» ko‘rsatardi. Lokal http sinovi uchun `COOKIE_SECURE=false` (ildiz `.env`). — `18ccad3`

- **Server (nginx + Redis, production tuzilmasi):** `docker-compose.prod.yml` — nginx (`proxy_cache`, single-flight `proxy_cache_lock`, stale-while-revalidate, API va admin statik), Nuxt build (`frontend/Dockerfile`), gunicorn backend, **Redis** (umumiy kesh va so‘rov-cheklov, `volatile-lru`), PostgreSQL. `requirements.txt` ga `redis` paketi. Lokal sinash: `docker compose -f docker-compose.prod.yml up -d --build`, `X-Cache: MISS → HIT`. CI’da yangi `deploy` ishi: compose to‘g‘riligi, kalitsiz ishga tushmasligi va `nginx -t`. Hali haqiqiy Docker’da to‘liq ishga tushirib sinalmagan (sandbox’da Docker yo‘q) — birinchi ishga tushirishda `docker compose ... logs nginx` ni tekshiring. — `a34cef4`

- **Backend + sayt (admin saqlaganda keshni yangilash):** kontent o‘zgarsa fonda Nuxt keshi tozalanadi (`POST /api/_purge`, token bilan) va nginx’dagi bosh sahifalar (4 til) `X-Cache-Refresh` sarlavhasi bilan yangilanadi — endi 5 daqiqa kutish yo‘q. Ketma-ket saqlashlar bitta yangilanishga birlashadi; xato bo‘lsa saqlash to‘xtamaydi. Sozlamalar: `EDGE_PURGE_URL`, `EDGE_REFRESH_URLS`, `EDGE_REFRESH_TOKEN` (bo‘sh bo‘lsa o‘chiq). Yangi: `apps/api/edge.py`, `frontend/server/api/_purge.post.ts`; 5 ta test. — `83c4026`

- **Xavfsizlik (audit, hujjat va test):** yopiq fayl endpointi (faqat superadmin, `safe_join`, `attachment`/`nosniff`/`no-store`) va kabinet hujjatlari egasiga bog‘langanligi tekshirildi — kamchilik topilmadi; UUID faqat fayl nomini taxmin qilib bo‘lmas qiladi, ruxsat tekshiruvi emasligi `docs/10-server.md` ga yozildi. Yangi test: `CabinetOwnershipTests` (boshqa xodim hujjatini o‘chirib bo‘lmaydi). — `51b158d`

- **Backend (to‘dan himoya — cache stampede):** ochiq GET javoblar keshi endi bir xil so‘rovlarni birlashtiradi: keshda yangi nusxa bo‘lsa — darhol; muddati o‘tgan bo‘lsa — eski nusxa darhol beriladi, yangilashni qulfni olgan **bitta** so‘rov bajaradi; nusxa umuman yo‘q bo‘lsa (birinchi so‘rov, kontent o‘zgargandan keyin) — bitta so‘rov yig‘adi, qolganlari natijani (≤ 5 s) kutadi, qulf egasi yiqilsa o‘zi yig‘adi. Muddati o‘tgan nusxa `PUBLIC_CACHE_STALE_SECONDS` (300 s) saqlanadi; admin o‘zgartirsa kesh baribir bir zumda yangilanadi (kalit versiyasi). 8 ta test (`tests/api/test_cache_stampede.py`: 30 parallel so‘rov → 1 ta yig‘ish). — `6fe5082`

- **Sayt (tezlik, yuklama):** `routeRules` — sahifalarga `Cache-Control: public, s-maxage=60, stale-while-revalidate=300` (kabinet, qidiruv va `/api/**` — `no-store`), bosh sahifalar (4 til) Node’da `swr: 60`; hashli `/_nuxt/**` — `immutable`. `docs/10-server.md` ga «Yuklama va tezlik» bo‘limi: nginx `proxy_cache` + bir nechta Node nusxasi namunasi, qatlamlar jadvali, HEMIS ta’siri (ochiq sahifa HEMIS’ga bormaydi), tekshirish buyruqlari. Backend yuk sinovi (sandbox): 1000 bir vaqtdagi so‘rov — xatosiz, ~3 s. — `feaf988`

## 2026-11-12

- **Backend (mavjud bazalar uchun migratsiya):** «Universitet bitiruvchilari haqida» menyu bandi PDF-havoladan matnli sahifaga o‘zi aylanadi — `pages/0003_graduates_text_page` (qo‘lda admin panelda o‘zgartirish kerak emas; faqat hali PDF-havola bo‘lsa ishlaydi, allaqachon o‘zgartirilgan bo‘lsa tegmaydi). Oldingi `d86a741` yozuvidagi «mavjud bazada admin orqali» qadami endi shart emas. — `b81ff12`

- **Backend (menyu tozalash):** «Toshkent haqida» va «Kontingent» sahifalari endi mavjud bazalardan ham o‘zi o‘chadi — `pages/0002_remove_toshkent_kontingent` migratsiyasi (backend qayta ishga tushganda bajariladi; qo‘lda buyruq kerak emas; ostida bolasi bor sahifa saqlanadi). Sabab: seed faqat bo‘sh bazaga yuklanadi, shuning uchun eski bazada sahifalar menyuda qolib ketgan edi. — `fde8ce7`

- **Sayt (Faoliyat → «Universitet bitiruvchilari haqida»):** endi PDF emas, saytdagi matnli sahifa — `/universitet-bitiruvchilari-haqida`: kirish matni 4 tilda va PDF’dagi infografika rasmi (`public/images/pages/bitiruvchilar.webp`, 2400 px, PDF’dan chizilgan). Matnli sahifa, yangilik va BRM sahifalaridagi har qanday rasm (havola ichida bo‘lmasa) bosilsa to‘liq ekranda kattalashadi (`ProseHtml` + `ImageViewer`). `pages-seed.json` va `mock-menu.ts` yangilandi; mavjud bazada — admin panel → Sahifalar: shablon «Matnli sahifa», manzil `universitet-bitiruvchilari-haqida`. — `d86a741`

- **Sayt (menyu):** «Abiturientlar» bo‘limidan «Toshkent haqida» va «Kontingent» sahifalari butunlay olib tashlandi (`pages-seed.json`, `mock-menu.ts`; mavjud bazada — admin panel → Sahifalar orqali o‘chiriladi). Endi `/toshkent-haqida` va `/kontingent` — 404. — `84688f2`

- **Sayt (bosh sahifa, til almashtirish):** til o‘zgarganda kartalar endi kattalashib-kichraymaydi — matn uchun hamma tilda bir xil joy ajratiladi: xizmatlar tasmasi (sarlavha 2, izoh 3 qator), «Universitet haqida» kartalari (kamida 400 px) va raqamlar tasmasi yozuvlari (2 qator), fakultet kartalari (288 px, nom 4 qatorgacha), yangilik/e’lon sarlavhalari (3 qator), tadbirlar (sarlavha 3 qator, joy 1 qator), binolar (nomi 2, manzili 3 qator), bo‘lim tavsifi (`SectionHeading`, 2 qator). 1280/1440/1920 px da 4 tilda sahifa balandligi bir xil. Bayram banneri rasm yuklanguncha joyini oldindan egallaydi: `GET /home → banner.width/height` (shartnomada ham), sahifa sakramaydi. — `dcd74f8`

- **Sayt (chap panel va jurnal):** eski saytdagi chap panel qaytdi — chetga yopishgan vertikal panel: Facebook, X, Instagram, Telegram, YouTube (brend rangida, hover’da to‘ladi va nomi chiqadi) va «O‘quv binolari» (`/oquv-binolari`). Havolalar admin panel sozlamalaridan (`GET /site → socials`); keng ekranda (≥1360 px) doim ochiq, torroqda kontentni yopmasligi uchun chetga yig‘iladi (kursor yoki tilcha bilan chiqadi), telefonda mobil menyuda. «Filologiya masalalari» jurnali (`philmatt.uzswlu.uz`, «FM» logotipi `public/images/journal-fm.webp`) sarlavhada — til tanlagich oldida. Yangi: `SocialDock.vue`, `utils/socials.ts`, `social.*`/`journal.*` matnlari 4 tilda. **Admin:** Sozlamalar → aloqa: «X (Twitter)» maydoni (`SiteSettings.x_url`, avval admindan o‘zgartirib bo‘lmasdi). Test: `GlobalsAndVersionsTests.test_settings_x_link_reaches_site`. — `91e56d6`

- **Sayt (tarjima, til almashtirish):** universitet nomi (sarlavha, footer logosi, footer pastki qatori, sahifa sarlavhasi/OG) endi tanlangan tilda: ru — «Узбекский государственный университет мировых языков» (УзГУМЯ), en — «Uzbekistan State World Languages University» (UzSWLU), zh — «乌兹别克斯坦国立世界语言大学»; avval `university.*` 4 tilda ham o‘zbekcha edi. Footer pastki qatori bitta `footer.copyright` kaliti (xitoychada «。»). Til almashtirilganda sahifa tepaga sakramaydi — o‘sha joyida qoladi (`app/plugins/locale-scroll.client.ts`: faqat til o‘zgargan o‘tishda `meta.scrollToTop = false`; boshqa o‘tishlar avvalgidek). Testlar: `test:pages`, `test:seo`, `test:last-good`. — `84f46de`

- **Sayt (footer):** «Binolar» ustuni va «Ijtimoiy tarmoqlar» olib tashlandi (binolar — bosh sahifadagi «Biz bilan bog‘lanish» va Aloqa sahifasida); endi: logo va tavsif · «Bog‘lanish» · «Foydali havolalar» · QR kod (`public/images/footer-qr.png`, asl rasmdan modulma-modul qayta chizilgan, `qr.me-qr.com/OA2VhTfV`). `footer.qr.*` matnlari 4 tilda. Footer tepasidagi bo‘sh joy qisqartirildi (80 → 40 px). — `44c7b95`

- **Sayt (bosh sahifa): yangiliklar, e’lonlar, aloqa va bayram banneri.** «Yangiliklar» — 4 ta karta (rasm, toifa, sana, BRM maqsadi belgisi, hover’da ko‘tariladi); «E’lonlar» — alohida doskada 4 ta afisha (tik rasm, varaqli taqvim ko‘rinishidagi sana). «Taqvim»dan keyin «Biz bilan bog‘lanish»: binolar kartalari (telefon, e-pochta, manzil, rangli Google xarita, «Xaritada ochish»). Undan keyin «Davlat ramzlari» oldidan bayram banneri — bitta rasm. API: `NewsItem.sdg`, `Announcement.image/sdg`, `ContactPage.campuses[].email/mapEmbed`, `HomeData.banner` (shartnomada ham). — `44efb59`
- **Admin panel:** Sozlamalar → «Binolar va xarita» — binolarni qo‘shish/o‘chirish/tartiblash, nomi va manzili 4 tilda, telefon, e-pochta, xaritadagi joy (koordinata yoki Google Maps havolasi — backend koordinataga aylantiradi, xarita oldindan ko‘rinadi); sozlamalar tarixiga kiradi. «Bosh sahifa karuseli» sahifasida «Bayram banneri» — bitta rasm (yangisi eskisining o‘rniga), ko‘z belgisi bilan yashirish, havola va rasm tavsifi (4 tilda). Backend: `Campus.email/coords` (`structure.0004`), `HomeBanner` (`content.0003`), `apps/structure/maps.py`, global `home-banner`. — `44efb59`

- **Sayt (bosh sahifa, soddalashtirildi):** olib tashlandi — slayder tagidagi «Qabul» paneli va so‘nggi yangiliklar kartasi, «Yaqin tadbir» yo‘lagi, 11 tildagi salomlashuv tasmasi, «Biz o‘qitadigan tillar» karuseli va «Qabul» (4 qadam) bloki (`Hero`, `Today`, `Greetings`, `Languages`, `Admission` komponentlari o‘chirildi). «Universitet haqida» yangi ko‘rinishda: to‘q raqamlar tasmasi — 1949, talabalar va professor-o‘qituvchilar (HEMIS), o‘qitiladigan tillar va xorijiy hamkorlar soni (`GET /home`) — va uchta karta: «Tillar va madaniyatlar ko‘prigi» (→ `/universitet-haqida`), «Rektor murojaati» (ism va surat `GET /leadership` dan, → `/rektorat`), «Video tur» (→ `/video-darsliklar`). `about.*` matnlari 4 tilda yangilandi. Testlar: `test:pages`, `test:seo`, `test:last-good`. — `cb2231b`

- **Sayt (bosh sahifa):** «O‘qitiladigan tillar» haqiqiy karusel: o‘zi har ~3 soniyada bir karta suriladi, oxiriga yetganda boshiga qaytadi; strelkalar ham aylanadi (boshida «oldingi» — oxiriga); kursor/fokus ustida, yashirin tabda yoki «harakatni kamaytir» yoqilganda to‘xtaydi. — `44801b0`

- **Sayt (bosh sahifa, tuzatishlar):** slayder yuqoriroq, qabul paneli uni qoplamaydi (strelkalar/nuqtalar ko‘rinadi); «O‘qitiladigan tillar» — kursor kelganda ko‘tariladigan/buriladigan kartalar, har bir til ostida shu tilda o‘qitiladigan yo‘nalishlar va fakultetlar soni; «Qabul» bloki maketdagidek: 4 qadam gorizontal chiziqda + mint harakat kartasi. API: `GET /home` → `languages[]` ga `programs` va `faculties` (Program.language bo‘yicha hisoblanadi; admin ish qilmaydi). Talabalar soni til bo‘yicha hozircha yo‘q (HEMIS’da til kesimi bog‘lanmagan). — `fd2ce11`

- **Sayt (bosh sahifa, to‘liq qayta dizayn):** slayder tagida qisman ustiga chiqib turuvchi «Qabul» paneli va so‘nggi yangiliklar (eski hero-qidiruv va salomlashuv kartasi olib tashlandi; qidiruv sarlavhada qoladi); «Yaqin tadbir» yo‘lagi; 11 tildagi salomlashuv tasmasi; xizmatlar tasmasi (`QuickLinks`) «Universitet haqida» tagida, bir xil kenglikda, yumaloq konteynerda; tillar — rangli siljiydigan karusel (strelkalar bilan; yangi `languages.prev/next` kalitlari 4 tilda); tadbirlar — och fonli band; hamkorlar — to‘q indigo konteynerda. Ichki sahifalar va sarlavha o‘zgarmadi. — `d7e602d`

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
