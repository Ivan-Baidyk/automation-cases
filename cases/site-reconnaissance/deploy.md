# Быстрое развёртывание: site-reconnaissance

```bash
# 1. Зависимости
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Запуск (systemd)
sudo cp site-analyzer.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now site-analyzer

# 3. Проверка
curl http://localhost:8000/health
curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/", "deep": true, "diagnostics": true}'
```

## Требования
- Playwright (chromium): `playwright install chromium`
- Внешние инструменты: scrapalyser, api-recon, caniscrape (в PATH или venv)
