# ÖzDJTU sayti (uzswlu.uz yangi versiyasi)

| Papka | Nima | Manzil (localhost) |
|---|---|---|
| `frontend/` | Sayt — Nuxt 4, Tailwind 4, 4 til (uz, ru, en, zh) | http://localhost:3000 |
| `admin/` | Admin panel — Vue 3, Vite, Tailwind 4, TipTap | http://localhost:5173 |
| `backend/` | API va CMS — Django 5 + DRF, PostgreSQL 17, Swagger (JWT) | http://localhost:8000 |

Swagger: http://localhost:8000/api/docs/ · batafsil: [backend/README.md](backend/README.md)

## Ishga tushirish

Kerak: Docker Desktop, Node.js 22.

```bash
cp .env.docker.example .env.docker
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

`.env` fayllardagi parol va kalitlarni o'zgartiring, keyin:

```bash
docker compose up -d
```

Backend va baza Docker'da ishlaydi (loyiha nomi `uzswlu-drf`, baza porti 5433). Birinchi ishga tushishda superadmin va namunaviy ma'lumotlar o'zi yaratiladi.
Payload'dagi mavjud ma'lumotni ko'chirish: `docker compose exec backend python manage.py import_payload --replace`.

```bash
cd admin && npm install && npm run dev
```

```bash
cd frontend && npx npm@11 install && npm run dev
```

## Eslatmalar

- `.env` fayllar, `node_modules` va admin panelda yuklangan fayllar (`backend/media`) repozitoriyga kirmaydi.
- HEMIS hali ulanmagan: `backend/seed_data/hemis-snapshot.json` — namunaviy ma'lumot. Ulash — `backend/README.md` → HEMIS.
- `frontend/.env`: `NUXT_CMS_BASE=http://localhost:8000/api/site` (yoki to'liq API: `NUXT_API_BASE=http://localhost:8000/api`).
- Windows'da `.sh` skriptlar LF bilan saqlanishi shart (`.gitattributes`) — aks holda Docker'da `docker-entrypoint.sh: no such file or directory`.
