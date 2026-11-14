# Инвентаризация сервисов — сервер 176.98.178.8 (msk-1-vm-w24m)

> Дата снятия данных: 2026-11-14
> Хост: `176.98.178.8` (SSH-алиас `srv`, root)
> Обратный прокси: Nginx Proxy Manager (`proxy-manager`, `/root/web-project`)

## Сводка по ресурсам (на момент аудита)

| Ресурс | Значение | Оценка |
|---|---|---|
| Диск `/` | 67G / 78G used, **12G свободно (86%)** | 🔴 |
| RAM | 5.2G / 7.8G used, **swap 2.0G занят на 100%** | 🔴 |
| Docker images | 49.2 GB (96% «reclaimable» — ложный ориентир, см. ниже) | 🔴 |
| Docker volumes | 5.55 GB (из них 1.97 GB сироты) | 🟡 |
| Build cache | 1.2 GB | 🟡 |

---

## 1. docling — парсинг документов (AI/OCR)

- **Назначение**: Docling Serve — извлечение структурированного текста/таблиц из PDF, DOCX, изображений (ML-модели layout/OCR).
- **Контейнер**: `docling`, образ `docling-serve-cpu-libreoffice:latest` (**8.52 GB**), Up 3 days (healthy).
- **Порты**: `0.0.0.0:5001->5001` (публично!) + `8080` (внутренний).
- **Домен**: `docling.aimentorcrm.com` → `172.17.0.1:5001` (NPM id=26).
- **Развёртывание**: compose, `/opt/docling/docker-compose.yml` (+ `Dockerfile`, `build.log`).
- **Volume**: `docling_docling-cache` (912 MB — кэш моделей).
- **Конфиг (env)**: `DOCLING_SERVE_ENABLE_UI=true`, `LOAD_MODELS_AT_BOOT=true`, `DOCLING_DEVICE=cpu`, `mem_limit 6g`, `shm_size 512m`.
- **Статус**: ✅ работает (healthy). Образ самый большой на сервере.

## 2. metabase — BI-аналитика

- **Назначение**: Metabase — BI-дашборды/запросы поверх PostgreSQL.
- **Контейнер**: `metabase`, образ `metabase/metabase:latest` (**1.71 GB**), Up 3 days.
- **Порты**: `0.0.0.0:3003->3000` (публично!).
- **Домен**: `metabase.aimentorcrm.com` → `172.17.0.1:3003` (NPM id=8).
- **Развёртывание**: голый `docker run` (без compose, без `/opt`-каталога, **без volume**).
- **БД**: PostgreSQL `172.17.0.1:5432`, db `metabase`, user `metabase` (пароль в env, замаскирован).
- **JVM**: `JAVA_OPTS=-Xmx1280m -Xms256m -XX:+UseG1GC`.
- **Статус**: ✅ работает. ⚠️ writable-слой 627 MB (нет volume — плагины пишутся в слой контейнера).

## 3. proflab-b24-test — ТЕСТОВАЯ копия Bitrix24-виджета каталога Proflab

- **Назначение**: тестовая копия Flask-приложения «OAuth-виджет Bitrix24 → каталог Proflab» (поиск/КП через n8n).
- **Контейнер**: `proflab-b24-test`, образ `proflab-b24-app:latest` (общий с prod, 203 MB), Up 3 days.
- **Порты**: нет опубликованных (Flask слушает `0.0.0.0:80` внутри).
- **Домен**: `b24-test.aimentorcrm.com` → `proflab-b24-test:80` (NPM id=32).
- **Развёртывание**: голый `docker run`, bind mount `/opt/proflab-b24-test` → `/opt/proflab-b24`.
- **Код**: `/opt/proflab-b24-test/` (app.py идентичен prod, Dockerfile, install.sh, static/).
- **Конфиг (.env)**: `B24_DOMAIN=b24-lutjvd.bitrix24.ru`, redirect `https://b24-test.aimentorcrm.com/`, вебхуки n8n (`server.aimentorcrm.com`).
- **Статус**: ✅ работает. 🟡 Кандидат на удаление (тестовая копия, привязана к тестовому порталу Bitrix24).

## 4. open-webui — AI-чат интерфейс (Proflab)

- **Назначение**: Open WebUI — веб-интерфейс LLM-чата + кастомные pipes (каталог Proflab, поставщики, laminar).
- **Контейнер**: `open-webui`, образ `ghcr.io/open-webui/open-webui:main` (**6.51 GB**), Up 3 days (healthy).
- **Порты**: `127.0.0.1:3006->8080` (только локально).
- **Домены**: `webui.aimentorcrm.com` → `open-webui:8080` (NPM id=31); `proflab-ui.aimentorcrm.com` (id=25, удалён).
- **Развёртывание**: compose, `/opt/open-webui/docker-compose.yml`, `mem_limit 2g`.
- **Data**: `/opt/open-webui/data` (1.1 GB — векторная БД, история чатов, файлы).
- **Pipes**: `catalog_pipe.py`, `proflab_webhook_pipe.py`, `suppliers_pipe.py`, `laminar_pipe.py`, инжекторы (`inject_catalog.py` и др.).
- **Конфиг (.env)**: `OPENAI_API_BASE_URL=http://172.20.0.1:4010/v1` (см. 🔴 ниже), `WEBUI_SECRET_KEY` (замаскирован).
- **Статус**: ✅ работает, НО 🔴 **LLM-бэкенд мёртв** — `172.20.0.1:4010` (litellm) не слушает, домен `litellm.aimentorcrm.com` удалён (NPM id=17 is_deleted). Чат без бэкенда не работает.

