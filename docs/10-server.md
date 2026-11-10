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
