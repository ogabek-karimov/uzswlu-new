# 10. Serverga chiqarish

> Hozirgi `docker-compose.yml` — **lokal** muhit uchun (kod konteynerga ulanadi, `runserver`/dev server). Productionda `DEBUG=false` bo‘ladi: backend gunicorn bilan ishlaydi, sayt va admin esa build qilingan holda xizmat qiladi, oldida nginx (HTTPS) turadi.

## Chiqishdan oldin tekshiruv ro‘yxati

| # | Tekshiruv | Qanday | Nega |
|---|---|---|---|
| 1 | `DEBUG=false` | `backend/.env` | debug sahifasi sirni chiqarib yuboradi |
| 2 | `SECRET_KEY` — uzun tasodifiy (≥ 50 belgi) | `uzswlu.W003` | JWT va sessiyalar shunga tayanadi |
| 3 | `ALLOWED_HOSTS` — faqat o‘z domeningiz | `uzswlu.W004` | Host-sarlavha hujumi |
| 4 | `TRUSTED_ORIGINS` — faqat `https://` domenlar (localhost yo‘q) | `uzswlu.W007` | cookie/token bilan so‘rov yuboriladigan manzillar |
| 5 | `API_TOKEN` ≥ 24 belgi, frontendda `NUXT_API_TOKEN` bilan bir xil | `uzswlu.W001/W002` | ochiq API faqat saytdan |
| 6 | `NUM_PROXIES=1` (nginx), Cloudflare bilan — `2` | `uzswlu.W005` | aks holda hamma foydalanuvchi bitta IP bo‘lib qoladi |
| 7 | `API_DOCS_PUBLIC=false` | `uzswlu.W006` | Swagger faqat admin kirganlarga |
| 8 | `BACKUP_ENABLED=true`, `BACKUP_DIR` alohida diskda, `BACKUP_COPY_TO` to‘ldirilgan | `uzswlu.W008/W009` | disk buzilsa hammasi yo‘qolmasin |
| 9 | `SUPERADMIN_PASSWORD` kuchli (≥ 12 belgi) | — | birinchi superadmin shu bilan yaratiladi |
| 10 | `REQUIRE_2FA_ROLES=superadmin` (tavsiya) | — | admin hisobini o‘g‘irlashdan himoya |
| 11 | `COOKIE_SECURE=true` (sukut), HTTPS ishlayapti | brauzerda qulf belgisi | cookie faqat HTTPS orqali |
| 12 | `PUBLIC_SERVER_URL=https://api.sizning.uz` | `.env` | media havolalari to‘g‘ri chiqishi uchun |
| 12a | **`NUXT_PUBLIC_SITE_URL=https://sizning.uz`** (`frontend/.env`) | `curl https://sizning.uz/sitemap.xml \| head` — manzillar `localhost` emas, domen bilan boshlansin | canonical, hreflang, sitemap va Telegram preview shundan; aks holda qidiruv tizimlariga `localhost` ko‘rsatiladi |
| 13 | HEMIS: `HEMIS_API_URL`, `HEMIS_API_TOKEN` | [08-hemis-kesh](08-hemis-kesh.md) | bo‘sh bo‘lsa — namuna ma’lumot |
| 14 | `pgdata`, `media`, `private`, `backups` — doimiy volume | `docker volume ls` | konteyner o‘chsa ma’lumot saqlansin |

Hammasini bitta buyruq tekshiradi:

```bash
docker compose exec backend python manage.py check --deploy
docker compose exec backend python manage.py check        # uzswlu.W00x ogohlantirishlari
docker compose exec backend python manage.py backup --status
```

Natija **ogohlantirishsiz** bo‘lsa — sozlamalar to‘g‘ri.

## Server tuzilmasi (tavsiya)

```
Internet ─► nginx :443 (HTTPS)
              ├─ sizning.uz          ─► Nuxt server   127.0.0.1:3000
              ├─ admin.sizning.uz    ─► statik fayllar (admin/dist) + /api/ ─► backend
              └─ api.sizning.uz      ─► backend       127.0.0.1:8000  (+ /media/ to‘g‘ridan-to‘g‘ri)
Backend ─► PostgreSQL (tashqaridan yopiq)
```

- Baza porti (`5433`) **tashqariga ochilmasin** (`127.0.0.1` ga bog‘langan).
- `private/` papkasi (xodim hujjatlari) nginx orqali **ochilmaydi** — faqat backend (ruxsat tekshiruvi bilan) beradi.

## nginx namunasi (api va admin)

