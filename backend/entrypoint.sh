#!/bin/sh
set -e

# 載入環境變數
echo "Starting app with updated environment variables..."

exec uvicorn app.main:app --host 0.0.0.0 --root-path /api --workers 4