## 5. gotenberg — HTML→PDF конвертер (Chromium)

- **Назначение**: Gotenberg — рендер HTML/Office в PDF (Chromium headless). Бэкенд для `html2pdf-api`.
- **Контейнер**: `gotenberg`, образ `gotenberg/gotenberg:8` (**2.43 GB**), **Exited (0) 5 недель назад**.
- **Порты**: `127.0.0.1:3102->3000` (bind из `.env`, только локально).
- **Домен**: нет (внутренний сервис).
- **Развёртывание**: compose, `/opt/gotenberg/compose.yaml` + `.env` (+ `test/`).
- **Конфиг**: отключены LibreOffice/PDFengines/webhook, включена SSRF-защита (`CHROMIUM_DENY_PRIVATE_IPS=true`), `CHROMIUM_MAX_CONCURRENCY=2`.
- **Статус**: 🔴 **ОСТАНОВЛЕН 5 недель** → `html2pdf-api` сломан (см. ниже).

## 6. carbone — генерация документов (Carbone Enterprise)

- **Назначение**: Carbone EE — генерация DOCX/PDF/XLSX из шаблонов (JSON-данные + шаблоны).
- **Контейнер**: `carbone`, образ `carbone/carbone-ee:latest` (**2.03 GB**), Up 3 days.
- **Порты**: `0.0.0.0:4000->4000` (публично!).
- **Домен**: нет (внутренний сервис, используется программно).
- **Развёртывание**: compose, `/opt/carbone/docker-compose.yml`.
- **Volume**: bind-mounts `./template`, `./render`, `./config`.
- **Конфиг**: `CARBONE_STUDIO=true`, `TZ=Europe/Moscow`. Лицензионный ключ EE в `/opt/carbone/config/` (`config.json`, `key.pem`, `key.pub`).
- **Файлы**: `/opt/carbone/template/` (6 hash-шаблонов ~3 MB), `render/` (пусто), тестовые `test-carbone.py`, `dl-test.pdf`.
- **Статус**: ✅ работает.

## 7. html2pdf-api — HTTP-обёртка над gotenberg

- **Назначение**: Node/Express API: принимает HTML (`POST /convert`), отдаёт PDF через gotenberg; раздаёт результат по `PUBLIC_BASE/pdf/...`.
- **Контейнер**: `html2pdf-api`, образ `html2pdf-api-html2pdf-api:latest` (208 MB), Up 3 days.
- **Порты**: `0.0.0.0:3103->3000` (публично!).
- **Домен**: `pdf.aimentorcrm.com` → `html2pdf-api:3000` (NPM id=24).
- **Развёртывание**: compose, `/opt/html2pdf-api/compose.yaml` (+ `Dockerfile`, `server.js`, `package.json`, `pdf/`).
- **Конфиг**: `GOTENBERG_URL=http://gotenberg:3000`, `PUBLIC_BASE=http://176.98.178.8:3103`, сеть `gotenberg_default`.
- **Статус**: 🔴 **СЛОМАН** — зависит от `gotenberg` (остановлен 5 недель). `POST /convert` вернёт ошибку «gotenberg error».

---

## Топология зависимостей

```
docling          (независим, ML-парсинг)          → docling.aimentorcrm.com
metabase         (независим, PostgreSQL)           → metabase.aimentorcrm.com
proflab-b24      (prod, Bitrix24 OAuth)            → proflab-b24.aimentorcrm.com
proflab-b24-test (test, Bitrix24 OAuth)            → b24-test.aimentorcrm.com
open-webui       (чат) ──🔴─→ litellm :4010 (МЁРТВ)
html2pdf-api     (Express) ──🔴─→ gotenberg :3000 (ОСТАНОВЛЕН)
carbone          (независим, генерация документов)
gotenberg        (HTML→PDF) [STOPPED 5 недель]
```

## Сети

- `global-proxy-network` (172.20.0.x) — общая сеть NPM + сервисы (n8n, open-webui, html2pdf-api).
- `docling_default`, `carbone_default`, `gotenberg_default` — per-compose.
- `onyx_default` — сирота (Onyx переехал на другой сервер).
- `mtg-net`, `n8n-proxy-network`, `bridge` — прочие.

## Обнаруженные проблемы (для «навести порядок»)

1. 🔴 **html2pdf-api сломан** — gotenberg остановлен 5 недель. Либо перезапустить gotenberg, либо вывести оба из эксплуатации.
2. 🔴 **open-webui без LLM-бэкенда** — litellm (172.20.0.1:4010) удалён, домен погашен. Нужен новый роутер или реконфигурация.
3. 🟡 **Публично открыты порты** — docling :5001, metabase :3003, carbone :4000, html2pdf-api :3103 слушают на `0.0.0.0` (без NPM/basic-auth).
4. 🟡 **metabase без volume** — 627 MB writable-слой (риск потери плагинов при пересоздании).
5. 🟡 **proflab-b24-test** — тестовая копия, дублирует prod.

## Кандидаты на удаление (освобождение места)

См. отдельный файл `cleanup-plan.md` (готовится по факту согласования).
