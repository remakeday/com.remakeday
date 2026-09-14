# 수정본 플레이 기록 — 테스터2

상태: **접속 URL·backend health 확인 완료 — 사용자의 새 게임 시작 대기 / 실제 사용자 표본 미수집**

- 참가자 ID: 테스터2 (사용자 지정)
- 일반·집중 조건: 미수집
- 첫 플레이 여부 / 사전 정답 노출 여부: 미수집 / 미수집
- attempt_id: 미수집
- 실제 접속 URL·연결된 backend health: `http://localhost:3500/play` HTTP200 / 연결 backend `http://127.0.0.1:8500` health `db: ok`, core `gemini:gemini-3-flash-preview`, NPC `ollama:exaone3.5:7.8b`, embedding `gemini` (2026-09-09 17:28:59 KST 확인)
- 기기·화면 크기: 미수집
- 시작·종료 시각: 미수집
- 완주 여부: 미수집

이 PC에서는 문서 정리만 마친다. 사용자가 HANDOFF를 다른 PC의 에이전트에게 전달하고 **“테스터 2 시작”**이라고 지시하면, 그 에이전트는 실제 게임 접속 URL과 연결된 backend health를 먼저 확인한다. 다른 PC가 서버를 호스팅한다고 가정하지 않으며 이 PC의 localhost 주소를 원격 접속 주소로 사용하지 않는다. 확인된 URL에서 사용자가 새 게임을 시작할 때 새 attempt_id·시작 시각을 기록하고 5회차까지 플레이한다. 완료 뒤 “테스터2 완료”라고 알리면 attempt_id와 인스펙터·DB 로그를 읽기 전용으로 대조한다. 테스터1의 기존 판 `b56dca9d-8b01-4fe7-9b52-4afabb80e3f7`과 최종 DB47.9점은 변경하지 않는다.

core 기본 모델은 사용자가 선택한 `gemini-3-flash-preview`이며 NPC는 local Exaone, embedding은 기존 Gemini를 유지한다. Gemini adapter에는 process-wide 10 RPM pacing이 적용된다. 2026-09-09 17:15:54 KST **이 PC 로컬** backend health는 core `gemini:gemini-3-flash-preview`, NPC `ollama:exaone3.5:7.8b`, embedding `gemini`, DB `ok`였고 `http://localhost:3500/play`은 HTTP200이었다. 다른 PC의 접속·health는 시작 지시 뒤 별도로 확인한다. 실제 제품 adapter 단일 structured 호출은 2.543초에 기대 답 `no`를 반환했지만 전체 corpus 의미 정확도는 미검증이다.

## 시작 전 접속 확인 (2026-09-09 17:28:59 KST)

- 이 지시는 별도 PC가 아니라 기존 작업 PC(`kimchungsik`, `/home/kimchungsik/projects/com.remakeday`)에서 받았다. 기동해 둔 frontend·backend 프로세스가 그대로 살아 있어 같은 환경에서 확인했다.
- 플레이 URL: `http://localhost:3500/play` — HTTP 200.
- 그 URL이 사용하는 API base는 `frontend/.env.local`의 `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8500`이며, 해당 backend `/health`는 `{"scenario":"a","harness":"on","models":{"npc":"ollama:exaone3.5:7.8b","core":"gemini:gemini-3-flash-preview","embedding":"gemini"},"db":"ok"}`였다. `Origin: http://localhost:3500` 요청에 CORS 허용 헤더가 돌아왔다.
- backend 8500과 DB 5435는 `127.0.0.1`에만 바인딩돼 있다. **브라우저는 이 PC에서 열어야 한다.** 다른 기기에서 `http://<이 PC IP>:3500`으로 열면 화면은 떠도 API 호출이 실패한다.
- 시작 전 DB 기준선(읽기 전용): `attempts` 73건, 가장 최근 생성 `39bcb2c4-314b-4a3d-8059-0e81015f6045` (2026-09-09 08:17:29 UTC = 17:17:29 KST, 이전 세션의 기술 점검 판이며 사람 표본 아님). 이 시각 이후 새로 생성되는 attempt를 테스터2 판으로 식별한다.
- 아직 새 게임을 시작하지 않았다. attempt_id·시작 시각·회차 점수는 여전히 미수집이다. 확인 과정에서 판·회차·노트를 새로 만들지 않았고 테스터1 판 `b56dca9d-8b01-4fe7-9b52-4afabb80e3f7`은 그대로다.

| 회차 | 이해도(0~100) | 막힌 장면·조작 | 제공한 도움·오류·대기 |
|---|---:|---|---|
| 1 | 미수집 | | |
| 2 | 미수집 | | |
| 3 | 미수집 | | |
| 4 | 미수집 | | |
| 5 | 미수집 | | |

## 결말 공개 전 기록

- 이해한 상황과 근거(원문): 미수집
- 기억에 남은 장면·대화·노트(원문): 미수집
- 이해되지 않은 점과 불편한 조작(원문): 미수집
- 질문·추천 규칙·직접 규칙·이전 답안·이미지·원숭이손·회고 중 도움이 된 것과 따로 논 것: 미수집
- 출처 누락, 부정 질문 오답, 이유·조건의 과도한 확정: 미수집

## 완료 뒤 읽기 전용 대조

- 판 식별: `POST /sessions` 응답의 attempt_id 또는 인스펙터 URL의 ID를 기록한다.
- 인스펙터: 확인된 게임 URL과 같은 origin의 `/inspector/{attempt_id}`. 토큰이나 비밀값은 기록 파일에 복사하지 않는다.
- 회차별 최종 편집 답안·선택 근거, 노트의 observation ID, 질문과 source ID, 추천·직접 규칙 preview와 실제 실행, 원숭이손 대가, 본 이미지 gallery, 최종 회고 지표를 연결해 확인한다.
- 실제 플레이 판만 사람 표본으로 센다. 서버 smoke, 자동 브라우저, fake API 판은 제외한다.
- 로그 대조 중에도 DB reset, 기존 판 재채점, 운영 기록 수정은 하지 않는다.

## 알려진 기술 경계

- 최종 backend 자동 suite는 327 passed, 기존 경고3건(6.86초)이지만 실제 Ollama RM1 의미 gate는 통과하지 못했다.
- 명시적 반대 사실, 이유, 조건 질문이 잘못 확정될 수 있다. 화면에서 보이면 질문과 답 원문을 그대로 보존한다.
- 한 명의 결과나 한 점수로 약50%·집중70% 목표 달성을 확정하지 않는다.
