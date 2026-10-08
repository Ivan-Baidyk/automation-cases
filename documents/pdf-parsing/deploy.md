# Быстрое развёртывание: pdf-document-parsing

```bash
docker build -t docling-serve-cpu .   # Dockerfile из этого каталога
docker compose up -d
curl http://localhost:5001/health
```

## Требования к ресурсам
`mem_limit: 6g`, `shm_size: 512m` — модели грузятся в память при старте.

## docker-compose.yml

```yaml
services:
  docling:
    image: docling-serve-cpu:latest
    restart: unless-stopped
    ports: ["5001:5001"]
    environment:
      DOCLING_SERVE_ENABLE_UI: "true"
      DOCLING_SERVE_LOAD_MODELS_AT_BOOT: "true"
      DOCLING_DEVICE: cpu
    mem_limit: 6g
    shm_size: 512m
```
