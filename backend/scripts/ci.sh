#!/usr/bin/env bash
# 로컬 CI — git init 후 GitHub Actions로 그대로 이전한다 (P0 설계서 §7)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/3 pytest =="
.venv/bin/python -m pytest -q

echo "== 2/3 import-linter =="
.venv/bin/lint-imports

echo "== 3/3 코어 금칙어 grep =="
bash scripts/check_forbidden_words.sh

echo "CI 초록"
