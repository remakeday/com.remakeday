#!/usr/bin/env bash
# 코어(apps/engine) 금칙어 검사 — 목록은 시나리오 어댑터가 가진다. 코어는 모른다.
set -euo pipefail
cd "$(dirname "$0")/.."

LIST=$(mktemp)
trap 'rm -f "$LIST"' EXIT

# 1글자 단어는 일반 어휘 오탐(예: '-준다', '기-준')을 막기 위해 한글 경계 lookaround 적용.
# 한계: 1글자 이름 + 조사 결합(예: 'X이')은 CI에서 못 잡는다 — 런타임 검출은 P1 하네스 소관.
if ! .venv/bin/python -c "
from apps.scenarios.scenario_a.adapter import build
for w in build().forbidden_words():
    print(f'(?<![가-힣]){w}(?![가-힣])' if len(w) == 1 else w)
" > "$LIST" 2>/dev/null; then
  echo "SKIP: scenario_a 미설치 — 금칙어 검사 생략"
  exit 0
fi

# grep -P는 -f 다중 패턴을 지원하지 않아 패턴별로 검사한다
FOUND=0
while IFS= read -r pat; do
  [ -z "$pat" ] && continue
  if grep -rnP --include="*.py" -e "$pat" apps/engine; then
    FOUND=1
  fi
done < "$LIST"
if [ "$FOUND" -eq 1 ]; then
  echo "FAIL: 코어(apps/engine)에 금칙어 검출"
  exit 1
fi
echo "OK: 코어 금칙어 0건 (검사 파일 $(find apps/engine -name '*.py' | wc -l)개)"
