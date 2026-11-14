# Metabase — конфигурация запуска (bare docker run)

Сервис развёрнут НЕ через compose, а голым `docker run` (нет `/opt`-каталога, нет volume).
Состояние хранится в PostgreSQL (`172.17.0.1:5432`, база `metabase`).

## Команда запуска (с маскированным паролем)

```bash
docker run -d --name metabase --restart unless-stopped \
  -p 3003:3000 \
  -e MB_DB_TYPE=postgres \
  -e MB_DB_HOST=172.17.0.1 \
  -e MB_DB_PORT=5432 \
  -e MB_DB_DBNAME=metabase \
  -e MB_DB_USER=metabase \
  -e MB_DB_PASS=<ПАРОЛЬ_ЗАМАСКИРОВАН> \
  -e MB_JETTY_PORT=3000 \
  -e JAVA_OPTS="-Xmx1280m -Xms256m -XX:+UseG1GC" \
  metabase/metabase:latest
```

## Домен

`metabase.aimentorcrm.com` → `172.17.0.1:3003` (NPM proxy host id=8).

## Примечания

- Пароль БД — в live-конфиге контейнера (`docker inspect metabase`), в этот репозиторий НЕ добавлять.
- JVM: heap 1280m. На constrained-сервере не задавать `-XX:MaxMetaspaceSize`.
- Нет volume → плагины пишутся в writable-слой контейнера; при пересоздании переустанавливаются.
