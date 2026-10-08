# Быстрое развёртывание: document-template-rendering

```bash
docker compose up -d
curl http://localhost:4000/status

# загрузить шаблон
curl -X POST http://localhost:4000/template \
  -H "carbone-version: 5" -H "Content-Type: application/json" \
  -d '{"template": "<base64_docx>"}'

# рендер (сразу файл, pdf)
curl -X POST "http://localhost:4000/render/{templateId}?download=true" \
  -H "carbone-version: 5" -H "Content-Type: application/json" \
  -d '{"data": {"name": "…", "positions": []}, "convertTo": "pdf"}'
```

## docker-compose.yml

```yaml
services:
  carbone:
    image: carbone/carbone-ee:latest
    restart: unless-stopped
    ports: ["4000:4000"]
    environment:
      CARBONE_BIND: 0.0.0.0     # иначе слушает только 127.0.0.1
    volumes:
      - ./template:/app/template
      - ./render:/app/render
      - ./config:/app/config    # лицензионный ключ
```

## Pitfalls
- Контейнер работает под UID 1000 — каталогам нужен `chown 1000:1000`, иначе EACCES.
- Образ `latest` включает LibreOffice (PDF работает; у `slim` — нет).
