# 연결형 추리 구현 — 테스트 실행 이력

날짜: 2026-09-09  
범위: 연결형 추리, 이미지 A안, frontend, 격리 API, 실제 Ollama 검증, Gemini adapter·pacing·로컬 전환 확인

## 집계 원칙

이 문서는 **실행 횟수**, **한 실행에서 수집한 테스트 항목 수**, **스크립트 assertion 수**, **HTTP 요청 수**, **모델 provider 호출 수**를 서로 더하지 않는다.

- `278 passed`는 pytest 한 번이 수집한 테스트 항목 278개다. 테스트 명령을 278번 실행했다는 뜻이 아니다.
- API의 25 checks, 브라우저의 14 assertions·3 composite checks는 해당 관찰 스크립트의 판정 항목이다. pytest 항목과 합산하지 않는다.
- 실제 모델의 24 provider outputs은 모델 경계 호출 수다. 질문·통제·custom·ambient 사례 수와 다르고, 테스트 통과 수로 환산하지 않는다.
- 아래 실행 횟수는 문서·raw·도구 결과에서 서로 다른 명령 결과를 식별할 수 있는 **확인 가능한 최소 실행 횟수**다. 중간의 모든 재실행 로그가 영구 보존된 것은 아니므로 정확 총계는 미확정이다.
- 동일 artifact가 owner 보고와 독립 reviewer 보고에 함께 인용되면 실행을 한 번만 센다. reviewer가 “독립 실행”이라고 명시한 명령은 별도 실행으로 센다.

## 현재 gate

- 질문 해석·근거 판단을 두 단계로 분리한 이전 source checkpoint는 전체 suite **289 passed, 3 existing warnings, 6.61s, exit0**, root exec session `81396`이었다. focused pure suite는 owner와 독립 reviewer가 각각 **82 passed**를 확인했다.
- 06:28 UTC(15:28 KST) 실제 모델에서 해석 단계 fallback과 극성·시간 손실이 확인돼 backend 구조를 다시 단순화했다. 후속 enum 소스는 owner pure **86 passed**, 전체 DB suite **293 passed, 3 existing warnings, 6.84s, exit0**, root exec session `19546`을 확인했다. 코드 gate는 통과했고 실제 모델 재검토는 진행 중이다.
- adapter 추가 전 bounded-prompt 소스는 owner pure **100 passed**, 전체 DB suite **307 passed, 3 existing warnings, 6.73s, exit0**, root exec session `88434`을 확인했다. 직전 source-local 소스의 독립 reviewer pure100은 별도 실행이다.
- 06:47 후속 실행은 원문12 + 통제10 + custom3 + ambient3에서 harness44, provider output46, accepted43, rejected3, provider error0, final fallback1이었다. PC4·SPC2의 부정 관계는 정상화됐지만 PC3 공개 여부, PC6 이유, PC7 미래 시점과 Q6 조건 표현에서 의미 손실이 남았다. **RM1 P1은 아직 열려 있다.**
- 같은 질문·public corpus를 Exaone advisor로만 바꾼 06:55 비통계 비교도 PC3·SPC2를 틀리고 일부 질문을 반전하거나 발명했다. 제품 모델은 바꾸지 않았으며 이 비교도 RM1을 닫지 못했다.
- 최종 07:35 실행은 kind21/21과 인용30개 원문 일치를 확인했지만 SPC2의 명시적 공개 기록과 부정 질문을 supported로 답했다. 여러 다른 의미 오분류도 guard가 최종 응답만 보호했다. **RM1 P1과 기능 전체 의미 승인은 열려 있다.**
- Gemini/Ollama adapter 추가 뒤 owner pure118, 독립 reviewer targeted18, 전체 DB suite **325 passed, 3 existing warnings, 6.49s, exit0**, root exec session `61313`을 확인했다. 이는 pacing 추가 전 checkpoint다. 이후 전체 suite는 **327 passed, 3 existing warnings, 6.86s, exit0**, root exec session `60744`, 독립 reviewer targeted suite는 **20 passed, 0.25s**였다.
- 사용자 선택으로 core를 Gemini 3 Flash(`gemini-3-flash-preview`)로 전환했고 process-wide 10 RPM pacing을 적용했다. 실제 제품 adapter 단일 structured 호출은 2.543초에 기대 답 `no`를 반환했다. 2026-09-09 17:15:54 KST 이 PC 로컬 health는 core `gemini:gemini-3-flash-preview`, NPC `ollama:exaone3.5:7.8b`, embedding `gemini`, DB `ok`였고 localhost3500 `/play`은 HTTP200이었다. Gemini 전체 corpus 의미 검증과 다른 PC 접속 확인은 아직 별도다.

