# 연결된 추리 통합 검증 계획

날짜: 2026-09-09  
담당: `/root/integration`  
상태: 준비 완료, 구현 안정화와 `pigfarm_test` 백엔드 인계 대기

## 목적과 통과 기준

승인 명세의 `관찰 → 노트 → 질문 → 규칙 → 실제 기회/결과 → 다음 답안 → 회고` 연결을 실제 HTTP 응답과 실제 프론트 화면에서 함께 확인한다. 생성 이미지의 품질 통과와 런타임 공개 조건 통과를 별도 판정한다. 자동 검증 기록은 사람의 첫 플레이 결과로 부르지 않는다.

통합 통과에는 다음 근거가 모두 필요하다.

1. backend 담당 launcher가 URL과 SQL `current_database()`를 각각 `pigfarm_test`로 검사하고 fake LLM·별도 포트로 기동했다는 비밀 없는 attestation
2. 실제 API로 새 테스트 판을 만들고 5회차를 완주한 원문 응답 기록
3. 실제 frontend 3500이 그 API를 소비한 390px·desktop 브라우저 화면과 네트워크 기록
4. 0/100점 양쪽의 결말→회고 불변 조건을 모의 API 브라우저 회귀로 확인한 결과
5. 독립 사람이 질문 관련성·규칙 의미·검사 정확성을 검토하기 전에는 해당 지표가 N/A인 결과
6. 실제 Ollama 표본은 별도 backend 소유 실행으로 남기고 fake 결과와 섞지 않은 보고서

## 실행 격리

- backend DB 실행·초기화·테스트·서버 기동은 backend 담당자만 한다. 운영 `pigfarm` DB를 reset, migrate, truncate, regrade하지 않는다.
- 통합 담당자는 launcher가 URL DB 이름과 SQL `current_database()`를 모두 `pigfarm_test`로, NPC/core provider를 fake로 검사한 뒤 쓴 secret-free attestation을 live `/health`와 대조한 뒤에만 harness를 실행한다. exec PID namespace가 분리되어 `/proc`는 증거로 사용하지 않는다. 연결 문자열과 비밀은 결과에 출력하지 않는다.
- frontend 3500 서버는 기존 담당 프로세스를 유지한다. 종료·재시작·환경 변경을 하지 않는다. 브라우저의 8500 API 요청만 Playwright에서 인계받은 별도 backend 포트(기본 8501)로 전달한다.
- `/tmp/pigfarm-connected-integration/`의 harness는 DB 생성·삭제·migration·server launch 명령을 포함하지 않는다.
- 테스트가 만든 attempt ID는 `integration_automation`으로 별도 목록화한다. 기존 사용자 판 `b56dca9d-8b01-4fe7-9b52-4afabb80e3f7`과 점수는 읽거나 바꾸지 않는다.

## producer/consumer 경계

| 경계 | backend producer가 보장할 것 | frontend consumer가 보장할 것 | 통합 판정 |
|---|---|---|---|
| 공개 관찰 | 장면·이미지·발언·규칙 결과마다 안정된 `observation_id`, 출처 종류, observed/reported, 실제 공개된 이미지 | 관찰 ID를 유지하고 출처/발언 상태를 표시하며 숨은 사실을 보충하지 않음 | 응답→노트→원본 카드의 ID·문구·이미지 동일성 |
| 관찰 조회 | 현재 loop까지 공개된 관찰만 반환, 조회는 예산 불변 | 낮 노트/밤 갤러리 열람이 발화·비트를 쓰지 않음 | 조회 전후 budget/beat와 화면 표시 비교 |
| 이전 답안 | 직전 제출의 최종 편집 claims를 `draft_text`로, 당시 전체 선택 ID를 반환 | 3회차 이후에도 초안과 선택을 복원; 토글은 첨부만 바꾸고 prose를 바꾸지 않음 | loop 1 편집→loop 2 토글→loop 3 payload/화면 추적 |
| 질문 | public observation만 근거로 supported/contradicted/unknown, 무관한 근거 금지, unknown은 확인 노트 없음 | 상태·근거·다음 관찰을 그대로 표시 | 테스터1 원문 12문항의 사람이 검토 가능한 원문 기록 |
| 추천 | 0–3개; target/action/effect/when/reason/evidence/expected observation 완비 | 후보 수를 채우지 않고 전 필드를 표시 | 각 후보 근거 ID 존재와 행동/이유/확인 UI 확인 |
| 직접 규칙 | exact custom text에 묶인 성공 preview만 apply; 미지원 의도는 제한·대안, 조용한 치환 금지 | 원문/의미/제한/충돌을 먼저 표시하고 별도 apply 클릭 | preview만으로 다음 loop 불가, 변조 text 거부, 명시 적용 뒤에만 진행 |
| 실행 결과 | 실제 scene opportunity에만 obeyed/violated/conflict/not_evaluable 기록, rule observation 연결 | 실제 변화와 규칙을 표시하고 등록을 성공으로 세지 않음 | 억제 시 내레이션·이미지 동시 억제, 기회 없음은 분모 0 |
| 원숭이손 | 이득과 실제 발생 가능한 비용이 같은 규칙/기회에 연결됨 | 제안 이유와 이후 aftermath/회고를 원인 단정 없이 표시 | 수락 전후 budget·execution·side_effect 관찰 |
| 회고/지표 | experiments와 metrics의 분자·분모·방법·검토수, nullable call coverage | 의도→해석→기회→실제 행동→검사 결과 순서와 N/A 표시 | API 원문과 회고 화면 수치/문구 대조 |

