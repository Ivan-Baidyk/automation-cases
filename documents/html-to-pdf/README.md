# HTML → PDF (Express + Gotenberg)

Конвертация HTML в PDF через headless Chromium (Gotenberg) с тонким Express-прокси.

## Задача

Нужна была точная HTML-вёрстка документов (таблицы позиций, кастомный дизайн) → PDF,
как альтернатива шаблонам docx.

## Под капотом

- **html2pdf-api** (`server.js`) — Express, принимает HTML → отдаёт PDF-файл по URL.
- **Gotenberg** — контейнер с headless Chromium, фактический рендер
  (`/forms/chromium/convert/html`).

## API

```
POST /convert  body: {"html": "...", "filename": "kp"}  (или raw text/html)
  → {"ok": true, "url": "/pdf/<file>.pdf", "filename": ..., "size": ...}
GET  /health
```

## Запуск

См. [deploy.md](deploy.md).

## Использовалось

В связке с остальными документами — см. [../README.md](../README.md).
