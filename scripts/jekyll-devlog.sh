#!/bin/bash
# 매일 23:45 실행 — REMAKE DAY(com.remakeday) 당일 개발 이력을 docs/jekyll.md에 기록하고
# beyondbob.remakeday.com(지킬 허브)의 _posts/ 로 당일 섹션을 공개용으로 재작성해 복사.
#
# 등록: crontab "45 23 * * * /home/kimchungsik/projects/com.remakeday/scripts/jekyll-devlog.sh"
# 시간 분리 — 23:45 remakeday / 23:50 masterless / 23:55 beyondfacade / 23:59 lifetutorial(일시중지)
#
# 사용법:
#   jekyll-devlog.sh                                  기본 동작 — 1단계(docs/jekyll.md 갱신) 후
#                                                      어제·오늘 섹션의 허브 포스트를 재생성
#   jekyll-devlog.sh --posts-only DATE [DATE...]       1단계를 건너뛰고, 지정한 날짜(YYYY-MM-DD)들의
#                                                      허브 포스트만 docs/jekyll.md 원본 기준으로 재생성
#
# com.remakeday 의 git 커밋/푸시는 하지 않는다(docs/jekyll.md 는 사용자가 커밋).
# 허브 포스트는 새로 쓴 파일만 beyondbob 저장소에 커밋·푸시한다(scripts/beyondbob-publish.sh).
#
# 저장소 역할 분리:
#   com.remakeday/docs/jekyll.md                          ← 개발 작업만. 개발 일지의 원본(비공개 정보 포함 가능)
#   beyondbob.remakeday.com/_posts/YYYY-MM-DD-dev-log.md  ← 당일 섹션을 공개용으로 재작성한 사본(front matter 부착)
#   이 스크립트가 원본을 갱신한 뒤, 당일 섹션을 claude -p로 공개 버전으로 다시 써서 지킬 포스트로 저장한다.
#   재작성 결과가 금칙어 게이트를 통과하지 못하면 포스트를 쓰지/덮어쓰지 않고 로그에만 남긴다.
#   지킬 저장소에서 이 포스트를 직접 고치지 않는다 — 다음 실행 때 덮어쓰인다.

set -u
PROJECT=/home/kimchungsik/projects/com.remakeday
BLOG=/home/kimchungsik/projects/beyondbob.remakeday.com
LOG=/home/kimchungsik/.claude/jekyll-devlog-remakeday-cron.log
export PATH="/home/kimchungsik/.local/bin:$PATH"

TODAY=$(date +%Y-%m-%d)

POSTS_ONLY=()
if [ "${1:-}" = "--posts-only" ]; then
  shift
  POSTS_ONLY=("$@")
fi

cd "$PROJECT" || exit 1

# 공개 포스트에 남으면 안 되는 표현. 대소문자 무시 grep -E 로 검사한다.
FORBIDDEN_PATTERNS='pigfarm|양돈|돼지|TRUST_PROXY|X-Forwarded-For|CF-Connecting-IP|DEV_LOGIN|DEV_ACCOUNT_ID|dev/login|USER_DAILY_ATTEMPTS|DAILY_ATTEMPT_CAP|INSPECTOR_TOKEN|inspector_token'

# 게이트: $1 = 검사할 본문. 통과(0)면 GATE_HITS=0/GATE_WORDS="".
# 실패(1)면 본문이 비어 있거나(GATE_HITS=0) 금칙어가 있음(GATE_HITS=건수, GATE_WORDS=매치된 단어 목록).
gate_check() {
  local body="$1"
  GATE_HITS=0
  GATE_WORDS=""
  if [ -z "$body" ]; then
    return 1
  fi
  local hits
  hits=$(printf '%s' "$body" | grep -io -E "$FORBIDDEN_PATTERNS")
  if [ -z "$hits" ]; then
    return 0
  fi
  GATE_HITS=$(printf '%s\n' "$hits" | grep -c .)
  GATE_WORDS=$(printf '%s\n' "$hits" | tr '[:upper:]' '[:lower:]' | sort -u | paste -sd, -)
  return 1
}

