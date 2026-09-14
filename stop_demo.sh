#!/usr/bin/env bash
cd "$(dirname "$0")"
pkill -f "uvicorn main:app --port 8500" 2>/dev/null || true
pkill -f "next dev -p 3500" 2>/dev/null || true
docker compose stop
echo "종료했습니다 (DB 컨테이너는 stop — 데이터 유지)"
