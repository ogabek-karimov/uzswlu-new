# ÖzDJTU backend (Django + DRF)

Frontend shartnomasi: `frontend/docs/openapi.yaml`. Admin: Django Jazzmin (`/admin/`).

## Ishga tushirish (Docker)
```
cp backend/.env.example backend/.env     # SECRET_KEY, SUPERADMIN_PASSWORD ni o'zgartiring
docker compose up -d
```
API: http://localhost:3001/api, admin: http://localhost:3001/admin/

## Lokal (Postgres'siz)
```
cd backend && pip install -r requirements.txt
export DEBUG=true DATABASE_URL=sqlite:///db.sqlite3 SUPERADMIN_PASSWORD=...
python manage.py migrate && python manage.py seed_demo && python manage.py runserver 3001
```

## Frontend sozlamasi
`NUXT_API_BASE=http://localhost:3001/api`, `NUXT_API_TOKEN=<API_TOKEN>`,
`NUXT_CMS_BASE=http://localhost:3001/api/site` (yangiliklar va /hit uchun).

## Xodim kabineti
HEMIS/my.gov orqali kirish hali ulanmagan. Sinov uchun token:
`python manage.py issue_staff_session <hemis_id>` → `Authorization: Bearer <token>`.
HEMIS hozir `seed_data/hemis-snapshot.json` dan o'qiladi (`apps/hemis/base.py` — adapter).

## Hali yo'q
Vue admin uchun `/api/admin/*`, post versiyalari/korzina, haqiqiy HEMIS login.