# 재작성 결과가 원문과 무관한 내용으로 통째로 바뀐 경우를 잡는 최소한의 안전장치.
# (실측: claude -p 세션이 다른 대화 내용을 이어받아 원문과 무관한 응답을 낸 사례가 있었다 —
#  금칙어는 0건이라 gate_check만으로는 못 걸러낸다.) 재작성 본문의 줄 수가 원문의 절반에
# 못 미치면 차단한다. 정상 재작성은 일부 축약만 하므로 이 정도로는 걸리지 않는다.
fidelity_check() {
  local src="$1" new="$2"
  local src_lines new_lines
  src_lines=$(printf '%s\n' "$src" | grep -c .)
  new_lines=$(printf '%s\n' "$new" | grep -c .)
  [ "$new_lines" -ge $(( (src_lines + 1) / 2 )) ]
}

# docs/jekyll.md 의 하루 섹션 본문(제목 줄 제외)을 받아 공개 블로그용으로 재작성한 본문을 stdout에 낸다.
# 툴 사용·파일 수정 없이 claude -p 로만 실행한다.
generate_public_body() {
  local body="$1"
  {
    cat <<'PROMPT_HEADER'
아래는 비공개 개발 일지 docs/jekyll.md 의 하루 섹션(제목 줄 제외 본문)이다. 이 내용을 공개 블로그(blog.remakeday.com)에 올릴 수 있는 버전으로 다시 써라.

## 출력 규칙
- 완성된 포스트 본문 마크다운만 출력해라. 머리말, 설명, 코드펜스 없이 본문만 출력한다.
- 원문에 없는 내용을 지어내지 마라.
- 아래 "반드시 바꿀 것"·"반드시 줄이거나 뺄 것"에 해당하는 부분 외에는 문장을 원문 그대로 베껴 써라. 해당하지 않는 문장을 의역하거나 뭉뚱그리지 마라 — 표현·어휘·구체성을 원문 그대로 유지한다.

## 반드시 바꿀 것 — 게임 결말 정체 노출 표현 (아래 나열한 것만 해당. 확대 해석 금지)
- pigfarm, pigfarm_test, demo.pigfarm, demopigfarm 등 pigfarm 계열 식별자 → "게임 DB", "테스트 DB", "이전 데모 저장소" 같은 중립적인 표현으로 바꿔라.
- "양돈", "돼지" 단어, 그리고 게임 결말이 무엇인지 직접 밝히는 문장 → 중립적인 표현으로 바꾸거나 결말을 밝히지 않는 방식으로 다시 써라.
- 세계관·미술·연출 관련 표현(예: 소독·방역 모티프, LP01/LP02 이미지 스펙 이름, 도로 통제 표지판 등)은 이미 랜딩 페이지에 공개된 내용이다. 위 두 항목에 해당하지 않으니 절대 건드리지 말고 원문 그대로 남겨라.

## 반드시 줄이거나 뺄 것 — 보안·운영 민감 정보
다음 항목은 "배포 보안 점검 1건", "과잉 사용 방지 허들 적용" 처럼 한 줄 언급으로 축약하거나, 자연스러우면 아예 빼라. 구체적인 방법·경로·수치·환경변수 이름은 남기지 마라.
- 프록시 IP 신뢰 관련 보안 결함/우회 경로(TRUST_PROXY, X-Forwarded-For, CF-Connecting-IP 등)
- 개발용 계정 로그인 관련 세부사항(환경변수 이름, 엔드포인트 경로, 세션 무효화 결함과 수정 내용, 자격 증명 교체 메모)
- inspector 토큰
- 운영 한도 수치(사용자별 일일 게임 수, 전역 일일 상한, 분당 제한, 관련 변수명, 한도에서 계산한 "하루 최대 비용" 수치)

**여러 항목이 나열된 불릿·리스트(예: 리뷰 지적 사항 목록, Minor 항목 목록)에 위 대상이 섞여 있으면, 그 목록 전체를 "N건"으로 뭉뚱그리지 마라.** 목록은 그대로 유지하고 위 네 항목에 해당하는 개별 항목만 한 줄 요약이나 삭제로 바꿔라. 위 네 항목에 해당하지 않는 다른 항목(예: 검증 절차상의 결함, 테스트 커버리지 공백, UI 순서 문제)은 그 목록 안에서도 원문 그대로 남겨야 한다.

## 그대로 유지할 것
- 위 두 항목에 해당하지 않는 모든 문장 — 결정 사항과 그 이유, 모델 평가 결과, 게임당 비용, **테스트 건수와 통과 수치(예: "테스트 4개", "590 passed")**, 커밋 해시, 날짜, 세계관·미술·연출 표현을 포함해 전부 원문 그대로 옮긴다.
- 문체("-다" 평서형 종결, 굵은 리드 불릿, ### 소제목 구조)도 원문 그대로 유지한다.

## 원문
PROMPT_HEADER
    printf '%s\n' "$body"
  } | (
    # 프로젝트 폴더에서 돌리면 CLAUDE.md·자동 메모리·claude-mem 세션 훅이 비공개 맥락을 주입한다 — 빈 폴더에서 훅 없이 실행
    ISOLATED=$(mktemp -d) && cd "$ISOLATED" &&
      claude -p --tools "" --restricted --strict-mcp-config --permission-prompts none --no-session-persistence \
        --settings '{"disableAllHooks":true}'
    RC=$?; rm -rf "$ISOLATED"; exit $RC
  )
}

{
  echo "=== jekyll-devlog-remakeday run $TODAY $(date +%H:%M:%S) ==="

  if [ ${#POSTS_ONLY[@]} -eq 0 ]; then
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
- docs/model_evaluation.md 와 docs/metrics.yml 에 오늘 추가된 항목이 있으면 확인 (모델 평가 수치의 정본은 그쪽이다 — 일지에는 결론만 요약하고 정본 위치를 적는다)
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

    YESTERDAY=$(date -d "$TODAY -1 day" +%Y-%m-%d)
    DAYS=("$YESTERDAY" "$TODAY")
  else
    echo "posts-only 모드 — 1단계(docs/jekyll.md 갱신) 스킵, 대상 날짜: ${POSTS_ONLY[*]}"
    DAYS=("${POSTS_ONLY[@]}")
  fi

  WRITTEN_POSTS=()
  # 지정된 날짜들의 섹션 → 공개 재작성 → 게이트 → 지킬 포스트로 변환해 복사.
  # 섹션이 없으면 그 날짜 포스트는 건드리지 않는다. 게이트를 통과하지 못해도 건드리지 않는다.
  if [ -d "$BLOG/_posts" ]; then
    for DAY in "${DAYS[@]}"; do
      SECTION=$(awk -v d="## $DAY" '
        index($0, d) == 1 { f = 1 }
        f && /^## / && index($0, d) != 1 { exit }
        f { print }
      ' docs/jekyll.md)
      if [ -n "$SECTION" ]; then
        TITLE=$(printf '%s\n' "$SECTION" | head -1 | sed -E 's/^## [0-9-]+[[:space:]]*(—[[:space:]]*)?//')
        [ -z "$TITLE" ] && TITLE="개발 일지 $DAY"
        BODY_RAW=$(printf '%s\n' "$SECTION" | tail -n +2)

        PUBLIC_BODY=$(generate_public_body "$BODY_RAW")
        RC=$?

        if [ $RC -ne 0 ]; then
          echo "BLOCKED post $DAY — claude 재작성 호출 실패 (exit $RC)"
        elif ! fidelity_check "$BODY_RAW" "$PUBLIC_BODY"; then
          echo "BLOCKED post $DAY — 재작성 결과가 원문 대비 지나치게 짧음(내용 무관 가능성)"
        elif gate_check "$PUBLIC_BODY"; then
          {
            printf -- '---\n'
            printf 'title: "%s"\n' "${TITLE//\"/\\\"}"
            printf 'author: chungsik\n'
            printf 'tags: [개발일지]\n'
            printf -- '---\n\n'
            printf '%s\n' "$PUBLIC_BODY"
          } > "$BLOG/_posts/$DAY-dev-log.md"
          echo "post written: $BLOG/_posts/$DAY-dev-log.md (title: $TITLE)"
          WRITTEN_POSTS+=("_posts/$DAY-dev-log.md")
        elif [ -z "$PUBLIC_BODY" ]; then
          echo "BLOCKED post $DAY — claude 재작성 결과 비어 있음"
        else
          echo "BLOCKED post $DAY — ${GATE_HITS} hits: ${GATE_WORDS}"
        fi
      else
        echo "SKIP post — docs/jekyll.md 에 $DAY 섹션 없음"
      fi
    done
  else
    echo "SKIP post — $BLOG/_posts 없음"
  fi

  # 허브 반영 — 게이트를 통과해 새로 쓴 포스트만 커밋·푸시
  if [ ${#WRITTEN_POSTS[@]} -gt 0 ]; then
    "$PROJECT/scripts/beyondbob-publish.sh" "데브로그 자동 갱신 — ${WRITTEN_POSTS[*]##*/}" "${WRITTEN_POSTS[@]}"
  fi

  echo "=== done $(date +%H:%M:%S) ==="
} >> "$LOG" 2>&1