## 시나리오 A — fake API 5회차

실행 파일: `/tmp/pigfarm-connected-integration/api-live-flow.mjs` (준비 골격). 결과 디렉터리는 실행 때 새 timestamp 경로를 사용한다.

1. 격리 사전검사 후 `/health`가 scenario `a`, harness `on`, DB `ok`, 두 LLM provider `fake`임을 확인한다.
2. 새 session을 만든다. loop 1 전에 harness가 403인지 확인한다.
3. 매 loop의 1~6 beat를 순서대로 수집한다. 관찰 ID 중복, 미래 loop, 숨은 정답 문구, 현재 없는 인물 재등장, `day_done` 뒤 이미지가 없는지 확인한다.
4. 관찰 GET과 notes GET 전후에 발화 예산·beat가 변하지 않는지 다음 응답과 대조한다. 모든 신규 note는 원본 observation ID와 source를 가지며, 같은 ID의 text/scene/image가 일치해야 한다.
5. loop 1의 최종 확인 화면에서 원래 초안을 다른 문장으로 편집해 제출한다. loop 2에서 최종 편집본과 이전 선택 ID가 복원되는지 확인한다. loop 2에서 기존 근거 하나를 해제하고 새 근거 하나를 선택하되 prose는 유지한다. loop 3에서 loop 2의 최종 prose와 최종 선택 ID가 복원되고, 이전 근거 문장이 중복 append되지 않는지 확인한다.
6. 1–4회차는 점수와 무관하게 `is_final=false`, `intervention_available=true`, `cells=null`, `ending_lines=null`; 5회차만 종료한다.
7. 각 intervention에서 테스터1 질문을 원문 그대로 최대 3개씩 사용한다. 자동 단정은 하지 않고 answer/status/detail/evidence/next_observation을 저장해 후속 사람 검토 표를 만든다.
8. 규칙 단계에서 known-source 직접 규칙 `은상은 소문의 알려진 출처를 밝힌다`를 preview한다. preview 직후 rule 목록과 다음 loop가 변하지 않아야 한다. exact text/preview ID 적용만 성공해야 한다. `은상은 소문의 진실을 무조건 나에게 이야기 해준다.`는 executable=false이거나 미지원 한계를 명시하고 대안을 제시해야 하며 자동 적용하면 실패다.
9. 추천 후보는 0–3개를 허용한다. 각 후보의 target/action/reason/expected_observation/evidence_ids가 완전하고 evidence ID가 공개 관찰에 실제 존재해야 한다.
10. 한 회차에는 원숭이손을 수락해 설명 이득과 조건 충족 시 실제 발화 budget 비용, 다음 아침 aftermath, 회고 side effect를 같은 rule/opportunity로 연결한다. 오퍼가 없으면 그 실행의 원숭이손 항목은 N/A이며 실패로 세지 않는다.
11. 5회차 종료 뒤 6회차 409, harness 200, retry attempt_n=2 및 prior cells를 확인한다. fake 완주의 실제 점수는 관찰값으로 기록하며 특정 점수를 강제하지 않는다.

테스터1 질문 원문:

