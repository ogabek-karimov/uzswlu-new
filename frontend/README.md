# UzSWLU — yangi sayt (frontend)

O‘zbekiston davlat jahon tillari universiteti saytining yangi frontendi.
Stack: **Nuxt 4 (Vue 3) + Tailwind CSS 4 + @nuxtjs/i18n**. Tillar: `uz` (asosiy), `ru`, `en`, `zh`.

## Ishga tushirish

```bash
npm install
npm run dev        # http://localhost:3000
```

> Node versiyasi: hozir `22.13.1` bilan ishlashi uchun Nuxt `4.4.8` ga qotirilgan.
> Node 24 LTS'ga o‘tilgach, Nuxt'ni so‘nggi versiyaga ko‘tarish mumkin.

## Tuzilma

```
app/
  pages/index.vue          bosh sahifa
  components/home/*        bosh sahifa bloklari (Hero, Faculties, News ...)
  components/The*.vue      yuqori panel, sarlavha (mega-menyu), footer
  utils/navigation.ts      menyu tuzilmasi
i18n/locales/*.json        interfeys matnlari (4 til)
server/api/*.get.ts        Nuxt server — backend oldidagi oraliq qatlam
server/utils/mock-home.ts  backend tayyor bo‘lguncha vaqtinchalik ma’lumot
shared/types/api.ts        API shartnomasi (TypeScript turlari)
docs/openapi.yaml          API shartnomasi (backend uchun, OpenAPI 3.1)
public/slides, public/logos  uzswlu.uz'dan olingan rasmlar (WebP'ga siqilgan)
```

## Backend bilan ulanish

Brauzer backend'ga to‘g‘ridan-to‘g‘ri murojaat qilmaydi:
`brauzer → Nuxt server (/api/*) → backend API → HEMIS`.
Token faqat Nuxt serverida turadi, javoblar keshlanadi.

`.env`:

```
NUXT_API_BASE=https://api.example.uz   # bo‘sh bo‘lsa — mock ma’lumot
NUXT_API_TOKEN=...
```

### Backend qaytarishi kerak bo‘lgan endpointlar

To‘liq shartnoma: **[`docs/openapi.yaml`](docs/openapi.yaml)** (Swagger Editor'da ochiladi).
Frontenddagi TypeScript turlari: [`shared/types/api.ts`](shared/types/api.ts) — ikkalasi bir xil.

| Endpoint | Tur | Mazmuni |
|---|---|---|
| `GET /home?lang=` | `HomeData` | karusel bannerlari, statistika (HEMIS), fakultetlar, yangiliklar, e’lonlar, tadbirlar, tillar, hamkorlar |
| `GET /site?lang=` | `SiteData` | asosiy menyu (8 bo‘lim, 70+ sahifa), telefon, e-pochtalar, binolar, ijtimoiy tarmoqlar |

Asosiy qoidalar:

- `?lang=uz|ru|en|zh` — matnlar shu tilda; tarjima bo‘lmasa o‘zbekcha qaytadi.
- Rasm va logolar — to‘liq URL (`https://...`).
- Statistika — **aniq son** (`17384`); "17K+" ko‘rinishiga frontend o‘zi keltiradi.
- Sana — ISO 8601; tadbir vaqti mintaqa bilan (`2026-11-07T10:00:00+05:00`).
- Karusel bannerlari **16:9 bo‘lishi shart** (1920×1080, WebP, 500 KB gacha) — shunda chetdan chetgacha to‘liq ko‘rinadi.
  Admin panelda yuklashda nisbatni tekshirish kerak.

Namuna javoblarni ko‘rish: `npm run dev`, so‘ng `http://localhost:3000/api/home?lang=ru`.

### Frontendda qolgan (API'ga ulanmagan) qismlar

Interfeys matnlari (`i18n/locales`), tezkor xizmatlar, qabul bosqichlari va "Kirish" havolalari
(HEMIS, KPI) — kam o‘zgaradi, kerak bo‘lsa keyin CMS'ga ko‘chiriladi.

### Menyu

Menyu `/site` javobida keladi. Sahifa manzillari hozirgi sayt bilan bir xil (`/universitet-haqida`,
`/qabul-20262027` …) — eski havolalar va Google'dagi o‘rinlar saqlanadi.
Navbar sig‘magan bo‘limlarni o‘zi "⋯" tugmasi ichiga oladi (ekran torayganda, shrift kattalashtirilganda
yoki uzun tillarda) — backend buni o‘ylashi shart emas.
