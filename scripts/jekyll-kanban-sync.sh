#!/bin/bash
# 매일 23:00 실행 — REMAKE DAY(com.remakeday) 개발 근거로 지킬 허브(beyondbob.remakeday.com) 칸반 카드 상태를 갱신.
#
# 등록: crontab "0 23 * * * /home/kimchungsik/projects/com.remakeday/scripts/jekyll-kanban-sync.sh"
# 시간 분리 — 23:00 remakeday 칸반 / 23:45 remakeday 데브로그(jekyll-devlog.sh) / 23:50 masterless / 23:55 beyondfacade
#
# 사용법:
#   jekyll-kanban-sync.sh              판정 후 칸반 yml 의 status 만 갱신
#   jekyll-kanban-sync.sh --dry-run    판정만 하고 파일은 건드리지 않음 (제안 목록만 로그·표준출력)
#   jekyll-kanban-sync.sh --no-publish 판정·반영은 하되 커밋·푸시는 하지 않음 (수동 확인 후 푸시할 때)
#
# 두 폴더의 역할:
#   com.remakeday                         ← 근거. docs/jekyll.md · docs/HANDOFF.md · git log · 파일 구성
#   beyondbob.remakeday.com/_data/kanban  ← 대상. 완료(done)가 아닌 카드만 판정한다
#
# 안전장치:
#   - 상태는 앞으로만 움직인다 (todo → doing → review → done). 사람이 올려둔 상태를 내리지 않는다.
#   - 각 카드 줄의 status 값만 바꾼다. 제목·완료 기준·다른 필드와 주석은 건드리지 않는다.
#   - 갱신 후 YAML 파싱이 하나라도 실패하면 전부 원래대로 되돌린다.
#   - 반영이 있으면 칸반 yml 만 커밋·푸시한다(scripts/beyondbob-publish.sh). 작업 트리의 다른 수정은 섞지 않는다.
#     --dry-run 이면 커밋·푸시도 하지 않는다.

set -u
PROJECT=/home/kimchungsik/projects/com.remakeday
BLOG=/home/kimchungsik/projects/beyondbob.remakeday.com
KANBAN="$BLOG/_data/kanban"
LOG=/home/kimchungsik/.claude/jekyll-kanban-remakeday-cron.log
export PATH="/home/kimchungsik/.local/bin:$PATH"

DRY_RUN=0
PUBLISH=1
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
[ "${1:-}" = "--no-publish" ] && PUBLISH=0

TODAY=$(date +%Y-%m-%d)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

exec 9>/tmp/jekyll-kanban-sync-remakeday.lock
if ! flock -n 9; then
  echo "=== jekyll-kanban-sync $TODAY $(date +%H:%M:%S) — 이미 실행 중, 건너뜀 ===" >> "$LOG"
  exit 0
fi

