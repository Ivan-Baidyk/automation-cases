# Быстрое развёртывание: web-catalog-scraper

## Требования
- Docker + Docker Compose
- PostgreSQL (для хранения каталога)

## Шаги

```bash
# 1. PostgreSQL + схема (упрощённо — таблицы suppliers/sections/products)
#    полный DDL в репозитории parser-service

# 2. Конфигурация
cp .env.example .env
# заполнить: DATABASE_URL, PARSER_API_TOKEN

# 3. Сборка и запуск
docker compose up -d --build

# 4. Проверка
curl -H "Authorization: Bearer $PARSER_API_TOKEN" http://localhost:8001/health
curl -X POST http://localhost:8001/catalog \
  -H "Authorization: Bearer $PARSER_API_TOKEN" \
  -d '{"parser_id": "my_parser", "url": "https://example.com/catalog"}'
```

## docker-compose.yml (основное)

```yaml
services:
  parser-api:
    build: .
    network_mode: host          # для доступа к БД и целевым сайтам
    restart: unless-stopped
    env_file: .env
```

## Добавление нового парсера

Реализовать плагин в реестре (3 метода: fetch_catalog / fetch_product_urls / fetch_product_details)
и зарегистрировать — см. `docs/HOW_TO_ADD_PARSER.md` в репозитории parser-service.
