# 1. Boshlash: o‘rnatish va kundalik buyruqlar

## Nima kerak

| Dastur | Nima uchun |
|---|---|
| Docker Desktop (Compose) | backend, baza, nightly, sayt va admin — hammasi konteynerda |
| Node.js 22 | faqat konteynersiz ishlatsangiz yoki testlar/`typecheck` uchun |
| Python 3.13 | faqat backendni konteynersiz (lokal) ishga tushirsangiz yoki testlar uchun |
| Git | — |

## Birinchi ishga tushirish

```bash
cp .env.docker.example .env.docker        # PostgreSQL foydalanuvchi/parol
cp backend/.env.example backend/.env      # backend sozlamalari
cp frontend/.env.example frontend/.env    # sayt sozlamalari
```

`.env` fayllarda **o‘zgartiring**:

1. `.env.docker` → `POSTGRES_PASSWORD`; `backend/.env` → `DATABASE_URL` dagi parol **aynan shu bilan bir xil** bo‘lsin.
2. `backend/.env` → `SECRET_KEY` (uzun tasodifiy), `SUPERADMIN_PASSWORD` (birinchi superadmin paroli).
3. `API_TOKEN` (backend) = `NUXT_API_TOKEN` (frontend) — ikkalasida bir xil. Lokalda bo‘sh qoldirsangiz tekshirilmaydi.

Tasodifiy kalit: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

```bash
docker compose up -d
```

Birinchi ishga tushish **1–2 daqiqa** oladi: `backend` konteyneri migratsiyalarni qo‘llaydi, statik fayllarni yig‘adi, **bo‘sh bazaga** namunaviy kontent va superadmin yaratadi (`seed_demo --first-run`), `manage.py check` ogohlantirishlarini chiqaradi. Keyingi ishga tushishlarda admin o‘chirgan kontent qaytib kelmaydi.

| Xizmat | Vazifasi |
|---|---|
| `db` | PostgreSQL 17 (ma’lumot `pgdata` volume'da) |
| `backend` | Django API (Docker'da `DEBUG=true` bo‘lsa `runserver`, aks holda gunicorn). Sog‘liq tekshiruvi: `/healthz` |
| `nightly` | kechki vazifalar: zaxira, HEMIS sinxronlash, tozalash ([08-hemis-kesh](08-hemis-kesh.md)) |
| `frontend` | Nuxt sayti (:3000) |
| `admin` | Vue admin panel (:5173) |

## Kirish

- Admin panel: http://localhost:5173 → login `superadmin` (yoki `SUPERADMIN_USERNAME`), parol — `SUPERADMIN_PASSWORD`.
- Sayt: http://localhost:3000 · Swagger: http://localhost:8000/api/docs/

> Superadmin faqat foydalanuvchilar **bo‘sh** bo‘lganda yaratiladi. Productionda (`DEBUG=false`) 12 belgidan qisqa yoki oddiy parol bilan yaratilmaydi.

## Kundalik buyruqlar

| Nima qilish | Buyruq |
|---|---|
| Holatni ko‘rish | `docker compose ps` |
| Log (jonli) | `docker compose logs -f backend` (yoki `nightly`, `frontend`, `admin`, `db`) |
| Qayta ishga tushirish | `docker compose restart backend` |
| Kod o‘zgarsa (Python) | `backend/` papkasi konteynerga ulangan — dev server o‘zi qayta yuklaydi |
| Kutubxona (`requirements.txt`) o‘zgarsa | `docker compose up -d --build backend nightly` |
| Django buyrug‘i | `docker compose exec backend python manage.py <buyruq>` |
| Baza qobig‘i | `docker compose exec backend python manage.py shell` |
| SQL qobig‘i | `docker compose exec db psql -U uzswlu uzswlu` |
| To‘xtatish (ma’lumot saqlanadi) | `docker compose down` |
| ⚠️ Bazani **butunlay o‘chirish** | `docker compose down -v` — `pgdata` volume yo‘qoladi! Avval `backup` oling |

Barcha `manage.py` buyruqlari: [reference → buyruqlar](reference.md).

## Konteynersiz (lokal, Postgres'siz)

```bash
cd backend && pip install -r requirements.txt
export DEBUG=true DATABASE_URL=sqlite:///db.sqlite3 SUPERADMIN_PASSWORD=...
python manage.py migrate && python manage.py seed_demo && python manage.py runserver 8000
```

SQLite bilan statistika (`/panel/stats`) va Payload'dan ko‘chirish ishlamaydi — ular faqat PostgreSQL'da. Admin: `cd admin && npm install && npm run dev`, sayt: `cd frontend && npx npm@11 install && npm run dev`.

## Windows'da bilib qo‘ying

- `.sh` fayllar **LF** bilan saqlanishi shart (`.gitattributes` buni ta’minlaydi). Aks holda Docker'da `docker-entrypoint.sh: no such file or directory`.
- Port band bo‘lsa (`ports are not available`): sababini `netstat -ano | findstr ":8000"` ko‘rsatadi (ko‘pincha `netsh interface portproxy` qoidasi). Ildiz `.env` fayliga `BACKEND_PORT=3001` yozing va `backend/.env` da `PUBLIC_SERVER_URL=http://localhost:3001` qiling.
- Windows papkasidagi o‘zgarishlar konteynerga `CHOKIDAR_USEPOLLING` bilan uzatiladi (sozlangan).
- Testlar: PowerShell'da `.\scripts\test.ps1`.

## Keyingi qadam

[02-tuzilma](02-tuzilma.md) — papkalar va arxitektura bilan tanishing, so‘ng kerakli bo‘limga o‘ting ([bosh sahifa](README.md) jadvali).
