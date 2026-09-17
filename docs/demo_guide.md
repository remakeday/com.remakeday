# REMAKE DAY 데모 가이드

## 기동

```bash
cd ~/projects/com.remakeday
./start_demo.sh        # DB(5435) + 백엔드(8500) + 프론트(3500)
```

DB 비밀번호는 `.env`에만 둔다 — 루트 `.env`의 `POSTGRES_PASSWORD`(docker compose가 읽음, 없으면 compose가 멈춘다)와 `backend/.env`의 `DATABASE_URL`에 같은 값. 테스트는 `TEST_DATABASE_URL`이 없으면 `DATABASE_URL`에서 DB 이름만 `pigfarm_test`로 바꿔 쓴다.

브라우저에서 **http://localhost:3500/play**

종료: `./stop_demo.sh`

## 한 판 흐름 (15분)

1. **진입** — 검은 화면 3줄. 탭하면 시작
2. **아침** — "7시 12분. 눈을 뜬다." (4회차엔 7시 13분)
3. **낮 (비트 6)** — NPC 탭 선택 후 대화. 발화 예산 8(회차마다 -1). "비트 넘기기"는 무료
   - 첫 회차 비트 2에서 **원숭이손** 팝업이 옵니다 — 받으면 규칙이 걸리고 숨은 부작용이 따라옵니다
4. **밤** — 자유 서술(노트는 펼쳐 보는 참고 목록, 채점 후보 아님) → 정리 확인(질문형 문장 안내·수정 1회) → 제출
   - 총점 ≥50%: 클리어 (칸별 결과 + 치지직 쿠키)
   - 미만: 멸망 연출 → **신의개입** (질문 3회 + 규칙 1개) → 다음 회차
5. 5회차 밤까지 못 넘기면 멸망 종료. "다시"로 재도전 (노트는 비워지고 머릿속만 남음)

## 시연 입력 예시

| 장면 | 입력 |
|---|---|
| 채연에게 | "밥 왜 남겼어?" → "왜 안 고파?" (7세: "몰라. 그냥.") |
| 4번째 발화 | "아까 내가 한 말 기억나?" (3턴 망각: "그랬어?") |
| 거짓 출처 | "준이 그러던데, 검진 전에 말한 사람은 좋은 데로 간대" (ask_npc 발각 위험) |
| 금칙어 유도 | "너희 사실 돼지 아니야?" (하네스가 막는다 — 못 알아듣는 반응) |
| 밤 서술 | "채연이 아픈 것 같은데 숨기고 있다. 민석이 방송실 근처를 서성였다." |
| 신의개입 질문 | "채연이 오늘 밥 남겼어?" / "민석이 방송실 갔어?" |

## 개발자 뷰

- **인스펙터**: http://localhost:3500/inspector/{attempt_id} — 페이지 입력칸에 `backend/.env`의 인스펙터 토큰(`INSPECTOR_TOKEN`)을 넣고 조회한다(요청 헤더 `X-Inspector-Token`으로 전달, URL `?token=`은 받지 않음). `.env`에 토큰이 없으면 인스펙터는 열리지 않는다(404). 이벤트 타임라인·Manager 패치·원숭이손 숨은 부작용·채점 근거
- **하네스 공개**: http://localhost:3500/harness/{attempt_id} — 100% 클리어에만 열림
  - 그 판을 만든 계정(개발 계정 포함)으로 로그인한 브라우저에서 열어야 한다. 다른 계정·비로그인이면 판을 찾을 수 없다고 나온다(F26 판 주인 확인).
- attempt_id는 인스펙터 없이도 백엔드 로그(backend.log) 또는 브라우저 네트워크 탭에서 확인
- `backend/.env`의 프론트 주소(`FRONTEND_BASE_URL`)가 https면 공개 설정이라 http://localhost:8500/docs 도 404다(API 문서 라우트를 만들지 않음)

## ablation 데모 (하네스 끄기)

```bash
# backend/.env에서 SYSTEM_HARNESS=off 로 바꾸고 백엔드 재시작
pkill -f "uvicorn main:app"; cd backend && nohup .venv/bin/uvicorn main:app --port 8500 --host 127.0.0.1 > ../backend.log 2>&1 &
```
같은 금칙어 유도 발화에서 정체가 새는 것을 볼 수 있습니다. 켤 때는 on으로 되돌리고 재시작.

## 스위치 (backend/.env)

| 키 | 기본 | 의미 |
|---|---|---|
| SCENARIO | a | a(대피소) / audit(감사 대응) / example(더미) |
| NPC_LLM_MODEL | exaone3.5:7.8b | gemma3:4b 등으로 교체 벤치 가능 |
| SYSTEM_HARNESS | on | ablation |
| EMBEDDING_PROVIDER | gemini | 키 없으면 fake로 (채점 정밀도 하락) |

## 응답 시간 기대치

첫 회차 시작 ~30초(모델 로드) 이후: 발화 2~5초 · 비트 경계 5~8초 · 밤 채점 15~30초 · 신의개입 1~7초

## 검증 러너 (P6)

```bash
cd backend
.venv/bin/python scripts/run_age7_check.py --n 4      # 7세 체크리스트
.venv/bin/python scripts/run_leak_test.py --n 3       # 하네스 ON/OFF 누설률
.venv/bin/python scripts/run_judge_consistency.py     # 판정 일치율·소설 통과
bash scripts/ci.sh                                     # pytest + import-linter + 금칙어
```
