#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_demo
python manage.py check 2>&1 | grep -E 'WARNINGS|uzswlu\.W|HINT|System check' || true
if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
  exec python manage.py runserver 0.0.0.0:8000
fi
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 \
  --workers "${WEB_CONCURRENCY:-3}" --threads "${WEB_THREADS:-2}" --worker-class gthread \
  --timeout "${WEB_TIMEOUT:-30}" --graceful-timeout 20 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 100 --limit-request-line 4094 --limit-request-fields 60
