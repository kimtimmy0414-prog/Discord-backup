@echo off
uvicorn web:app --host 0.0.0.0 --port 20765 --workers 1
PAUSE