```nginx
# /etc/nginx/conf.d/uzswlu.conf — o‘zingizning domeningizga moslang
server {
  listen 443 ssl http2;
  server_name api.sizning.uz;
  # ssl_certificate / ssl_certificate_key — Let's Encrypt (certbot)

  client_max_body_size 25m;                 # yuklash chegarasi backenddagi BODY_LIMITS/UPLOAD_LIMITS bilan mos

  location /media/ {                        # yuklangan ochiq rasmlar
    alias /srv/uzswlu/media/;
    expires 7d;
    add_header X-Content-Type-Options nosniff;
  }
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;   # NUM_PROXIES=1 shunga tayanadi
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 40s;
  }
}

server {
  listen 443 ssl http2;
  server_name admin.sizning.uz;
  root /srv/uzswlu/admin-dist;              # cd admin && npm run build
  location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host api.sizning.uz;
                   proxy_set_header X-Forwarded-For $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; }
  location / { try_files $uri /index.html; }    # SPA marshrutlari
}
```

> `X-Forwarded-For` ni **ustiga yozing** (`$remote_addr`), `$proxy_add_x_forwarded_for` emas — aks holda foydalanuvchi soxta IP yuborib so‘rov cheklovini aylanib o‘tadi.

## Yuklama va tezlik (1000+ bir vaqtdagi foydalanuvchi)

**Sinov natijasi (sandbox, 2 yadro, SQLite — taxminiy):** backend API ~500 so‘rov/soniya beradi, 1000 so‘rov bir lahzada kelsa ham hammasi ~3 soniyada, xatosiz javob oladi (o‘rtacha so‘rov — 5 ms). Sayt tomoni (Nuxt, sahifani serverda chizish) sinalmagan — u eng og‘ir qism, shuning uchun quyidagi qatlamlar kerak.

So‘rov yo‘li va har qatlamdagi kesh — foydalanuvchi baza yoki HEMIS’gacha deyarli yetib bormaydi:

| Qatlam | Nima qiladi | Muddat |
|---|---|---|
| nginx `proxy_cache` | tayyor sahifa HTML’i, Node’ga so‘rov bormaydi | 60 s (+ eskirgan nusxa xatoda) |
| Nuxt `routeRules` (`frontend/nuxt.config.ts`) | bosh sahifalar (4 til) Node’da stale-while-revalidate; boshqa sahifalarga `s-maxage=60` sarlavhasi | 60 s |
| Nuxt `server/api` kesh | `/api/home` va boshqalar | 5 daqiqa |
| «Oxirgi yaxshi javob» | backend o‘chsa, saqlangan nusxa | 3 soat |
| Backend ochiq javob keshi (`PUBLIC_CACHE_SECONDS`) | bazaga qayta bormaydi, kontent o‘zgarsa darhol yangilanadi; **to‘dan himoya**: muddati tugaganda (yoki kesh bo‘shaganda) bazaga bitta so‘rov boradi, qolgan minglablari eski nusxani oladi yoki natijani kutadi (`PUBLIC_CACHE_STALE_SECONDS`) | 60 s (+ 300 s eski nusxa) |

**HEMIS ta’siri:** ochiq sahifa so‘rovi HEMIS’ga **bormaydi** — talaba/xodim ma’lumotlari bazadagi nusxadan o‘qiladi (`HEMIS_CACHE_SECONDS`), nusxa esa alohida sinxronlash bilan yangilanadi. HEMIS sekin yoki o‘chiq bo‘lsa, sayt eski nusxani ko‘rsatadi, qotmaydi (o‘chirgich: `backend/apps/hemis/guard.py`). Faqat HEMIS orqali **kirish** (OAuth) HEMIS’ga boradi — u alohida cheklangan (`THROTTLE_HEMIS_AUTH`).

### Nginx: sayt uchun kesh va bir nechta Node nusxasi

```nginx
proxy_cache_path /var/cache/nginx/uzswlu levels=1:2 keys_zone=site:50m max_size=1g inactive=10m use_temp_path=off;

upstream nuxt {                       # Node bitta yadroda ishlaydi — yadro soniga qarab nusxa ishga tushiring
  least_conn;
  server 127.0.0.1:3000;
  server 127.0.0.1:3001;              # PORT=3001 node .output/server/index.mjs
  keepalive 64;
}

server {
  listen 443 ssl http2;
  server_name sizning.uz;

  location /_nuxt/ {                  # fayl nomida xesh bor — bir yil keshlanadi
    proxy_pass http://nuxt;
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
  location / {
    proxy_pass http://nuxt;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_cache site;
    proxy_cache_valid 200 60s;        # sayt `Cache-Control` bergan sahifalar (kabinet, qidiruv) keshlanmaydi
    proxy_cache_lock on;              # bir xil sahifaga 1000 ta so‘rov — Node’ga bittasi boradi
    proxy_cache_background_update on;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
    add_header X-Cache $upstream_cache_status;   # HIT/MISS/STALE — tekshirish uchun
  }
}
```

