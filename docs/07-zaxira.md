# 7. Zaxira nusxa (backup) va tiklash

## Nima zaxiralanadi

Bitta arxiv `backend/backups/uzswlu-YYYYMMDD-HHMMSS.tar.gz` (+ yonida `.json`: hajm, sha256, baza turi, qadalganmi):

| Ichida | Nima |
|---|---|
| `db.pgdump` / `db.sqlite3` / `db.jsonl` | baza (PostgreSQL → `pg_dump`; SQLite → ichki API; `BACKUP_DB_FORMAT=json` → ko‘chma) |
| `media/` | admin yuklagan rasm va fayllar |
| `private/` | fuqarolar murojaati ilovalari (yopiq) |
| `manifest.json` | qachon, qaysi baza, nechta fayl |

**Zaxiraga kirmaydi**: `.env` (kalitlar) — uni alohida, xavfsiz joyda saqlang. Kod git'da.

## Avtomatik ishlashi

`nightly` xizmati har kuni (HEMIS dan **oldin**) zaxira oladi → olingan nusxani **qayta o‘qib tekshiradi** (sha256, arxiv butunligi, `integrity_check` / `pg_restore --list`) → siyosatga ko‘ra eskilarini tozalaydi → `BACKUP_COPY_TO` berilgan bo‘lsa ikkinchi joyga nusxa (sha256 solishtiriladi).

Zaxira yiqilsa ham HEMIS sinxronlash va boshqa kechki vazifalar davom etadi (xato logda: `docker compose logs nightly`).

## Saqlash siyosati

| Oyna | Nima qoladi | Sozlama |
|---|---|---|
| oxirgi 14 kun | hammasi (qo‘lda olinganlari ham) | `BACKUP_KEEP_DAYS` |
| 14 kun – 8 hafta | har haftadan eng oxirgisi | `BACKUP_KEEP_WEEKS` |
| 8 hafta – 12 oy | har oydan eng oxirgisi | `BACKUP_KEEP_MONTHS` |
| 12 oydan eski | har yildan eng oxirgisi, abadiy (`0`) | `BACKUP_KEEP_YEARS` |

Doim qoladi: **qadalgan** nusxalar va eng yangi `BACKUP_KEEP_MIN` (3) tasi. `BACKUP_KEEP_DAYS=0` — hech narsa o‘chmaydi. Yillar o‘tsa ham ≈ 40 ta nusxa.

## Buyruqlar

Docker'da: `docker compose exec backend python manage.py …`

| Maqsad | Buyruq |
|---|---|
| Hozir zaxira olish | `backup` |
| Faqat baza (mediasiz) | `backup --no-media` |
| Ro‘yxat (har biri qaysi oynada) | `backup --list` |
| Nima o‘chishini oldindan ko‘rish | `backup --plan` (hech narsa o‘chirmaydi) |
| Ortiqchalarini hozir tozalash | `backup --prune` |
| Butunligini tekshirish | `backup --verify latest` (yoki fayl nomi) |
| Qadash / bekor qilish | `backup --pin FAYL` / `backup --unpin FAYL` |
| Sanaga eng yaqin nusxalar | `backup --find 2026-08-15` |
| Zaxira yangimi? (monitoring) | `backup --status` — eskirgan bo‘lsa xato kodi (≥ 36 soat: `BACKUP_MAX_AGE_HOURS`) |
| Tiklash | `restore latest --yes` · `restore 2026-08-15 --yes` · `restore FAYL --yes` |
| Faqat baza / faqat fayllar tiklash | `restore … --db-only` / `--media-only` |

## Vaziyatlar

### A) Katta o‘zgarish (yangilanish, ommaviy tahrir) oldidan

```bash
docker compose exec backend python manage.py backup --label oldin
docker compose exec backend python manage.py backup --pin uzswlu-YYYYMMDD-HHMMSS-oldin.tar.gz
```

### B) Kimdir post/sahifani o‘chirib yubordi (kecha edi)

1. `backup --find 2026-11-09` — shu sanaga yaqin nusxani ko‘ring.
2. **Butun bazani qaytarish shart emas** bo‘lishi mumkin: avval admin panelda «Savat» va «Versiyalar» (postlar va sozlamalar versiyasi) ni tekshiring.
3. Baribir tiklash kerak bo‘lsa — `restore` bo‘limiga (C) qarang. Tiklashdan keyingi kiritilgan o‘zgarishlar **yo‘qoladi** — shuning uchun oldin `pre-restore` nusxasi olinadi.

### C) Tiklash

```bash
docker compose stop backend nightly                                   # ochiq ulanishlar bazani bloklamasin
docker compose run --rm backend python manage.py restore 2026-08-15 --yes   # yoki latest / fayl nomi
docker compose up -d
```

Tiklashdan oldin joriy holatdan `…-pre-restore.tar.gz` olinadi — xato bo‘lsa shunga qaytish mumkin. `--yes`siz hech narsa o‘zgarmaydi. Tiklashdan keyin `migrate` avtomatik ishlaydi (zaxira eski bo‘lsa yangi migratsiyalar qo‘llanadi) va kesh tozalanadi.

### D) Server butunlay yo‘qoldi — yangisiga ko‘chirish

1. Yangi serverda loyihani o‘rnating, `.env` fayllarni (alohida saqlangan) qo‘ying.
2. `docker compose up -d db`
3. Zaxira arxivini (va `.json` ni) `backend/backups/` ga qo‘ying (tashqi nusxadan: `BACKUP_COPY_TO`).
4. `docker compose run --rm backend python manage.py restore FAYL --yes` → `docker compose up -d`.

### E) PostgreSQL → SQLite (yoki aksincha) ko‘chirish

Manba muhitda `BACKUP_DB_FORMAT=json` bilan zaxira oling, maqsad muhitda `migrate` qilib `restore FAYL --yes` ishlating (`pgdump` ↔ `sqlite` formatlari faqat o‘z bazasiga tiklanadi).

## Qoidalar va tavsiyalar

- **Faqat shu serverdagi zaxira yetarli emas**: `BACKUP_COPY_TO` (boshqa disk/ulangan tarmoq papkasi) yoki `backups/` ni `rsync`/`rclone` bilan tashqariga oling (`uzswlu.W009` ogohlantiradi).
- Zaxiralar maxfiy ma’lumot (parol xeshlari, fuqaro murojaatlari) — `backups/` git'ga tushmaydi, unga ruxsatni cheklang.
- Tiklashni **vaqti-vaqti bilan sinab ko‘ring** (alohida bo‘sh bazada): tekshirilmagan zaxira — zaxira emas.
- Monitoring: cron yoki uptime-xizmatdan `backup --status` ni chaqiring — kechikkan zaxira haqida xabar beradi.
- PostgreSQL'da `pg_dump` versiyasi server versiyasidan past bo‘lmasin (image'da 17, `db` ham 17).
- Joy: media har kuni to‘liq arxivlanadi; media gigabaytlarga yetsa, `BACKUP_KEEP_*` ni qisqartiring yoki `BACKUP_MEDIA=false` qilib mediani alohida (`rsync`) zaxiralang.

Kod: `backend/apps/core/backup.py`; buyruqlar: `commands/backup.py`, `commands/restore.py`; testlar: `backend/tests/core/test_backup.py`.
