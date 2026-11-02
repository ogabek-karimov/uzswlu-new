# ÖzDJTU sayti (uzswlu.uz yangi versiyasi)

| Papka | Nima | Manzil (localhost) |
|---|---|---|
| `frontend/` | Sayt — Nuxt 4, Tailwind 4, 4 til (uz, ru, en, zh) | http://localhost:3000 |
| `admin/` | Admin panel — Vue 3, Vite, Tailwind 4, TipTap | http://localhost:5173 |
| `backend/` | CMS va API — Payload 3 (Next.js), PostgreSQL 17 | http://localhost:3001 |

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

Backend va baza Docker'da ishlaydi. Birinchi ishga tushishda superadmin va namunaviy ma'lumotlar o'zi yaratiladi.

```bash
cd admin && npm install && npm run dev
```

```bash
cd frontend && npx npm@11 install && npm run dev
```

## Eslatmalar

- `.env` fayllar, `node_modules` va admin panelda yuklangan fayllar (`backend/media`) repozitoriyga kirmaydi.
- HEMIS hali ulanmagan: `backend/src/hemis/snapshot.json` — namunaviy ma'lumot.
- Payload `public` sxemasidagi o'zi bilmagan jadvalni o'chirmoqchi bo'ladi — qo'lda yaratiladigan jadvallar alohida sxemada bo'lsin (masalan, `analytics.events`).
