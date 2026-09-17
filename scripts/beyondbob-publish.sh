#!/bin/bash
# 지킬 허브(beyondbob.remakeday.com)에 자동화가 만든 파일만 커밋하고 푸시한다.
# jekyll-devlog.sh(포스트)와 jekyll-kanban-sync.sh(칸반 status)가 공용으로 쓴다.
#
# 사용법: beyondbob-publish.sh "커밋 메시지" 경로 [경로...]   (경로는 허브 저장소 기준 상대 경로)
#
# 규칙:
#   - 넘겨받은 경로만 커밋한다(git commit --only). 작업 트리의 다른 수정은 커밋에 섞지 않는다.
#   - 원격이 앞서 있으면 rebase 로 따라간다(다른 수정은 autostash 로 보존). 충돌하면 중단하고 푸시하지 않는다.
#   - 푸시가 실패해도 로컬 커밋은 남긴다 — 다음 실행이나 사람이 푸시하면 된다.
#   - 결과는 호출한 스크립트의 로그로 표준출력에 남긴다.

set -u
BLOG=/home/kimchungsik/projects/beyondbob.remakeday.com
MSG="$1"; shift

cd "$BLOG" || { echo "PUBLISH SKIP — $BLOG 없음"; exit 0; }

CHANGED=$(git status --porcelain -- "$@")
if [ -z "$CHANGED" ]; then
  echo "PUBLISH SKIP — 커밋할 변경 없음"
  exit 0
fi

git add -- "$@"
if ! git commit -q --only -m "$MSG" -- "$@"; then
  echo "PUBLISH BLOCKED — 커밋 실패"
  exit 0
fi
echo "PUBLISH commit $(git rev-parse --short HEAD) — $MSG"

if ! git fetch -q origin main; then
  echo "PUBLISH BLOCKED — fetch 실패, 로컬 커밋만 남김"
  exit 0
fi

if ! git merge-base --is-ancestor origin/main HEAD; then
  if ! git pull -q --rebase --autostash origin main; then
    git rebase --abort 2>/dev/null
    echo "PUBLISH BLOCKED — 원격과 충돌, 로컬 커밋만 남김(수동 정리 필요)"
    exit 0
  fi
fi

if git push -q origin HEAD:main; then
  echo "PUBLISH pushed $(git rev-parse --short HEAD) → origin/main (GitHub Actions가 허브를 재빌드)"
else
  echo "PUBLISH BLOCKED — push 실패, 로컬 커밋만 남김"
fi
