import json, sqlite3, time

DB = "/opt/open-webui/data/webui.db"
CODE_PATH = "/opt/open-webui/laminar_pipe.py"
FUNC_ID = "laminar-systems-pipe"
ADMIN_ID = "19769372-1182-42f4-af27-f277669f7901"

content = open(CODE_PATH).read()
meta = json.dumps({"description": "Отправка вопроса на вебхук и показ ответа", "manifest": {"title": "Ламинарные системы", "version": "1.0.0"}})
valves = json.dumps({"WEBHOOK_URL": "http://n8n:5678/webhook/3f22e8c8-e090-4ce2-840e-d26667d1dea8", "TIMEOUT": 120})

now = int(time.time() * 1000)
con = sqlite3.connect(DB)
con.execute(
    "INSERT INTO function (id, user_id, name, type, content, meta, valves, is_active, is_global, updated_at, created_at) "
    "VALUES (?,?,?, 'pipe', ?,?,?,1,1,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, content=excluded.content, meta=excluded.meta, valves=excluded.valves, is_active=1, is_global=1, updated_at=excluded.updated_at",
    (FUNC_ID, ADMIN_ID, "Ламинарные системы", content, meta, valves, now, now))
con.commit()
row = con.execute("SELECT id, name, type, is_active, is_global FROM function WHERE id=?", (FUNC_ID,)).fetchone()
con.close()
print("INSERTED:", row)
