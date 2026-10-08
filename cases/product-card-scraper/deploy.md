# Быстрое развёртывание: product-card-scraper

```bash
# 1. Зависимости
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Собрать карту артикул→URL (один раз) и положить в article_url_map.json

# 3. Запуск (systemd)
sudo cp lamsys-api.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now lamsys-api

# 4. Проверка
curl "http://localhost:8002/product?article=1R-D.001-12"
```

## systemd unit (lamsys-api.service)

```ini
[Unit]
Description=Product card live scraper
After=network.target

[Service]
WorkingDirectory=/opt/product-card-scraper
ExecStart=/opt/product-card-scraper/run.sh
Restart=always

[Install]
WantedBy=multi-user.target
```
