#!/usr/bin/env bash
# REMAKE DAY 데모 기동 — DB(5435) + 백엔드(8500) + 프론트(3500)
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/4 DB =="
docker compose up -d
until docker exec pigfarm-db pg_isready -U pigfarm -q; do sleep 1; done

echo "== 2/4 ollama 확인 + 모델 워밍업 (최대 1분) =="
curl -sf http://localhost:11434/api/tags >/dev/null || {
  echo "ollama가 떠 있지 않습니다. 'ollama serve' 후 다시 실행하세요"; exit 1; }
# 현재 구성: NPC kanana1.5:8b-q4km · Core gemma4:12b — .env와 일치시킬 것
for M in "kanana1.5:8b-q4km" "gemma4:12b"; do
  curl -s http://localhost:11434/api/chat -d "{\"model\":\"$M\",\"messages\":[{\"role\":\"user\",\"content\":\"안녕\"}],\"think\":false,\"stream\":false,\"keep_alive\":\"2h\"}" >/dev/null &
done
wait

echo "== 3/4 백엔드 (8500) =="
cd backend
.venv/bin/alembic upgrade head
pkill -f "uvicorn main:app --port 8500" 2>/dev/null || true
nohup .venv/bin/uvicorn main:app --port 8500 --host 127.0.0.1 > ../backend.log 2>&1 &
cd ..
until curl -sf localhost:8500/health >/dev/null; do sleep 1; done
curl -s localhost:8500/health; echo

echo "== 4/4 프론트 (3500) =="
cd frontend
pkill -f "next dev -p 3500" 2>/dev/null || true
nohup npm run dev > ../frontend.log 2>&1 &
cd ..
sleep 5

echo
echo "  게임:      http://localhost:3500/play"
echo "  인스펙터:  http://localhost:3500/inspector/{attempt_id}  (토큰: backend/.env의 INSPECTOR_TOKEN)"
echo "  API:       http://localhost:8500/health"
echo "  로그:      backend.log / frontend.log"
echo "  종료:      ./stop_demo.sh"
