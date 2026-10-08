#!/bin/bash
export PATH="/opt/scrapalyser-venv/bin:/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
cd /opt/site-analyzer
source /opt/scrapalyser-venv/bin/activate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
