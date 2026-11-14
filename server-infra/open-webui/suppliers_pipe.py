"""
title: Таблицы Поставщики
author: Ivan Baidyk
author_url: https://aimentorcrm.com
version: 1.0.0
description: Отправляет вопрос из чата на вебхук (параметр «Вопрос») и показывает ответ (поле «Ответ»).
"""

import json
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

AUX_MARKERS = [
    "generate a concise title",
    "generate 1-3 broad tags",
    "generating search queries",
    "follow-up questions",
    "image generation task",
    "fitting emoji",
    "various models",
]


class Pipe:
    class Valves(BaseModel):
        WEBHOOK_URL: str = Field(
            default="http://n8n:5678/webhook/e15ec6a5-141b-4141-9cd9-5bd574692268",
            description="URL вебхука (внутренний адрес n8n)",
        )
        TIMEOUT: int = Field(default=120, description="Таймаут запроса, секунды")

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> list:
        return [{"id": "suppliers-tables", "name": "Таблицы Поставщики"}]

    def _extract_text(self, body: dict) -> str:
        for m in reversed(body.get("messages", []) or []):
            if m.get("role") != "user":
                continue
            content = m.get("content")
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict) and p.get("type") == "text":
                        parts.append(p.get("text", ""))
                    elif isinstance(p, str):
                        parts.append(p)
                return "\n".join(parts).strip()
        return ""

    def _is_auxiliary(self, text: str) -> bool:
        t = (text or "").lstrip().lower()
        if t.startswith("### task:"):
            return True
        return any(m in t for m in AUX_MARKERS)

    def _parse_response(self, raw: str) -> str:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(data, dict):
            for key in ("Ответ", "ответ", "answer", "response", "output", "text", "content", "result", "message", "data"):
                val = data.get(key)
                if isinstance(val, str):
                    return val
            for val in data.values():
                if isinstance(val, str):
                    return val
            return json.dumps(data, ensure_ascii=False)
        return raw

    async def pipe(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None) -> str:
        text = self._extract_text(body)

        if self._is_auxiliary(text):
            print(f"[suppliers] SKIP auxiliary task text[:60]={text[:60]!r}", flush=True)
            return ""

        if not text:
            return "Введите вопрос."

        url = self.valves.WEBHOOK_URL
        payload = {"Вопрос": text}

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Отправка вопроса...", "done": False}}
            )

        try:
            timeout = aiohttp.ClientTimeout(total=self.valves.TIMEOUT)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=timeout) as resp:
                    raw = await resp.text()
                    if resp.status >= 400:
                        return f"Ошибка вебхука (HTTP {resp.status}): {raw[:500]}"
        except Exception as exc:
            return f"Ошибка подключения к вебхуку: {exc}"

        out = self._parse_response(raw)

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Готово", "done": True}}
            )

        return out