run() {
  echo "=== jekyll-kanban-sync run $TODAY $(date +%H:%M:%S) (dry-run=$DRY_RUN) ==="

  [ -d "$KANBAN" ] || { echo "SKIP — $KANBAN 없음"; return; }
  cd "$PROJECT" || { echo "SKIP — $PROJECT 없음"; return; }

  # 1. 판정 대상 카드 — done 이 아닌 카드만 한 줄씩
  python3 - "$KANBAN" > "$WORK/tasks.txt" <<'PY'
import sys, glob, os, yaml
for path in sorted(glob.glob(os.path.join(sys.argv[1], "*.yml"))):
    d = yaml.safe_load(open(path, encoding="utf-8"))
    for t in d.get("tasks", []):
        if t.get("status") == "done":
            continue
        print(f'{t["id"]} | {d["member"]} | {t["date"]} | 현재 {t["status"]} | {t["title"]} | 완료 기준: {t.get("dod","")} | 산출물: {t.get("output","")}')
PY
  TASK_COUNT=$(grep -c . "$WORK/tasks.txt")
  echo "판정 대상 카드: $TASK_COUNT 건"
  [ "$TASK_COUNT" -eq 0 ] && { echo "모든 카드가 완료 상태"; return; }

  # 2. 판정 요청 — 도구 없이, 빈 폴더에서, 훅 없이 (데브로그 스크립트와 같은 격리 방식)
  {
    cat <<PROMPT_HEADER
너는 팀 칸반 보드의 카드 상태를 실제 개발 근거와 대조하는 검토자다. 오늘은 $TODAY 이다.

칸반은 2026-09-03 에 "14일 계획"으로 작성됐고, 실제 개발은 그 뒤 계획과 다른 경로로 진행된 부분이 많다.
아래 "근거" 자료(개발 일지·인계 문서·커밋 기록·파일 구성)만 보고 각 카드의 상태를 판정해라.

## 상태 기준
- done: 카드 제목이 뜻하는 목적이 실제로 달성됐다는 근거가 있다. 완료 기준의 세부(포트 번호, 도구, 인원, 날짜)가 이후 결정으로 바뀌었어도 목적이 달성됐으면 done 이다. 이때 근거에 "방식 변경"을 밝혀라.
- review: 구현·산출물 근거는 있으나 완료 기준의 핵심 조건(검증·합의·확인)을 근거에서 확인할 수 없다.
- doing: 착수 근거는 있으나 아직 끝나지 않았다.
- todo: 근거가 없다. 계획이 폐기·대체되어 수행되지 않은 카드도 todo 로 둔다.

## 규칙
- 근거에 없는 사실을 추측하지 마라. 애매하면 낮은 단계를 골라라.
- 현재 상태보다 높은 단계로 바꿔야 하는 카드만 출력해라. 그대로이거나 낮춰야 하면 출력하지 마라.
- 출력은 JSON 배열 하나만. 설명·코드펜스 없이.
  형식: [{"id":"FE-01","status":"done","evidence":"근거 한 문장 — 날짜·문서 섹션·파일 경로를 짚는다"}]
- evidence 는 한국어 한 문장.

## 판정 대상 카드 (id | 담당 | 계획일 | 현재 상태 | 제목 | 완료 기준 | 산출물)
PROMPT_HEADER
    cat "$WORK/tasks.txt"
    echo
    echo "## 근거 1 — 커밋 기록 (com.remakeday, 2026-09-14 저장소 이관 이후. 그 이전 작업은 개발 일지에 있다)"
    git log --date=short --pretty='%ad %h %s'
    echo
    echo "## 근거 2 — 저장소 파일 구성 (경로 앞 3단계별 파일 수)"
    git ls-files | cut -d/ -f1-3 | sort | uniq -c
    echo
    echo "## 근거 3 — 화면 경로와 스크립트"
    git ls-files 'frontend/app/**/page.tsx' 'scripts/*' 'backend/scripts/*' 'frontend/tests/*' 'backend/alembic/versions/*'
    echo
    echo "## 근거 4 — 인계 문서 docs/HANDOFF.md"
    cat docs/HANDOFF.md
    echo
    echo "## 근거 5 — 개발 일지 docs/jekyll.md (최신 날짜가 위)"
    cat docs/jekyll.md
  } > "$WORK/prompt.txt"

  ( cd "$WORK" && timeout 1800 claude -p --tools "" --restricted --strict-mcp-config --permission-prompts none \
      --no-session-persistence --settings '{"disableAllHooks":true}' < "$WORK/prompt.txt" ) > "$WORK/verdict.txt" 2> "$WORK/claude.err"
  RC=$?
  if [ $RC -ne 0 ]; then
    echo "BLOCKED — claude 판정 호출 실패 (exit $RC): $(head -c 300 "$WORK/claude.err")"
    return
  fi

  # 3. 적용 — status 값만, 앞으로만, 파싱 실패 시 원복
  python3 - "$KANBAN" "$WORK/verdict.txt" "$DRY_RUN" > "$WORK/apply.txt" <<'PY'
import sys, glob, os, re, json, shutil, yaml

kanban, verdict_path, dry_run = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
RANK = {"todo": 0, "doing": 1, "review": 2, "done": 3}
LINE = re.compile(r'id:\s*([A-Z]+-\d+),.*?status:\s*(\w+),(\s*)priority')

raw = open(verdict_path, encoding="utf-8").read()
start, end = raw.find("["), raw.rfind("]")
if start < 0 or end < start:
    print(f"BLOCKED — 판정 결과에서 JSON 배열을 찾지 못함: {raw[:300]!r}")
    sys.exit(0)
try:
    verdicts = json.loads(raw[start:end + 1])
except json.JSONDecodeError as e:
    print(f"BLOCKED — 판정 결과 JSON 파싱 실패: {e}")
    sys.exit(0)

files = sorted(glob.glob(os.path.join(kanban, "*.yml")))
lines = {p: open(p, encoding="utf-8").read().split("\n") for p in files}
where = {}
for p, ls in lines.items():
    for i, l in enumerate(ls):
        m = LINE.search(l)
        if m:
            where[m.group(1)] = (p, i, m.group(2))

changed, skipped = [], []
for v in verdicts:
    tid, new, ev = v.get("id"), v.get("status"), (v.get("evidence") or "").strip()
    if tid not in where:
        skipped.append(f"{tid}: 칸반에 없는 id"); continue
    if new not in RANK:
        skipped.append(f"{tid}: 알 수 없는 상태 {new!r}"); continue
    p, i, old = where[tid]
    if RANK[new] <= RANK.get(old, 0):
        skipped.append(f"{tid}: {old} → {new} 는 앞으로 가는 변경이 아님"); continue
    line = lines[p][i]
    m = LINE.search(line)
    seg_old = f"status: {old},{m.group(3)}"
    seg_new = f"status: {new},"
    seg_new += " " * max(1, len(seg_old) - len(seg_new))
    lines[p][i] = line.replace(seg_old, seg_new, 1)
    changed.append((tid, os.path.basename(p), old, new, ev))

for tid, f, old, new, ev in changed:
    print(f"CHANGE {tid} ({f}) {old} → {new} | {ev}")
for s in skipped:
    print(f"SKIP {s}")
print(f"요약: 제안 {len(verdicts)}건 · 적용 대상 {len(changed)}건 · 제외 {len(skipped)}건")

if dry_run or not changed:
    sys.exit(0)

backup = {p: open(p, encoding="utf-8").read() for p in files}
for p, ls in lines.items():
    open(p, "w", encoding="utf-8").write("\n".join(ls))
try:
    for p in files:
        yaml.safe_load(open(p, encoding="utf-8"))
except yaml.YAMLError as e:
    for p, text in backup.items():
        open(p, "w", encoding="utf-8").write(text)
    print(f"ROLLBACK — 갱신 후 YAML 파싱 실패, 전부 원복: {e}")
    sys.exit(0)
print(f"written: {len(changed)}건 반영")
PY
  cat "$WORK/apply.txt"

  # 4. 허브 반영 — 칸반 yml 에 커밋 안 된 변경이 있으면 커밋·푸시 (오늘 반영분 + 이전에 못 올린 변경)
  #    변경이 없으면 beyondbob-publish.sh 가 아무것도 하지 않는다
  WRITTEN=$(sed -n 's/^written: \([0-9]*\)건 반영$/\1/p' "$WORK/apply.txt")
  if [ "$DRY_RUN" -eq 0 ] && [ "$PUBLISH" -eq 1 ]; then
    "$PROJECT/scripts/beyondbob-publish.sh" "kanban: 개발 근거로 카드 상태 자동 동기화 $TODAY (오늘 ${WRITTEN:-0}건)" _data/kanban
  fi

  echo "=== done $(date +%H:%M:%S) ==="
}

run 2>&1 | tee -a "$LOG"
