#!/bin/bash
cd /opt/lamsys-api
source venv/bin/activate
exec uvicorn main:app --host 0.0.0.0 --port 8002 --workers 1
