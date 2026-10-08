# Работа с документами

Три решения, которые закрывают контур обработки документов в автоматизации: распознать
входящий PDF, сгенерировать документ по шаблону (docx), сформировать итоговый PDF.
Написано как шпаргалка «вернуться, если снова понадобится».

## Решения под капотом

| Решение | Что делает | Технология | Кейс |
|---|---|---|---|
| **pdf-parsing** | PDF/DOCX → структурированный текст/таблицы | Docling (IBM) + LibreOffice | [pdf-parsing](pdf-parsing/README.md) |
| **doc-generation** | шаблон + JSON → docx/pdf | Carbone (Node.js + LibreOffice) | [doc-generation](doc-generation/README.md) |
| **html-to-pdf** | HTML → PDF | Express + Gotenberg (Chromium) | [html-to-pdf](html-to-pdf/README.md) |

## Как использовал (в связке)

```
Входящий прайс/КП (PDF, DOCX, скан)
        │
        ▼
  pdf-parsing (Docling)          ← РАСПОЗНАВАНИЕ: PDF → Markdown/JSON, извлечение таблиц
        │
        ▼
  LLM/парсер структурирует позиции → данные
        │
        ▼
  doc-generation (Carbone)       ← ФОРМИРОВАНИЕ: шаблон docx + данные → документ
        │                              (либо docx напрямую, либо convertTo: pdf)
        │
        ├──► итоговый .docx (шаблон в фирменном стиле)
        │
        └──► html-to-pdf (Gotenberg)  ← АЛЬТЕРНАТИВА: HTML-вёрстка → PDF
```

## Подробнее про каждый

### pdf-parsing — Docling (распознавание)
- **Под капотом:** self-hosted `docling-serve` + LibreOffice (для docx/pptx/сканов).
  Модели грузятся при старте, CPU-инференс.
- **Использовал:** подавал PDF-прайсы поставщиков → на выходе Markdown с таблицами →
  дальше LLM распознавал позиции и складывал в БД.
- **Эндпоинт:** `POST /v1/convert/file` (multipart) → `json_content`/markdown.

### doc-generation — Carbone (docx/pdf по шаблону)
- **Под капотом:** Carbone Enterprise (Node.js + LibreOffice), шаблонизатор с
  `{d.field}`-плейсхолдерами. Шаблон загружается → `templateId`, рендер из JSON →
  docx, `convertTo: pdf` — конвертация на лету.
- **Использовал:** фирменные КП/договоры — один шаблон, подстановка позиций/сумм.
- **Эндпоинты:** `POST /template`, `POST /render/{templateId}?download=true`.

### html-to-pdf — Gotenberg (HTML → PDF)
- **Под капотом:** тонкий Express-прокси (`html2pdf-api`) поверх Gotenberg — Gotenberg
  гоняет headless Chromium (`/forms/chromium/convert/html`).
- **Использовал:** там, где нужна точная HTML-вёрстка (таблицы позиций, кастомный
  дизайн), а не шаблон docx.
- **Эндпоинт:** `POST /convert` (`{html, filename}`) → `{url, filename, size}`.

## Как развернуть (кратко)

```bash
# распознавание PDF
cd pdf-parsing && docker compose up -d      # см. pdf-parsing/deploy.md

# генерация по шаблону
cd doc-generation && docker compose up -d   # см. doc-generation/deploy.md (нужен ключ EE)

# HTML → PDF
cd html-to-pdf && docker compose up -d      # см. html-to-pdf/deploy.md (gotenberg + api)
```

## Pitfalls (важно, чтобы не наступить снова)

- **Carbone** работает под UID 1000 — каталогам `config/template/render` нужен
  `chown 1000:1000`, иначе `EACCES` при чтении `config.json`.
- **Carbone** по умолчанию слушает `127.0.0.1` — для доступа извне нужен `CARBONE_BIND=0.0.0.0`.
- **Docling** требователен к памяти (`mem_limit 6g`), модели грузятся при старте —
  первый запуск/healthcheck долгий.
- **Gotenberg** — отдельный контейнер, `html2pdf-api` ходит к нему по внутреннему имени
  (`gotenberg:3000`), а не по localhost.
- **html2pdf-api** принимает HTML в JSON/form-urlencoded, НЕ multipart-файлы — иначе
  `400 {"error":"missing html"}`.
