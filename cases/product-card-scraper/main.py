# -*- coding: utf-8 -*-
"""lamsys-api — live-скрейп карточки example.com по артикулу. Без БД."""
import json
import re
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from lamsys_parser import parse_page, parse_article

BASE = "https://www.example.com"
COOKIE = {"Cookie": "beget=begetok"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# нормализация артикула: верхний регистр + кириллица→латиница (на сайте бывает 1R-В.001-15PHARM)
_TR = str.maketrans({
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O",
    "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X",
})


def norm(s: str) -> str:
    return (s or "").upper().translate(_TR).strip()


def _load_map() -> dict[str, str]:
    p = Path(__file__).parent / "article_url_map.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


ARTICLE_URL = _load_map()

app = FastAPI(title="lamsys-api", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "articles_indexed": len(ARTICLE_URL)}


@app.get("/")
async def index():
    return {
        "service": "lamsys-api",
        "usage": "/product?article=1R-D.001-12",
        "articles_indexed": len(ARTICLE_URL),
    }


@app.get("/product")
async def product(article: str):
    a = norm(article)
    if not a:
        raise HTTPException(status_code=400, detail="передайте параметр ?article=")
    url = ARTICLE_URL.get(a)
    if not url:
        # попробовать без PHARM-суффикса
        base_a = re.sub(r"PHARM$", "", a)
        url = ARTICLE_URL.get(base_a)
    if not url:
        raise HTTPException(status_code=404, detail=f"артикул '{article}' не найден на example.com")

    if url.startswith("/"):
        url = BASE + url
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": UA, "Cookie": "beget=begetok"})
            r.raise_for_status()
            html = r.text
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"example.com вернул {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"не удалось получить страницу: {e}")

    data = parse_page(html, page_url=url)
    data["article"] = data.get("article") or article
    return JSONResponse(data)
