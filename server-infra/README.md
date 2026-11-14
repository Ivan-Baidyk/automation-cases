# Server Infrastructure Archive — 176.98.178.8

Снимок конфигураций сервисов (без секретов и сгенерированных данных) по состоянию на **2026-11-14**.

Архив создан при наведении порядка на сервере: `gotenberg` + `html2pdf-api` и тестовая
копия `proflab-b24-test` выведены из эксплуатации. Конфиги сохранены здесь для возможного
воссоздания.

## Содержимое

| Каталог | Сервис | Статус на 2026-11-14 |
|---|---|---|
| `gotenberg/` | HTML→PDF конвертер (Chromium) | ❌ удалён |
| `html2pdf-api/` | Node/Express обёртка над gotenberg | ❌ удалён |
| `proflab-b24-test/` | Тестовая копия Bitrix24-виджета Proflab | ❌ удалён |
| `docling/` | Парсинг документов (AI/OCR) | ✅ работает |
| `carbone/` | Генерация документов (Carbone EE) | ✅ работает |
| `open-webui/` | AI-чат интерфейс + pipes | ✅ работает |
| `metabase/` | BI-аналитика | ✅ работает |

Полное описание всех сервисов, портов, доменов, зависимостей и проблем — в
[`2026-11-14-services-inventory.md`](2026-11-14-services-inventory.md).

## Что НЕ включено (намеренно)

- **Секреты**: `.env` с токенами (Bitrix24, open-webui API key), пароли БД, ключи лицензии
  Carbone EE (`config/key.pem`, `key.pub`).
- **Данные**: сгенерированные PDF (`html2pdf-api/pdf/`), шаблоны Carbone (`template/`),
  данные open-webui (`data/`), история БД.
- **Полный бэкап** (включая `.env` файлы) лежит на сервере:
  `/root/backups/services-7-20261114.tar.gz` (root-only, `chmod 600`).

## Воссоздание удалённых сервисов

### gotenberg
```bash
cd gotenberg && docker compose up -d
```

### html2pdf-api (зависит от gotenberg)
```bash
cd html2pdf-api && docker compose up -d --build
# NPM: pdf.aimentorcrm.com -> html2pdf-api:3000 (перевыпустить сертификат)
```

### proflab-b24-test
```bash
cd proflab-b24-test
docker build -t proflab-b24-app .
docker run -d --name proflab-b24-test --restart unless-stopped \
  -v /opt/proflab-b24-test:/opt/proflab-b24 proflab-b24-app
# заполнить .env (B24_* и WEBHOOK_*), NPM: b24-test.aimentorcrm.com -> proflab-b24-test:80
```

## Примечания

- Паттерн развёртывания: NPM (Nginx Proxy Manager) → домен → контейнер.
- Сеть с NPM: `global-proxy-network` (172.20.0.x).
- Секреты в этот репозиторий НЕ добавлять — только `.env.example` шаблоны.
