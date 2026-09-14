# AGENTS.md — Frontend

These instructions apply to work under `frontend/` together with the repository-root `AGENTS.md`.

---

## 로컬 실행

- 개발 서버 포트: **3500**
- 백엔드 API: **http://localhost:8500**

## 프론트엔드 규약

아직 정해진 것이 없습니다.

현재 공통 규칙은 루트 `AGENTS.md`에 있으며 프론트엔드 전용 규칙은 이 파일에 둡니다. 스택, 디렉터리 구조, 상태 관리 및 테스트 규약이 정해지는 대로 이 문서에 추가합니다.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes—APIs, conventions, and file structure may all differ from your training data. Before writing Next.js code, read the relevant guide under `frontend/node_modules/next/dist/docs/`. In a monorepo, do not assume the `next` package is visible from the repository root. Follow all deprecation notices.

This block is maintained by `next dev`; verify its behavior in `frontend/node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only causes the uncommitted change to be recreated, so keep the generated block committed when Next.js updates it.

<!-- END:nextjs-agent-rules -->
