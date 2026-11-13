# nginx + admin panel (statik). Build konteksti — loyiha ildizi:  docker compose -f docker-compose.prod.yml build nginx
FROM node:24-alpine AS admin
WORKDIR /app
COPY admin/package.json admin/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY admin/ .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=admin /app/dist /usr/share/nginx/admin
# *.template dagi ${O'ZGARUVCHI} lar ishga tushishda muhitdan to'ldiriladi (nginx rasmiy imidji)
COPY deploy/nginx/uzswlu.conf.template /etc/nginx/templates/default.conf.template
