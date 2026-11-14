"""
title: Каталог (живой поиск)
author: Ivan Baidyk
author_url: https://aimentorcrm.com
version: 1.0.0
description: Демо живого поиска — HTML-виджет с debounce-запросом к n8n и отрисовкой таблицы.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        WIDGET_PATH: str = Field(
            default="/app/backend/data/search_widget.html",
            description="Путь к HTML-виджету внутри контейнера",
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> list:
        return [{"id": "catalog-search", "name": "Каталог (живой поиск)"}]

    async def pipe(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None) -> str:
        try:
            with open(self.valves.WIDGET_PATH, "r", encoding="utf-8") as f:
                html = f.read()
        except OSError:
            return "Ошибка: файл виджета не найден."

        print(f"[catalog] emitter_ok={__event_emitter__ is not None} html_len={len(html)}", flush=True)
        if __event_emitter__:
            await __event_emitter__({
                "type": "embeds",
                "data": {"embeds": [html]},
            })

        return "Введите запрос в поле ниже — результаты появятся автоматически (поиск от 3 символов)."
