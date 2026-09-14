#!/bin/bash
# 매일 23:45 실행 — REMAKE DAY(com.remakeday) 당일 개발 이력을 docs/jekyll.md에 기록하고
# beyondbob.remakeday.com(지킬 허브)의 _posts/ 로 당일 섹션을 포스트로 변환해 복사.
#
# 등록: crontab "45 23 * * * /home/kimchungsik/projects/com.remakeday/scripts/jekyll-devlog.sh"
# 시간 분리 — 23:45 remakeday / 23:50 masterless / 23:55 beyondfacade / 23:59 lifetutorial(일시중지)
#
# git 커밋/푸시는 사용자가 직접 수행한다. 이 스크립트는 파일만 갱신한다.
#
# 저장소 역할 분리:
#   com.remakeday/docs/jekyll.md                          ← 개발 작업만. 개발 일지의 원본
#   beyondbob.remakeday.com/_posts/YYYY-MM-DD-dev-log.md  ← 당일 섹션의 사본 (front matter 부착)
#   이 스크립트가 원본을 갱신한 뒤 당일 섹션만 지킬 포스트로 변환한다.
#   지킬 저장소에서 이 포스트를 직접 고치지 않는다 — 다음 실행 때 덮어쓰인다.

set -u
PROJECT=/home/kimchungsik/projects/com.remakeday
BLOG=/home/kimchungsik/projects/beyondbob.remakeday.com
LOG=/home/kimchungsik/.claude/jekyll-devlog-remakeday-cron.log
export PATH="/home/kimchungsik/.local/bin:$PATH"

TODAY=$(date +%Y-%m-%d)

cd "$PROJECT" || exit 1

{
  echo "=== jekyll-devlog-remakeday run $TODAY $(date +%H:%M:%S) ==="

  claude -p --permission-mode acceptEdits \
    --allowedTools "Bash(git log:*)" "Bash(git diff:*)" "Bash(git status:*)" "Bash(find:*)" "Bash(wc:*)" "Bash(docker ps:*)" "Bash(docker compose ps:*)" \
    <<EOF
오늘($TODAY) 하루 동안 개발된 내용을 개발 일지 docs/jekyll.md 에 기록해줘.

## 1. 근거 수집 — 추측하지 말고 실제로 확인할 것

아래를 순서대로 확인하고, 확인한 것만 쓴다. 확인하지 못한 것은 쓰지 않는다.

- \`git log --since="$TODAY 00:00" --until="$TODAY 23:59" --pretty='%h %ad %s' --date=format:'%H:%M'\` — 오늘 커밋
- \`git status --short\` — 미커밋 변경. 커밋이 0건이어도 작업이 있었을 수 있다
- \`git diff --stat\` 와 \`git diff --cached --stat\` — 변경 규모(파일 수, +/- 줄수)
- \`find . -newermt "$TODAY 00:00" -type f -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/.next/*' -not -path '*/__pycache__/*'\` — 오늘 수정된 파일 전체
- docs/model_evaluation.md 와 backend/metrics.yml 에 오늘 추가된 항목이 있으면 확인 (모델 평가 수치의 정본은 그쪽이다 — 일지에는 결론만 요약하고 정본 위치를 적는다)
- docs/ 아래 오늘 수정된 다른 문서가 있으면 함께 반영
- 인프라가 바뀌었으면 \`docker compose ps\` 로 실제 상태를 확인

## 2. 작성 형식 — 이 파일의 기존 관례를 그대로 따를 것

- docs/jekyll.md 는 "# 작업 로그" 헤더 아래 최신 날짜가 위로 오는 구조다.
- "## $TODAY — 제목" 일자별 섹션을 인트로 바로 아래(가장 위 날짜 자리)에 추가한다.
  이미 오늘 섹션이 있으면 그 안에 이어서 갱신한다 — 세션 중에 미리 적어둔 내용을 지우지 말고 보완한다.
- 섹션 안은 필요하면 "### 소제목" 으로 나눈다. 굵은 리드 불릿(**항목명** — 내용) 스타일을 따른다.
- front matter 나 마일스톤 표는 이 파일에 없다. 만들지 마.
- 한국어로 쓴다. 문체는 기존 섹션과 맞춘다 (평서형 "-다" 종결, 담백하게).

## 3. 상세도 — 이 항목이 가장 중요하다

**수치와 확인 사실을 반드시 포함한다.** 다음이 있으면 빠짐없이 적는다:

- 테스트 통과/실패 건수, 소요 시간, p50/p95 (예: "pytest 386 passed 7.5초")
- 줄수·파일 수, 포트 번호, 버전, 커밋 해시와 시각
- 명령 실행 결과의 실제 출력 (예: "health: ok", "pair peak 12.34 GiB")
- 변경 전/후 대조는 표로

**판단이 필요했던 지점은 이유까지 적는다.** "무엇을 했다"보다 "왜 그렇게 했다"가 나중에 쓸모 있다.

**막힌 것·미완인 것도 적는다.** 이전 날짜의 미완 항목이 아직 안 끝났으면 이월해서 유지한다.

과장하지 않는다. 안 한 것을 한 것처럼 쓰지 않는다. 검증하지 않은 수치를 지어내지 않는다.

## 4. 금지 사항

- 오늘 개발된 내용이 전혀 없으면 파일을 수정하지 말고 "변경 없음"이라고만 답해. 근거(커밋 0건, 수정 파일 없음 등)를 함께 적어.
- git commit / push 는 절대 하지 마.
- docs/jekyll.md 외의 파일은 수정하지 마.
- 이전 날짜 섹션은 건드리지 마. 오늘 섹션만 추가/갱신한다.
EOF

  # 당일 섹션 → 지킬 포스트 변환 (원본 갱신 후 실행)
  if [ -d "$BLOG/_posts" ]; then
    SECTION=$(awk -v d="## $TODAY" '
      index($0, d) == 1 { f = 1 }
      f && /^## / && index($0, d) != 1 { exit }
      f { print }
    ' docs/jekyll.md)
    if [ -n "$SECTION" ]; then
      TITLE=$(printf '%s\n' "$SECTION" | head -1 | sed -E 's/^## [0-9-]+[[:space:]]*(—[[:space:]]*)?//')
      [ -z "$TITLE" ] && TITLE="개발 일지 $TODAY"
      {
        printf -- '---\n'
        printf 'title: "%s"\n' "${TITLE//\"/\\\"}"
        printf 'author: chungsik\n'
        printf 'tags: [개발일지]\n'
        printf -- '---\n\n'
        printf '%s\n' "$SECTION" | tail -n +2
      } > "$BLOG/_posts/$TODAY-dev-log.md"
      echo "post written: $BLOG/_posts/$TODAY-dev-log.md (title: $TITLE)"
    else
      echo "SKIP post — docs/jekyll.md 에 $TODAY 섹션 없음"
    fi
  else
    echo "SKIP post — $BLOG/_posts 없음"
  fi

  echo "=== done $(date +%H:%M:%S) ==="
} >> "$LOG" 2>&1