## Backend pytest — 전체 suite checkpoint

각 행은 식별 가능한 pytest 명령 한 번이다. `수집 항목`은 실행된 테스트 항목의 pass/failure/error 합계다. import 수집 실패는 통과 항목으로 세지 않는다.

| 최소 실행 # | 소스 시점 | 결과 | 수집 항목 | 해석·근거 |
|---:|---|---:|---:|---|
| 1 | 초기 연결 구현 | 171 passed / 32 failed | 203 | 구 계약 기대와 실제 회귀를 분류한 첫 전체 checkpoint. [backend progress](backend-progress.md#existing-test-change-classification) |
| 2 | 독립 리뷰 전 구현 | 198 passed / warnings3 | 198 | 첫 구현 handoff. [backend progress](backend-progress.md#review-handoff-checkpoint) |
| 3 | BR1–BR4 수정 | 204 passed / warnings3 | 204 | 중복 단서·동일 극성·계측·조회 수정 뒤. [backend progress](backend-progress.md#independent-review-fixes-and-server-handoff) |
| 4 | BR5–BR7 수정 | 211 passed / warnings3 | 211 | 중복 원숭이손 비용, provider 실패 기록, scene transaction 수정 뒤. |
| 5 | 실제 모델 grounding 1차 수정 | 232 passed / 12 failed | 244 | 오래된 free-text/null/prompt 기대 11건과 ambient note 실제 회귀1건을 분리. |
| 6 | 위 회귀 수정 중 | 243 passed / 1 failed | 244 | 새 assertion의 suppressed caption 기대 오류1건 확인. |
| 7 | grounding sandbox 실행 | 244 setup errors | 244 | PostgreSQL socket 접근 차단. backend exec session `14686`, 약28.15s. 기능 failure로 세지 않음. |
| 8 | grounding 권한 실행 | 244 passed / 6.19s / exit0 | 244 | owner tool chunk `95d1cf`. |
| 9 | grounding 최종 재실행 | 244 passed / warnings3 / 6.33s / exit0 | 244 | owner tool chunk `b9e403`. 같은 수의 별도 실행. [backend progress](backend-progress.md#real-model-grounding-repair--final-backend-checkpoint) |
| 10 | relation 수정 후 sandbox 실행 | 254 setup errors | 254 | PostgreSQL socket 접근이 sandbox에서 막힌 환경 실패. `/tmp/connected-backend-suite-final.log`는 이 실패 원문이며 성공 근거가 아니다. |
| 11 | 같은 소스 권한 실행 | 254 passed / warnings3 / 6.23s / exit0 | 254 | root exec session `78183`. 실행10의 제품 회귀가 아님을 확인. |
| 12 | same-event context 수정 | 261 passed / warnings3 / 6.95s / exit0 | 261 | root exec session `8668`. 254와 다른 소스 checkpoint. |
| 13 | polarity/lookup 분리 | 278 passed / warnings3 / 7.22s / exit0 | 278 | root exec session `35068`. 이후 두 단계 분리 변경 전 checkpoint. |
| 14 | two-stage checkpoint | 289 passed / warnings3 / 6.61s / exit0 | 289 | root exec session `81396`. 이후 06:28 의미 실패에 따른 단순화 전 checkpoint. |
| 15 | coherent interpretation enum | 293 passed / warnings3 / 6.84s / exit0 | 293 | root exec session `19546`. 코드 gate 통과; 실제 모델 의미 gate는 별도. |
| 16 | whole-claim direct entailment | 294 passed / warnings3 / 6.63s / exit0 | 294 | root exec session `82930`. 코드 gate 통과; 실제 모델 의미 gate는 별도. |
| 17 | source-local evidence | 307 passed / warnings3 / 6.66s / exit0 | 307 | root exec session `84558`. 코드 gate 통과; 실제 모델 의미 gate는 별도. |
| 18 | final bounded prompts | 307 passed / warnings3 / 6.73s / exit0 | 307 | root exec session `88434`, source hash `6fb42a73…a2d8d9`. 최종 코드 gate; 의미 gate 실패 뒤 추가 수정 없음. |
| 19 | Gemini/Ollama adapter | 325 passed / warnings3 / 6.49s / exit0 | 325 | root exec session `61313`. Adapter 코드 gate이며 실제 Gemini 생성·의미 gate와 다름. |
| 20 | pacing 추가 뒤 환경 설정 누락 | import collection errors27 / 0.40s / exit2 | 미실행 | backend cwd에서 `.venv/bin/pytest -q`; `PYTHONPATH` 누락으로 수집 실패. 통과 테스트에 포함하지 않음. |
| 21 | pacing 추가 뒤 올바른 환경 | 327 passed / warnings3 / 6.86s / exit0 | 327 | root exec session `60744`. 명시적 `PYTHONPATH`와 정리된 환경에서 `.venv/bin/python -m pytest -q`; 정확 명령은 [최종 요약](final-validation-summary.txt). |

warnings3은 기존 Starlette TestClient/httpx, anyio BlockingPortal, google-genai UnionGenericAlias deprecation이다. pass 수 증가 자체는 품질 지표가 아니라 테스트 파일 추가와 계약 갱신도 반영한다.

## Backend pytest — focused·red/green 실행

owner 도구 결과와 reviewer의 “독립 실행” 기록을 대조하면 이번 연결형 재설계에서 확인 가능한 backend pytest는 **최소81회**다: full-suite 명령 시도21회 + owner focused49회 + reviewer 독립 focused11회. full21에는 import 수집 실패1회가 포함되며 이를 통과 테스트로 세지 않는다. 권한 대기 뒤 실행 담당을 바꾼 미실행 요청은 세지 않았다. 영구 로그가 없는 중간 실행이 더 있을 수 있어 정확 총계는 미확정이다.

| 종류 | 식별 가능한 실행 결과 | 의미 |
|---|---|---|
| 관찰/이전 답안 milestone | 4 red → 4 passed | owner2회. 기능 부재를 먼저 재현. |
| BR5–BR7 | pure4 passed; DB+pure targeted7 passed | owner2회. provider/비용 pure와 실제 PostgreSQL fault injection. |
| 직접 규칙 이름 경계 | target12: 7 failed/5 passed → whole pure16 passed | owner2회. 별도 “target12 pass” 실행 증거는 없고 16 안의 부분집합이다. |
| 실제 모델 grounding 회귀 | target12 fail → 23 pass/5 fail → 28 pass → 34 pass → target20 pass/1 fail → pure37 pass → pure37 재실행 pass | owner7회. detail/ID/부분 근거/ambient 발명 교정 과정. |
| relation/relevance | 8 fail/1 pass → target9 pass → pure45 pass/1 fail → pure46 pass → pure47 pass | owner5회. 관계·관련 source·`말이야` 경계. |
| same-event scope | target2 fail/5 pass → pure54 pass | owner2회. evidence-first와 actor/loop/beat/scene context. |
| polarity/lookup | 7 fail/8 pass → target15 pass → pure66 pass/3 fail → pure69 pass → pure71 pass | owner5회. 별도 targeted17 실행은 없고 두 케이스는 pure71 전에 추가됐다. |
| two-stage 분리 | target9 fail → target9 pass → pure80 pass → pure82 pass | owner4회. 질문-only 해석과 positive-claim/lookup 근거 판단 입력, 단계별 failure audit. |
| coherent interpretation enum | stage12 fail/2 pass → whole pure2 fail/83 pass → stage1 fail/14 pass → whole pure86 pass | owner4회. enum schema·temperature red와 방송 partial-evidence red를 차례로 교정. [backend progress](backend-progress.md#coherent-interpretation-enum-after-062838-real-model-failure) |
| whole-claim direct entailment | stage11 fail/4 pass → stage4 fail/11 pass → whole pure86 pass → whole pure87 pass | owner4회. 부정 재합성을 제거하고 원질문 범위의 평서 명제를 근거와 직접 비교하며 재시도 피드백을 추가. [backend progress](backend-progress.md#whole-claim-entailment-after-063851-live-double-negation-failure) |
| source-local evidence | test file missing exit4/no tests → target11 fail/3 pass → unchanged red11 fail/3 pass → target14 pass → whole pure100 pass | owner5회. source마다 인용과 relation을 판정. 경로 편집 오류 뒤 같은 red를 한 번 더 실행한 사실도 포함. [backend progress](backend-progress.md#source-local-evidence-after-quote-first-diagnostic) |
| final bounded prompts | prior-code pure100 pass → saved current-code pure100 pass | owner2회. 첫 실행은 저장되지 않은 compile-error patch 때문에 이전 소스를 실행했고, 두 번째가 최종 prompt 소스다. [backend progress](backend-progress.md#final-bounded-prompt-follow-up-before-the-last-full-corpus-run) |
| Gemini adapter | target18 fail → target18 pass → whole pure118 pass | owner3회. SDK mock, structured JSON, factory와 기존 provider 회귀. [adapter progress](adapter-progress.md) |
| Gemini process-wide pacing | target1 fail → target1 pass | owner2회. 기본 10 RPM pacing의 red/green. |
| reviewer 독립 실행 | 이전 pure9회 + Gemini adapter targeted18 pass + pacing 포함 targeted20 pass(0.25s) | reviewer11회. owner 결과와 다른 명령이며 DB suite는 재실행하지 않음. |

아키텍처 import contract4/4와 코어 금칙어0은 여러 안정 checkpoint에서 반복됐다. 개별 command 원문이 모두 남아 있지 않아 실행 횟수 합계를 추정하지 않는다. 최신 기록은 119 files/230 dependencies, core83 files다.

## Frontend type/build/browser 실행

frontend 명령은 pytest와 별도다. 문서에서 구별되는 명령은 아래와 같으며, 모든 중간 재실행의 정확 총계는 미확정이다.

| 계열 | 실행 이력 | 항목 수와 판정 |
|---|---|---|
| TypeScript | `npx tsc --noEmit` 최종 exit0 | typecheck 한 실행. assertion 수로 환산하지 않음. |
| 기본 build | `npm run build`가 Google font network 제한에 막힘 → 재시도에서 Turbopack port bind `EPERM` | 최소2회 환경 차단. source compile 실패로 세지 않음. |
| webpack build | `npx next build --webpack` exit0 | compile/typecheck 후 4/4 pages 생성. build 한 실행. |
| connected browser TDD | 구현 전 `낮의 노트 열기` timeout red → 최종 exit0 | 최소2회. 최종은 notebook, 고정 초상, 이전 답안, gallery, 질문, rule preview/apply, 390px, focus, N/A를 한 복합 흐름에서 확인. |
| five-loop mock | exit0 | 한 실행, 보존 artifact 기준 **14 assertions**, 오류0. 최종0/100·회고·retry. |
| scene illustrations mock | exit0 | 한 실행. new/legacy/unknown 이미지, 390/1440, 비트 비소비, outcome 분기. 내부 assertion 정확 수는 보고서에 별도 총계 없음. |
| 독립 frontend review | Chrome sandbox `setsockopt EPERM` 실패 → 권한 실행 exit0 → 390/1440 geometry 재확인 exit0 | 최소3회. focus/inert/Escape/원문·시간순·지연 복원 포함. |

상세 명령과 검증 범위: [frontend progress](frontend-progress.md#verification-ledger), [frontend independent review](frontend-review.md).

## 격리 API와 실제 frontend 통합

| 실행 | 실행 횟수 | 판정 항목·트래픽 | 결과·경계 |
|---|---:|---:|---|
| `test_db` fake API 5회차 | 1 | 25 checks, HTTP request/response 117건 | failed check0. note linkage154/154, rule compliance19/19. 이후 C3/RM 수정 전 소스라 최종-source smoke로 사용하지 않음. [report](integration-artifacts/live-api/report.json), [traffic](integration-artifacts/live-api/traffic.json) |
| 실제 frontend + test API 첫 browser | 1 | 시작 문구 대기 | `127.0.0.1:3500`에서 hydration/HMR 환경 문제. API 판 생성 없음. |
| 두 번째 browser | 1 | monkey-paw 중간 상태 | disabled 버튼 timing으로 종료. test 판1개가 생성됐지만 완료되지 않음. |
| 세 번째 browser | 1 | mobile390 + desktop1440 복합 checks2 | errors0, failed requests0. 각 viewport에서 하루 낮·밤, seen gallery, portrait, clue07–12, overflow를 확인. [report](integration-artifacts/live-browser-rerun3/report.json) |
| real frontend/mock connected | artifact 기준1 | composite checks3 | errors0. owner browser 실행과 artifact가 겹칠 가능성이 있어 전체 frontend 실행 수에 중복 합산하지 않음. [results](integration-artifacts/mock-connected/results.json) |
| real frontend/mock five-loop | artifact 기준1 | assertions14 | errors0. 위와 같은 중복 경계. [results](integration-artifacts/mock-five-loop/results.json) |

실제 HTTP 자동 실행은 사람 첫 플레이 표본이 아니다. 운영 DB `game_db`에는 판 생성·reset·재채점이 없었다.

## 실제 Ollama 실행

`사례`는 questions + controls + custom + ambient 입력 묶음 수다. `provider 호출`은 실제 모델 경계의 call record 수다. Q12와 custom preview는 결정적 코드 경로라 provider를 호출하지 않는다.

raw 시각은 UTC이며 괄호에 같은 날 KST(UTC+9)를 표시한다.

| raw UTC (KST) | 사례 | provider 호출 / 재시도 | fallback·오류 | 의미 변화와 결함 |
|---|---:|---:|---:|---|
| [03:58:04](real-model-artifacts/probes-20260909T035804Z.json) (12:58) | 12 Q + 3 custom + 3 ambient = 18 | 39 = 질문36(각3회, 재시도24) + ambient3 | 질문 fallback12, provider error0 | 질문 detail 누락으로 12개 전부 fallback. ambient3은 기계 검사 통과했지만 취향·숫자·완료·웃음·과거 부재를 발명해 의미 gate3/3 실패. |
| [04:17:23](real-model-artifacts/probes-20260909T041723Z.json) (13:17) | 12 Q + controls3 + custom3 + ambient3 = 21 | 16 = advisor14 + ambient2, 재시도0 | fallback0, error0 | Q1–11 형식 복구. controls0/3, Q1/Q4/Q10/Q11 relevance 문제. A1/A2 안전, A3는 `말이야` 오탐으로 호출0. |
| 04:40:44 (13:40) sandbox raw | 12 Q + controls4 + custom3 + ambient3 = 22 | provider attempt18 | fallback18, ConnectError18 | 약66ms 접근 차단 진단. 모델 성공0이며 의미 결과로 사용하지 않음. 원문은 `/tmp`에만 있고 [독립 검토의 접근 차단 절](real-model-review.md#044044-파일-실재-확인--실모델-검증-아님-provider-접근-차단)에 hash·집계 보존. |
| [05:41:43](real-model-artifacts/probes-20260909T054143Z.json) (14:41) | 12 Q + controls4 + custom3 + ambient3 = 22 | 18, 재시도0 | fallback0, error0 | 실제 output18 모두 accepted. RM2/RM3 닫힘, PC1/2/4 통과. PC3 공개 긍정 질문이 unknown이라 RM1 유지. root session19347 exit0. |
| [05:54:16](real-model-artifacts/probes-20260909T055416Z.json) (14:54) | 12 Q + controls4 + custom3 + ambient3 = 22 | 20 = 최종 task18 + Q2 rejected2 재시도 | fallback0, error0 | PC3는 contradicted로 교정됐지만 PC4 미공개 부정 질문이 contradicted로 회귀. accepted18/rejected2. root session89256 exit0. |
| [06:10:38](real-model-artifacts/probes-20260909T061038Z.json) (15:10) | 12 Q + controls10 + custom3 + ambient3 = 28 | 24, 재시도0 | fallback0, error0 | accepted24. 원래 PC3/PC4와 PC1–5 관계는 통과. synthetic 공개 source의 부정 질문 SPC2를 supported로 잘못 판정했고 PC6 이유·PC7 미래·PC8 실제 이행 등 내부 의미가 불완전. RM1 P1 유지. root session85107 exit0. |
| [06:28:38](real-model-artifacts/probes-20260909T062838Z.json) (15:28) two-stage raw | 12 Q + controls10 + custom3 + ambient3 = 28 | 51 calls / extra attempts12; accepted33, rejected18 | final fallback6, provider error0 | PC1/2/3/SPC1은 첫 해석이 open이라 fallback, PC4 evidence unknown, PC7 시간 손실 fallback, PC8 negative 오분류. RM1 실패. SHA `049f9acd…dc3b`. |
| [06:38:51](real-model-artifacts/probes-20260909T063851Z.json) (15:38) enum raw | 12 Q + controls10 + custom3 + ambient3 = 28 | harness45 / provider outputs47; accepted44, rejected3 | final fallback1, provider error0 | PC3는 ID 없는 denied를 세 번 내 fallback unknown, SPC2는 이중 반전 오답. PC4의 최종 supported도 negative claim과 evidence 오분류가 상쇄된 우연한 결과라 gate 실패. SHA `db888567…7e316`. |
| [06:47:53](real-model-artifacts/probes-20260909T064753Z.json) (15:47) whole-claim raw | 12 Q + controls10 + custom3 + ambient3 = 28 | harness44 / provider outputs46; accepted43, rejected3 | final fallback1, provider error0 | PC4/SPC2 부정 관계는 정상. PC3 공개 여부, PC6 이유, PC7 미래 시점과 Q6 조건 표현에서 의미 손실. RM1 실패. SHA `7c6b057b…443a9`. |
| [06:55:04](real-model-artifacts/probes-exaone-20260909T065504892941Z.json) (15:55) Exaone comparison | 12 Q + controls10 + custom3 + ambient3 = 28 | harness45 / provider outputs51; accepted45, rejected6 | final fallback0, provider error0 | 동일 corpus·기대 근거의 비통계 A/B. PC3/SPC2 오답, Q7 의미 반전, Q8–Q11 첫 답변 발명으로 RM1 실패. 제품 모델 변경 아님. SHA `d797217c…be315c`. |
| [07:19:26](real-model-artifacts/probes-20260909T071926Z.json) (16:19) source-local raw | 12 Q + controls10 + custom3 + ambient3 = 28 | harness45 / provider outputs46; accepted45, rejected1 | final fallback0, provider error0 | accepted quote79개 모두 원문 substring. PC3/SPC2가 lookup→supported 오답, PC7 unknown도 guard의 우연한 보호라 RM1 실패. SHA `2f07c1fc…56b814`. |
| [07:35:56](real-model-artifacts/probes-20260909T073556Z.json) (16:35) final raw | 12 Q + controls10 + custom3 + ambient3 = 28 | harness45 / provider outputs45; accepted45, rejected0 | final fallback0, provider error0 | kind21/21, quote30개 모두 원문 일치. SPC2가 명시적 공개 기록에도 부정 질문을 supported로 답해 RM1 실패. PC6과 원문 Q1/2/4/8/9/10/11 일부 중간 오분류는 guard가 최종 응답만 보호. SHA `adf69d8b…b969a4`. |

모델 실행 전의 두 운영 실패도 구분해 보존한다.

- 최초 명령은 작업 디렉터리/PYTHONPATH가 맞지 않아 `apps` import 전에 종료됐다. provider 호출0이므로 모델 표본이나 테스트 통과/실패로 세지 않는다.
- 04:40은 command exit0이지만 provider 예외를 harness fallback으로 처리한 결과다. exit0을 모델 성공으로 해석하지 않는다.

실제 모델 결과의 문항별 판정과 hash는 [real-model review](real-model-review.md)에 있다. provider 성공률, 통제 판정, 사람 정확도, 사용자 체감은 서로 다른 지표다.

### 별도 모델 진단

[07:07:29 UTC(16:07 KST) 진단](real-model-artifacts/nli-diagnostic-20260909T070729518766Z.json)은 Gemma3 12b, temperature0에서 네 문항을 기존·간결·인용 우선 입력으로 각각 실행한 **12 provider calls**이며 모두 HTTP200, 오류0이었다. 관계 일치는 기존3/4, 간결3/4, 인용 우선4/4였고 인용6개는 모두 지정한 원본 ID의 substring이었다. SHA는 `717be685…32f8a`다.

이 진단은 전체 12+10+3+3 corpus 재실행과 별도 계열이다. PC3/SPC1 입력에는 reported·observed 근거가 섞여 현재 제품의 blanket guard라면 unknown이므로, 인용 우선4/4를 제품 통과·RM1 종료·사람 정확도로 해석하지 않는다. source별 판정, 집계, kind-only 경로도 검증하지 않았다.

- [07:25:15 kind 진단](real-model-artifacts/kind-diagnostic-20260909T072515636890Z.json): 28 HTTP200, 오류0. classification 후보21개는 모두 기대 kind와 일치했고, 올바른 kind를 강제한 evidence7의 인용11개도 원문이었다. 그래도 PC3·SPC2·PC6·PC7 근거 판단이 틀렸고 제품 집계라면 PC3·SPC2·PC7이 오답이다. SHA `47429c71…7fd0f9`.
- [07:29:00 explicit-semantics 진단](real-model-artifacts/answer-semantics-diagnostic-20260909T072900364027Z.json): 7 HTTP200, 오류0, 인용9개 원문 일치. source 의미5/7, 제품 guard 적용 최종6/7이었다. SPC2와 PC6이 남아 RM1을 닫지 못했다. SHA `db33d6c4…f8cd59`.

두 진단 모두 제품 API 실행이나 전체 corpus 재실행이 아니다. 분류 성공, 일부 관계 일치, guard가 막은 최종 status를 기능 전체 성공이나 사람 정확도로 승격하지 않는다.

## 권한·환경 중단 이력

- PostgreSQL을 사용하는 full suite는 sandbox socket 제한으로 254 setup errors가 난 뒤 권한 실행에서 254 passed로 확인됐다.
- 후속 full-suite 권한 요청 한 건은 약576.4초 대기 뒤 root가 해당 요청을 중단하고 실행 담당을 전환했다. 이 요청에는 실행 결과가 없어 실행 횟수나 실패 테스트 수에 포함하지 않는다. root가 같은 범위의 명령을 정상 권한 중계해 성공 결과를 별도로 남겼다.
- frontend 기본 build는 network와 port-bind 제약을 분리해 기록했고 webpack build로 실제 compile을 검증했다.
- browser reviewer의 Chrome sandbox 실패는 같은 bounded probe의 권한 실행으로 분리했다.
- 8500 read-only host attestation은 정상 사용자·backend cwd·uvicorn command와 real-model health를 확인했지만, 기존 OpenAPI 16 paths에는 새 observations/night previous/rule preview가 없었다. 이는 테스트 항목 수나 API 통합 통과로 합산하지 않는다.

## 아직 측정하지 않은 것

- RM1 해결과 Gemini 전체 corpus 의미 정확도 검증
- 테스터 2번 시작 예정: 다른 PC에서 “테스터 2 시작” 지시 뒤 실제 접속 URL·backend health 확인, 사용자의 새 게임 시작 시 attempt_id·시작 시각 기록, 5회차 완료 뒤 읽기 전용 로그 대조. 이 PC에서는 문서 정리만 하며 사람 표본은 아직 없다.
- `gemini-2.5-pro` generation404는 이전 연결 시도 이력이다. 사용자가 선택한 현재 core는 Gemini 3 Flash이며 Pro·Flash Lite가 아니다. 단일 호출 성공과 로컬 health 확인을 전체 의미 승인으로 해석하지 않는다.
- 테스터1 재플레이, 정답을 모르는 새 참가자, 약50%·집중70% 목표
- 질문·추천·규칙·이미지의 사람 체감 효용과 인과적 개선 효과
- 보존되지 않은 모든 중간 명령의 정확한 총 실행 횟수
