"""
title: Формирование КП в ворде
author: Ivan Baidyk
author_url: https://aimentorcrm.com
version: 5.0.0
description: Отправляет текст чата и прикреплённые файлы (как binary) на вебхук. Если вебхук возвращает бинарный файл (docx/xlsx/pdf) — сохраняет его и отдаёт как скачиваемый файл в чате.
"""

import glob
import json
import mimetypes
import os
import re
import sqlite3
import time as _time
import uuid as _uuid
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

UPLOADS_DIR = "/app/backend/data/uploads"
DB_PATH = "/app/backend/data/webui.db"

FILE_TAG_RE = re.compile(r"<file\b([^>]*)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r"([\w:-]+)=\"([^\"]*)\"")
ATTACHED_BLOCK_RE = re.compile(r"<attached_files>.*?</attached_files>", re.DOTALL | re.IGNORECASE)

AUX_MARKERS = [
    "generate a concise title",
    "generate 1-3 broad tags",
    "generating search queries",
    "follow-up questions",
    "image generation task",
    "fitting emoji",
    "various models",
]

MIME_TO_EXT = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/pdf": ".pdf",
    "application/zip": ".zip",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "text/csv": ".csv",
    "text/plain": ".txt",
    "application/json": ".json",
}


class Pipe:
    class Valves(BaseModel):
        WEBHOOK_URL: str = Field(
            default="http://n8n:5678/webhook/open-web-ui",
            description="URL вебхука (внутренний адрес n8n)",
        )
        TIMEOUT: int = Field(default=300, description="Таймаут запроса, секунды")

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> list:
        return [{"id": "proflab-webhook", "name": "Формирование КП в ворде"}]

    def _resolve_path(self, fid: str, name: str):
        if not fid:
            return None
        direct = os.path.join(UPLOADS_DIR, f"{fid}_{name}")
        if os.path.isfile(direct):
            return direct
        matches = glob.glob(os.path.join(UPLOADS_DIR, f"{fid}_*"))
        return matches[0] if matches else None

    def _parse_attached_files(self, text: str) -> list:
        files = []
        for tag in FILE_TAG_RE.finditer(text or ""):
            attrs = dict(ATTR_RE.findall(tag.group(1)))
            fid = attrs.get("id") or attrs.get("url")
            name = attrs.get("name") or "file"
            if not fid:
                continue
            files.append({"id": fid, "name": name, "content_type": attrs.get("content_type")})
        return files

    def _extract(self, body: dict):
        text = ""
        files = []
        for m in reversed(body.get("messages", []) or []):
            if m.get("role") != "user":
                continue
            content = m.get("content")
            if isinstance(content, str):
                for f in self._parse_attached_files(content):
                    f["path"] = self._resolve_path(f["id"], f["name"])
                    f["size"] = os.path.getsize(f["path"]) if f["path"] and os.path.isfile(f["path"]) else None
                    files.append(f)
                clean = ATTACHED_BLOCK_RE.sub("", content).strip()
                if clean:
                    text = clean
            elif isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ptype = part.get("type")
                    if ptype == "text" and (part.get("text") or "").strip():
                        if not text:
                            text = (part.get("text") or "").strip()
                    elif ptype in ("file", "image"):
                        fid = part.get("id")
                        name = part.get("name") or part.get("filename") or "file"
                        files.append({
                            "id": fid, "name": name,
                            "content_type": part.get("content_type"),
                            "path": self._resolve_path(fid, name),
                            "size": part.get("size"),
                        })
            if text:
                break
        return text, files

    def _is_auxiliary(self, text: str) -> bool:
        t = (text or "").lstrip().lower()
        if t.startswith("### task:"):
            return True
        return any(m in t for m in AUX_MARKERS)

    def _user_field(self, __user__, field, default=""):
        if not __user__:
            return default
        if isinstance(__user__, dict):
            return str(__user__.get(field) or default)
        return str(getattr(__user__, field, None) or default)

    def _guess_mime(self, f: dict) -> str:
        if f.get("content_type"):
            return f["content_type"]
        mime, _ = mimetypes.guess_type(f.get("name") or "")
        return mime or "application/octet-stream"

    def _sanitize(self, s: str) -> str:
        return (s or "").replace('"', "'").replace("\r", " ").replace("\n", " ")

    def _build_multipart(self, fields: dict, files: list):
        boundary = _uuid.uuid4().hex
        buf = bytearray()
        for name, value in fields.items():
            buf += (
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                f'{value}\r\n'
            ).encode("utf-8")
        for name, filename, content_type, data in files:
            buf += (
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                f'filename="{self._sanitize(filename)}"\r\n'
                f'Content-Type: {content_type}\r\n\r\n'
            ).encode("utf-8")
            buf += data
            buf += b"\r\n"
        buf += f"--{boundary}--\r\n".encode("utf-8")
        return bytes(buf), f"multipart/form-data; boundary={boundary}"

    def _parse_response(self, raw: str) -> str:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(data, dict):
            for key in ("response", "output", "answer", "content", "text", "result", "message", "data"):
                if isinstance(data.get(key), str):
                    return data[key]
            for val in data.values():
                if isinstance(val, str):
                    return val
            return json.dumps(data, ensure_ascii=False)
        if isinstance(data, list):
            parts = [x for x in data if isinstance(x, str)]
            return "\n".join(parts) if parts else json.dumps(data, ensure_ascii=False)
        return str(data)

    def _is_binary(self, content_type: str) -> bool:
        ct = (content_type or "").lower()
        if not ct:
            return False
        if ct.startswith("text/"):
            return False
        if ct == "application/json" or ct.endswith("+json"):
            return False
        return True

    def _filename_from_mime(self, mime: str) -> str:
        ext = MIME_TO_EXT.get((mime or "").lower(), "")
        if not ext:
            ext = mimetypes.guess_extension((mime or "").split(";")[0].strip()) or ""
        return f"result{ext}" if ext else "result.bin"

    def _save_file(self, raw_bytes: bytes, mime: str, user_id: str):
        filename = self._filename_from_mime(mime)
        file_id = str(_uuid.uuid4())
        path = os.path.join(UPLOADS_DIR, f"{file_id}_{filename}")
        with open(path, "wb") as fh:
            fh.write(raw_bytes)
        now = int(_time.time() * 1000)
        meta = json.dumps({"name": filename, "content_type": mime, "size": len(raw_bytes)})
        try:
            con = sqlite3.connect(DB_PATH, timeout=10)
            con.execute(
                "INSERT INTO file (id, user_id, filename, meta, created_at, hash, data, updated_at, path) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (file_id, user_id, filename, meta, now, "", "{}", now, path),
            )
            con.commit()
            con.close()
        except Exception as exc:
            print(f"[proflab-webhook] DB register error: {exc}", flush=True)
        return {"id": file_id, "name": filename, "path": path, "size": len(raw_bytes)}

    async def pipe(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None) -> str:
        text, files = self._extract(body)

        if self._is_auxiliary(text):
            print(f"[proflab-webhook] SKIP auxiliary task text[:80]={text[:80]!r}", flush=True)
            return ""

        url = self.valves.WEBHOOK_URL

        fields = {
            "text": text,
            "messages": json.dumps(body.get("messages", []), ensure_ascii=False),
            "user_name": self._user_field(__user__, "name"),
            "user_email": self._user_field(__user__, "email"),
            "user_id": self._user_field(__user__, "id"),
        }
        if body.get("chat_id"):
            fields["chat_id"] = str(body["chat_id"])
        if body.get("model"):
            fields["model"] = str(body["model"])

        binary_files = []
        meta = []
        for i, f in enumerate(files):
            field = "file" if i == 0 else f"file{i + 1}"
            bytes_read = 0
            if f.get("path") and os.path.isfile(f["path"]):
                with open(f["path"], "rb") as fh:
                    file_bytes = fh.read()
                bytes_read = len(file_bytes)
                binary_files.append((field, f["name"], self._guess_mime(f), file_bytes))
            meta.append({"id": f.get("id"), "filename": f["name"],
                         "content_type": self._guess_mime(f), "size": f.get("size"),
                         "bytes_sent": bytes_read})
        fields["files"] = json.dumps(meta, ensure_ascii=False)

        body_bytes, content_type = self._build_multipart(fields, binary_files)
        print(f"[proflab-webhook] POST {url} text_len={len(text)} files={meta}", flush=True)

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Отправка на вебхук...", "done": False}}
            )

        try:
            timeout = aiohttp.ClientTimeout(total=self.valves.TIMEOUT)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=body_bytes, headers={"Content-Type": content_type}, timeout=timeout) as resp:
                    resp_ct = resp.headers.get("Content-Type", "")
                    raw_bytes = await resp.read()
                    if resp.status >= 400:
                        return f"Ошибка вебхука (HTTP {resp.status}): {raw_bytes[:500].decode('utf-8', 'replace')}"
        except Exception as exc:
            return f"Ошибка подключения к вебхуку: {exc}"

        # Бинарный ответ (файл) → сохраняем и отдаём как скачиваемый файл
        if self._is_binary(resp_ct):
            print(f"[proflab-webhook] BINARY response ct={resp_ct} size={len(raw_bytes)}", flush=True)
            user_id = self._user_field(__user__, "id")
            file_obj = self._save_file(raw_bytes, resp_ct.split(";")[0].strip(), user_id)
            if __event_emitter__:
                _ct = resp_ct.split(";")[0].strip()
                await __event_emitter__({
                    "type": "files",
                    "data": {"files": [{
                        "type": "file",
                        "id": file_obj["id"],
                        "name": file_obj["name"],
                        "url": f"/api/v1/files/{file_obj['id']}/content",
                        "content_type": _ct,
                        "mime_type": _ct,
                        "size": file_obj["size"],
                        "meta": {"name": file_obj["name"], "content_type": _ct, "size": file_obj["size"]},
                    }]},
                })
                await __event_emitter__(
                    {"type": "status", "data": {"description": "Готово", "done": True}}
                )
            return (f"Сформирован файл: **{file_obj['name']}**\n\n"
                    f"[Скачать файл](/api/v1/files/{file_obj['id']}/content?attachment=true)")

        # Текстовый ответ
        out = self._parse_response(raw_bytes.decode("utf-8", "replace"))

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "Готово", "done": True}}
            )

        return out
