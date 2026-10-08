# Развёртывание: html-to-pdf

```bash
# 1) Gotenberg (движок)
docker run -d --name gotenberg -p 3000:3000 gotenberg/gotenberg:8

# 2) html2pdf-api
docker compose up -d --build

# 3) проверка
curl -s http://localhost:3000/health
curl -s -X POST http://localhost:3000/convert \
  -H "Content-Type: application/json" \
  -d '{"html":"<html><body><h1>Test</h1></body></html>","filename":"test"}'
```

## Требования
- `GOTENBERG_URL` указывает на gotenberg-контейнер (внутреннее имя `gotenberg:3000`).
- В `compose.yaml` `PUBLIC_BASE` — внешний адрес, по которому отдаются PDF-ссылки.