Backend (gunicorn) uchun: `WEB_CONCURRENCY` ≈ yadro soni × 2 + 1, `WEB_THREADS` 2–4 (standart 3×2 — kichik server uchun). Kesh umumiy bo‘lishi uchun productionda **Redis** (`REDIS_URL`) bo‘lsin, aks holda har gunicorn jarayoni alohida kesh va alohida so‘rov-cheklov hisoblagichi yuritadi.

**Production’da tekshirish** (ishga tushirgach, 1–2 daqiqa): `curl -sI https://sizning.uz/ | grep -i x-cache` ikkinchi marta `HIT` bo‘lishi kerak; `hey -n 1000 -c 200 https://sizning.uz/` (yoki `ab`) natijasida xato 0 va p95 ~100 ms dan past bo‘lishi kerak.

## Sayt SEO (qidiruv va ijtimoiy tarmoq)

| Tekshiruv | Qanday |
|---|---|
| `https://sizning.uz/robots.txt` oxirida `Sitemap: https://sizning.uz/sitemap.xml` | brauzer / `curl` |
| `/sitemap.xml` ichida 4 til (`/ru/…`, `/en/…`, `/zh/…`) va yangiliklar, fakultetlar, xodimlar | `curl -s https://sizning.uz/sitemap.xml \| grep -c "<url>"` |
| Sahifa manbasida `<link rel="canonical">` va `hreflang` domen bilan | «Sahifa manbasini ko‘rish» |
| Telegram preview | havolani o‘zingizga yuboring (kesh uchun `@WebpageBot` orqali yangilanadi) |
| Google Search Console / Yandex Webmaster | `sitemap.xml` ni qo‘shing |

Nginx saytga `Host` va `X-Forwarded-Proto` ni uzatsin — `NUXT_PUBLIC_SITE_URL` bo‘sh bo‘lsa domen shulardan olinadi.

## Yangilash tartibi

1. **Zaxira**: `docker compose exec backend python manage.py backup` (katta o‘zgarishda — `backup --pin FAYL`).
2. `git pull` (faqat tekshirilgan filial).
3. `docker compose up -d --build backend nightly frontend admin` (yoki serverdagi build tizimi).
4. Backend ishga tushganda migratsiyalar avtomatik qo‘llanadi (`docker-entrypoint.sh`).
5. Tekshiruv: `docker compose ps` (hammasi `healthy`), `curl https://api.sizning.uz/healthz`, admin panelga kirish, saytda yangilik ochilishi.

## Orqaga qaytarish

| Holat | Amal |
|---|---|
| Yangi kod xato beryapti, baza o‘zgarmagan | oldingi `git` versiyasiga qaytib, qayta `up -d --build` |
| Migratsiya bazani buzdi / ma’lumot yo‘qoldi | `python manage.py restore --yes` (oxirgi zaxira) yoki `restore 2026-08-15 --yes` — [07-zaxira](07-zaxira.md) |
| Faqat media yo‘qoldi | zaxira arxividan `media/` ni tiklash ([07-zaxira](07-zaxira.md)) |

`restore` avval joriy holatning xavfsizlik nusxasini oladi, shuning uchun qaytarishni ham qaytarish mumkin.

## Kundalik monitoring

| Nima | Qanday |
|---|---|
| Server tirikmi | `/healthz` (uptime-monitorga ulang: UptimeRobot va h.k.) |
| Zaxira yangimi | `backup --status` (0 — yangi, 1 — eskirgan; cron/monitoringga mos) |
| HEMIS yangimi | Admin panel → Boshqaruv paneli (HEMIS kartasi) |
| Xatolar | `docker compose logs --since 1h backend` |
| Disk | `df -h`, `docker system df` — `backups/` va `media/` o‘sadi |
| Kutubxona zaifliklari | oyiga bir marta `pip-audit`, `npm audit` (CI ham bajaradi) |

## Keyingi qadam

Muammo chiqsa: [11-muammolar](11-muammolar.md). Zaxira: [07-zaxira](07-zaxira.md).
