# Automation and Data Engineering Cases

Подборка кейсов по автоматизации сбора и обработки данных, разделённая на **две темы**:
парсинг сайтов и работа с документами. Каждый кейс — задача с описанием, архитектурой и
инструкцией по развёртыванию (`deploy.md`).

> Кейсы обезличены: без имён клиентов, доменов и IP. Показаны технические решения и подходы.

## Темы

| Тема | Содержание | Стек |
|---|---|---|
| [**Парсинг сайтов**](site-parsing/README.md) | 3 продукта: разведка сайтов, фреймворк обхода каталогов, точечный скрейп карточек | FastAPI, Playwright, httpx/curl_cffi, PostgreSQL |
| [**Работа с документами**](documents/README.md) | 3 решения: распознавание PDF, генерация docx по шаблону, HTML → PDF | Docling, Carbone, Gotenberg, Express |

## Кейсы

### Парсинг сайтов
- [Обзор темы + инструкция](site-parsing/README.md)
- [catalog-scraper](site-parsing/catalog-scraper/README.md) — фреймворк обхода каталогов поставщиков
- [site-reconnaissance](site-parsing/site-reconnaissance/README.md) — разведка сайтов (scrapalyser → api-recon → caniscrape)
- [product-card-scraper](site-parsing/product-card-scraper/README.md) — live-скрейп карточек по артикулу

### Работа с документами
- [Обзор темы](documents/README.md)
- [pdf-parsing](documents/pdf-parsing/README.md) — PDF → текст (Docling)
- [doc-generation](documents/doc-generation/README.md) — docx/pdf по шаблону (Carbone)
- [html-to-pdf](documents/html-to-pdf/README.md) — HTML → PDF (Gotenberg)

## Смежный продукт

- [PIM / товарная база](pim/README.md) — централизация товарных данных (AtroCore) —
  стоит между темами: потребляет данные парсинга, питает генерацию документов.

## Ключевые навыки

- **Python / FastAPI** — микросервисы, REST API
- **PostgreSQL** (+ pgvector, paradedb/BM25, pg_trgm) — хранение и поиск
- **Docker / Docker Compose / systemd** — развёртывание и эксплуатация
- **n8n** — оркестрация (упоминается как связующий слой)
- **Playwright / httpx / curl_cffi** — сбор данных
- **LLM-интеграции** — распознавание неструктурированных данных
- **Docling / Carbone / Gotenberg** — обработка документов