1. `채연말고 밥을 남긴 사람은 누구야?`
2. `준은 어떤 역할이야?`
3. `민석은 누구에게 보고하는거야?`
4. `채연 말고 추가로 배급을 남긴 사람`
5. `호송 당한 사람은 누구야?`
6. `열이나면 죽나?`
7. `이송된 충식은 돌아오는가?`
8. `귀표는 무엇인가?`
9. `건강검진 후 이상이 있는 경우 어떻게 되는가?`
10. `축산 트럭의 정체는?`
11. `손목띠와 귀표는 무슨 관계야?`
12. `너에게 물어볼 수 있는건 뭐야?`

사람 검토 기준은 “질문이 요구한 대상/관계/정의를 detail이 실제로 다루는가”, “각 evidence가 detail을 직접 지지하는가”, “reported 내용을 세계 진실로 승격하지 않았는가”, “unknown을 사건 부정으로 표현하지 않았는가”, “next_observation이 이미 공개됐고 실제 가능한 행동인가”다. old answer label과 단순 일치 여부로 통과시키지 않는다.

## 시나리오 B — 이미지 공개와 억제

생성 asset QA는 [image-review.md](image-review.md)의 통과 판정을 재사용한다. 아래는 별도 runtime gate다.

| ID | runtime 통과 조건 | 즉시 실패 조건 |
|---|---|---|
| clue-07 | loop 1 beat 1에만, 채연·민석·은상·준이 모두 현재 roster에 있을 때 방송/배급 서술과 함께 공개 | loop 2–5 자동 재사용, 소거 인물 재등장, 관리자 신체/정체 주장 |
| clue-08 | beat 3, 민석 기록 action 실행, 채연 present | 기록 suppress인데 노출, 노트 내용·질병·보고 동기를 caption이 확정 |
| clue-09 | beat 5, 민석이 닫힌 방송실 문에 접근 action 실행 | 입실·보고 전달·수신자·보고 완료로 표현 |
| clue-10 | beat 2/5, 은상 소문 action과 익명 청자 존재; 이동은 narration, actual rumor content는 statement로 보완 | 그림만으로 출처/진위/이동 전후를 확정, action suppress인데 노출 |
| clue-11 | beat 2, 준 present, 손목띠 관찰 action 실행 | 정확한 숫자·동물/귀표 정체를 확정, action suppress인데 노출 |
| clue-12 | beat 4, 담당자가 이동하고 채연이 자기 자리에서 대기하며 checkup action 실행 | 채연이 이동, 접촉·검사 완료·정상/질병 진단, 금지/대체 장면 노출 |

모든 이미지 observation은 동일 caption/scene으로 노트와 갤러리에 재현한다. 이미지 자체에 없는 사실은 narration/statement provenance 없이는 확인 근거가 될 수 없다. clue-08 소매 띠 좌우와 clue-10 이동 순서는 기존 경미 지적으로 유지하며 추리 정답에 쓰지 않는다.

## 시나리오 C — 실제 frontend 3500 + isolated API

실행 파일: `/tmp/pigfarm-connected-integration/browser-live-observe.cjs` (준비 골격). Playwright는 `/tmp/pigfarm-image-browser/node_modules`, Chrome은 `/usr/bin/google-chrome`을 사용한다. 브라우저가 8500으로 보내는 요청을 backend 담당자가 인계한 8501로 route한다.

- 390×844와 1440×1000에서 가로 overflow, page errors, failed requests를 기록한다.
- 낮 노트를 열고 닫는 동안 발화 표기가 유지되고, observation card의 출처/scene/original reopen이 동작하는지 본다.
- 인물 선택 portrait가 E01/E04/E07/E10으로 고정됐는지 확인한다.
- 밤 갤러리에는 실제 네트워크로 이미 받은 observation image만 보이고 미래/억제/closure 이미지가 없는지 확인한다.
- loop 2와 3의 이전 최종 편집 초안, 기존 선택, 해제/추가 payload(`tapped_note_ids` full current, `inherited_note_ids` original restored)를 네트워크 요청과 화면에서 함께 확인한다.
- 질문 status/evidence/next path, 후보 action/reason/expected observation, custom preview 원문/의미/제한과 explicit apply를 캡처한다.
- 마지막 밤에는 이야기 결말이 회고보다 먼저 보이고, 회고에서 실제 experiment chain과 N/A가 나타나는지 확인한다.
- desktop은 같은 핵심 화면의 레이아웃과 gallery/replay를 확인한다. 모바일만 통과한 결과로 desktop을 추정하지 않는다.

## 시나리오 D — deterministic 0/100 UI 불변식

`frontend/tests/five-loop-flow.cjs`를 현재 구현에 맞춰 실행한다. 모의 API를 쓰므로 실제 DB/모델 통합 증거로 합산하지 않는다.

