#!/usr/bin/env bash
# Hamma testlar: backend (Django) + frontend (Node) + admin (tur tekshiruvi, node_modules bo'lsa).
#   scripts/test.sh          — to'liq
#   scripts/test.sh --fast   — sekin (`slow`) testlarsiz
set -euo pipefail
cd "$(dirname "$0")/.."
args=(--parallel)
[[ "${1:-}" == "--fast" ]] && args+=(--exclude-tag=slow)

echo "▶ backend"; (cd backend && python manage.py test "${args[@]}")
echo "▶ frontend (server/utils)"; (cd frontend && npm run --silent test:last-good)
if [[ -d admin/node_modules ]]; then echo "▶ admin (vue-tsc)"; (cd admin && npm run --silent typecheck); else echo "· admin: node_modules yo'q — tur tekshiruvi o'tkazib yuborildi (cd admin && npm ci)"; fi
echo "✔ hammasi o'tdi"
