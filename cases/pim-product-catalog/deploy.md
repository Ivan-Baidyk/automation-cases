# Быстрое развёртывание: PIM (AtroCore)

```bash
# 1. Клонировать стек AtroCore
git clone https://github.com/atrocore/docker.git && cd docker

# 2. Отключить встроенную БД, указать внешний PostgreSQL
#    (в compose: убрать db-сервис, в .env задать DB_HOST/DB_USER/DB_PASSWORD/DB_NAME)

# 3. Создать роль + схему в PostgreSQL (под суперпользователем):
#    CREATE ROLE pim LOGIN PASSWORD '…';
#    CREATE SCHEMA pim AUTHORIZATION pim;

# 4. Запуск + установщик
docker compose up -d
#    открыть http://<host> и пройти установщик (создаёт таблицы в схеме pim)

# 5. Импорт товаров (пример скрипта):
#    python3 import_products.py   # source → PIM, EAV-атрибуты по типам
```

## Pitfalls
- AtroCore требует **выделенную** БД/схему (не шарить с другими сервисами).
- Привязка атрибутов — через EAV: тип атрибута определяет value-колонку
  (`text→text_value`, `varchar/url→varchar_value`, `float→float_value`, `bool→bool_value`, `array→json_value`).