- 1–4회차 100점도 다음 intervention으로 진행한다.
- 최종 0점과 100점 모두 이야기 결말→회고 순서, harness fetch/retry, 새 attempt를 제공한다.
- 이해도와 세계 outcome을 섞지 않고, side effect를 채점 셀로 표시하지 않는다.
- `frontend/tests/connected-investigation.cjs`로 null/empty/N/A, unseen image, previous draft, grounded status, preview/apply UI를 별도 확인한다.

## 시나리오 E — 실제 Ollama 제한 표본

backend 담당자가 별도 `pigfarm_test` app/test 실행에서 provider와 PID를 검증한 뒤 수행한다. fake 결과와 별도 파일로 저장한다. 전체 5회차 점수를 목표로 하지 않고 다음 표본만 본다.

- 위 12개 테스터1 질문: 특히 남은 쟁반, 보고 수신자, 귀표 정의의 무관 confirmation/사건 부정 회귀
- 직접 규칙 3개: `민석이 내 질문에 자세하게 답할 수 있도록 한다.`, `채연은 묻는말에 자세하게 대답한다.`, `은상은 소문의 진실을 무조건 나에게 이야기 해준다.`
- 통과: 답한다를 질문한다로, 진실 공개를 소문 생성으로 조용히 치환하지 않음. 지원 범위면 본인이 아는 관찰 설명으로 정확히 preview하고, 미지원이면 executable=false + 한계/대안을 반환. 대안은 새 preview와 명시 apply 없이는 적용되지 않음.
- 모델 출력은 사람이 evidence/semantic 표본으로 검토한다. 같은 모델 자기평가로 `question_grounding`, `custom_semantics`, `checker_accuracy`를 채우지 않는다.

## 회고와 측정 판정

- 모든 Metric에 `denominator`, `reviewed`, `method`가 있다.
- 분모 0은 `numerator=null`, `value=null`이며 UI는 N/A다.
- `rule_success_rate`는 evaluable opportunity만 분모로 삼으며 기회가 없으면 null이다.
- 새 완전 로그는 `measurement_version`, `model_call_coverage=complete_logged_calls`, nullable이 아닌 model_calls/model_attempts를 가진다. legacy 불완전 로그는 두 수가 null이고 coverage가 `legacy_partial_or_unavailable`이다.
- `harness_interventions <= model_calls <= model_attempts`; interventions는 위반/폴백 호출 수이고 성공률이 아니다.
- 원숭이손 비용은 해당 experiment opportunity의 side_effect와 observation으로 연결될 때만 그 원숭이손 결과로 설명한다. 일반 tool side effect를 원숭이손 인과로 합산하지 않는다.

## 문서 불일치와 최종 정리

현재 [승인 명세](../../superpowers/specs/2026-09-09-connected-investigation-design.md)에는 검증 후 고쳐야 할 문구가 있다.

- 5행: 상태가 `이미지 구성 추가 브레인스토밍 / 구현 전`
- 9행: 이미지 구성 논의안을 “먼저 확정”하고 E03 단독 교체를 보완한다고 서술
- 18, 98, 132행: E03 단독 교체를 범위/완료 조건으로 유지
- 136행: 이미지 구성이 “추가 논의 중”이라고 서술

최종 검증 뒤에는 이를 승인된 A안, 즉 E01/E04/E07/E10 고정 초상 + clue-07…12 사건 6장 + 실제 관찰만 담은 낮 노트/밤 갤러리로 갱신한다. E03은 삭제/재제작하지 않으며 상태 초상 선택에 쓰지 않는다는 점을 명시한다.

[HANDOFF.md](../../HANDOFF.md)는 실제 명령, exit code, API attempt ID, artifact 경로, fake/real 모델 구분, 실패와 한계, 남은 사람 검증을 반영해 다시 쓴다. 사람의 새 first-play 약 50%/집중 약 70%, 관리자 회상, 이미지 이해 개선과 인과 효과는 자동 통합 결과로 완료 처리하지 않는다.

## 최종 산출물

- 이 계획
- `/tmp/pigfarm-connected-integration/` harness와 실행별 timestamp artifact
- `docs/review-verification/2026-09-09-connected-implementation/integration-report.md`: 명령, 환경 증거(비밀 제외), 응답/화면 artifact, assertion별 pass/fail, 정확한 실패, 제한
- 승인 명세 상태/이미지 범위 정정
- `docs/HANDOFF.md` 최종 실행과 남은 사용자 검증 정리
