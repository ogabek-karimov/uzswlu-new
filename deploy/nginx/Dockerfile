# nginx + admin panel (statik). Build konteksti — loyiha ildizi:  docker compose -f docker-compose.prod.yml build nginx
FROM node:24-alpine AS admin
WORKDIR /app
COPY admin/package.json admin/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY admin/ .
RUN npm run build

FROM nginx:1.28-alpine
COPY --from=admin /app/dist /usr/share/nginx/admin
# *.template dagi ${O'ZGARUVCHI} lar ishga tushishda muhitdan to'ldiriladi (nginx rasmiy imidji)
# Yukni rad etish chegaralari (uzswlu.conf.template → limit_conn); compose ildiz .env dan almashtiradi. Bu yerda — compose'siz ham ishlashi uchun
ENV LIMIT_CONN_PER_IP=100 LIMIT_CONN_API_PER_IP=30 LIMIT_CONN_BACKEND=300
# Asosiy sozlama: ulanishlar chegarasi (worker_connections 16384), bufer bilan log — yuk sinovidan keyin
COPY deploy/nginx/nginx.conf /etc/nginx/nginx.conf
COPY deploy/nginx/uzswlu.conf.template /etc/nginx/templates/default.conf.template
COPY deploy/nginx/security_headers.conf /etc/nginx/security_headers.conf
# REAL_IP_FROM → /etc/nginx/real_ip.conf va trusted_proxies.geo (shablondan oldin ishlaydi: 15 < 20-envsubst)
COPY --chmod=755 deploy/nginx/15-real-ip.sh /docker-entrypoint.d/15-real-ip.sh
