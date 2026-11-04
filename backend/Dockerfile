FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Entrypoint /app dan tashqarida (bind-mount ustidan yopmasin) va Windows CRLF'dan tozalanadi
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh && chmod +x /usr/local/bin/docker-entrypoint.sh
COPY . .
EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
