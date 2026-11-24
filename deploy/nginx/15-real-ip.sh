#!/bin/sh
# Oldingi ishonchli proksi (TLS: shu hostdagi nginx/certbot, Cloudflare, yuk balansirovchi) uchun sozlama — nginx ishga tushishida.
#   REAL_IP_FROM — proksi manzillari (CIDR), bo'sh joy yoki vergul bilan:  REAL_IP_FROM="172.16.0.0/12"  yoki Cloudflare diapazonlari.
# Faqat shu manzillardan kelgan so'rovda:
#   - mijozning haqiqiy IP'si X-Forwarded-For dan olinadi ($remote_addr) — backendga shu boradi (NUM_PROXIES=1 o'zgarmaydi);
#   - X-Forwarded-Proto: https ishoniladi (aks holda $scheme, ya'ni http).
# Bo'sh bo'lsa — hech kimga ishonilmaydi (avvalgi xatti-harakat). DIQQAT: port to'g'ridan-to'g'ri internetga ochiq bo'lsa,
# bu yerga keng diapazon yozmang — aks holda istalgan mijoz soxta X-Forwarded-For bilan IP'sini almashtira oladi.
set -eu

out_realip=/etc/nginx/real_ip.conf
out_geo=/etc/nginx/trusted_proxies.geo
: > "$out_realip"
: > "$out_geo"

list=$(printf '%s' "${REAL_IP_FROM:-}" | tr ',' ' ')
n=0
for cidr in $list; do
  case "$cidr" in
    *[!0-9a-fA-F.:/]*) echo "15-real-ip.sh: REAL_IP_FROM dagi noto'g'ri qiymat: $cidr" >&2; exit 1 ;;
  esac
  echo "set_real_ip_from $cidr;" >> "$out_realip"
  echo "$cidr 1;" >> "$out_geo"
  n=$((n + 1))
done
if [ "$n" -gt 0 ]; then
  echo "real_ip_header X-Forwarded-For;" >> "$out_realip"
  echo "real_ip_recursive on;" >> "$out_realip"
fi
echo "15-real-ip.sh: ishonchli proksilar: $n ta"
