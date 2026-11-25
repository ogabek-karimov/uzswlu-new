#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_demo --first-run   # faqat bo'sh bazada; keyingi ishga tushishda admin o'chirgan kontent qaytib kelmaydi
python manage.py check 2>&1 | grep -E 'WARNINGS|uzswlu\.W|HINT|System check' || true
if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
  exec python manage.py runserver 0.0.0.0:8000
fi
# Jarayonlar soni: WEB_CONCURRENCY bo'sh bo'lsa — CPU bo'yicha (2 × yadro + 1, ko'pi bilan 9; har biri ~50 MB xotira).
# Yuk sinovi (2026-11-25): sukut 3 × 2 = 6 ta parallel ishchi keshsiz so'rovlarda navbat hosil qilib, 504 berardi.
CPUS=$(nproc 2>/dev/null || echo 1)
AUTO_WORKERS=$(( CPUS * 2 + 1 > 9 ? 9 : CPUS * 2 + 1 ))
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-$AUTO_WORKERS}" --threads "${WEB_THREADS:-4}" --worker-class gthread --backlog 2048 \
  --timeout "${WEB_TIMEOUT:-30}" --graceful-timeout 20 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 100 --limit-request-line 4094 --limit-request-fields 60
