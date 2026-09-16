# 작업 이어하기 — 2026-09-16

> 이 문서 하나만 읽어도 이어서 작업할 수 있게 쓴다. **작업 브랜치는 `feat/coherence-chain`**(main보다 `7af14dd` WIP 1개 앞). 귀가 후 시작점은 아래 "지금 바로 할 일" 1번.
> 이전 인계(NPC 대화 개선 시점)는 `HANDOFF.md`(2026-09-15)에 그대로 있다.

## 현재 상태 — 테스터6 휴먼테스트와 개연성 설계

테스터6이 5회차를 완주했다(판 `2338ec9f`, 09:48~11:06, 8.8 → 64.2 → 94.2 ×3, 부작용 셀 0). 피드백 11건은 `review-verification/2026-09-16-tester6/tester6.md`에 원문·DB 대조·분류로 있다. 같은 날 다른 세션이 테스터7 기록(`review-verification/2026-09-16-tester7/`)을 따로 진행한다 — 서로 건드리지 않는다.

**즉시 수정 5건은 반영·커밋 완료.** F1 인물 대사 음원 보류(관리자·조언자·회고만 재생), F3 밤 근거 목록 "맨 위로" 고정 버튼, F4 신의 질문 답변 로그 높이 상한 제거, F5 규칙 없이 이미 하는 행동은 추천 규칙에서 제외, F6 관찰 기록·근거 목록의 회차 간 중복 문장 숨김. 검증: backend **462 passed** · tsc · 헤드리스 UI 7종 통과. 부수로 OAuth `credentials: "include"` 이후 깨져 있던 UI 테스트의 모의 CORS 헤더와 ToggleSwitch 셀렉터를 맞췄다.

**자산 제작·등록 (2026-09-16 오후)** — 밤 단서 P01~P05(9:16)와 원숭이손 삽화 Q02~Q08(3:2)을 사용자가 생성, 관리자 밤 방송 MA08~12 녹음 완료. 검수: P군 5장 전부 통과, Q군 6장 통과, Q04는 v1 보류(손잡이 허리 높이) 후 **v2 재생성 통과**(손잡이 문 상단). 통과분은 `frontend/public/assets/`(P), `assets/clues/`(Q), `audio/voice/`(MA08~12)에 복사하고 `voiceMap.ts`에 등록(대사 음원 34개). 음성은 형식·길이 확인 + 사용자 청취 검수 완료. 코드 참조(imageMap·DoomTransition)는 아직 없음 — Codex 브리프(P.6)로 구현 예정. 기록: `output/imagegen/P-v2-Q-v1-production.md`.
부수 수정: `VoicePlayer.tsx` BGM 페이드의 rAF 타임스탬프 음수 진행률로 볼륨이 0.25를 넘던 결함을 진행률 0 고정으로 수정(voice-playback 테스트가 재현 가능하게 실패하던 원인). 테스트 기대 수 29→34.

**인게임 확인 (2026-09-16 14:30)** — 헤드리스 UI 7종 전부 통과(gameplay-clarity·npc-followup·connected-investigation·five-loop-flow·voice-transitions·scene-illustrations·voice-playback). 실서버(8500·pigfarm DB) 셀프플레이 1회차 완주(판 `dfb1e585`, 플레이어 모델 kanana 상주 재사용, 69.8s): 발화 3·원숭이손 수락·밤 제출·신의 질문·규칙 적용까지 크래시 0, 하네스 재생성 0, 폴백 0. **F5 실동작 확인** — 채연이 규칙 없이 배급을 남긴 뒤 추천 규칙에 "채연: 배급을 남긴다"가 나오지 않음(옵션: 준 설명·은상 설명·은상 출처). 테스트 수정 2건: voice-playback 기대 수 34, connected-investigation의 근거 그림 크기 검사는 로드 완료를 기다린 뒤 검사(4MB 삽화 타이밍 실패 재현 2회 → 수정 후 통과).

**F8 밤 단서 시퀀스 — 구현 완료 (서브에이전트, 2026-09-16 14:40)** — 단서 표는 시나리오 `NightClueDTO` 5행이 단일 출처, `POST /nights/{id}/submit` 응답에 `night_clue {loop_n, caption, image_ids, voice_id, broadcast, outcome_line}`. 밤에 캡션(observed·scene)과 방송(reported·statement)을 「N회차 · 소등 후」 관찰·노트로 저장, 낮 노트의 고아 파편 5개 제거(배우 있는 진술·트럭 파편·7시 13분은 유지). `DoomTransition`: 결말 이미지 → 0.8s 방송 → 음원 50% 지점 치지직 1s(글로벌 CSS `.cookie-glitch` 재사용, 띠 3개, 2회차는 두 번) → 캡션 잔류 → 「계속」 탭(자동 진행 제거). 음원 실패 시 결말별 MA03/04/05 대체, 폐쇄는 MA06 이어 재생. 검증: backend **475 passed**(신규 13) · tsc · 헤드리스 6종 통과. 2회차 캡션은 방송과 중복되지 않게 "트럭 소리."로 정리(P.1). 부수: `test_e2e_flow`가 인스펙터 토큰을 하드코딩해 `.env` 토큰 교체 뒤 깨졌던 것을 설정값 참조로 수정.

**환경 변경 감지(이 세션 외부, 14:25)**: `backend/.env`의 `GOOGLE_OAUTH_REDIRECT_URI`·`FRONTEND_BASE_URL`이 `https://api.remakeday.com`·`https://remakeday.com`으로, `INSPECTOR_TOKEN` 교체, `NPC_LLM_MODEL=kanana1.5:8b-q4km`(HANDOFF 정본은 gemma4:12b). 백업 `.env.bak.20260916`. 로컬 OAuth 로그인은 이 값으로는 localhost에서 동작하지 않는다 — 배포 세션의 의도인지 확인 필요.

**서버**: 개발 계정 로그인 머지(`be42385`) 이후 백엔드·프런트 재기동 완료(20:39~21:01, `dev-login.cjs` PASS 확인). 이후 Anthropic·Gemini 평가 동안 `USER_DAILY_ATTEMPTS`를 테스트용으로 임시 상향했다 — **컨트롤러가 오늘 밤 이 상향값을 되돌리며 백엔드를 재기동한다**(아래 "남은 것" ③). 재기동 뒤에는 개발 로그인으로 `/play` → 판 생성 200을 다시 확인할 것.

## 과잉 사용 방지 허들 — main 머지 완료 (18:12, `8137acf`)

commits `c16a975`(attempts.user_id·설정 5종) → `177cb9a`(require_user·ip_bucket·client_ip·GuardEvent) → `b95d5d2`(프론트 GuardScreen) → `a6ccefc`(라우터 배선·판 생성 하루 5판·전역 정원·텍스트 200자) → `ad136b2`(opus 최종 리뷰 반영: free_text 2000·claims 8×500·custom_text 200 상한, 413 미들웨어, 버킷 sub 키·TRUST_PROXY, TOCTOU 재집계, SESSION_SECRET 기동 검사) → `8137acf`(GuardScreen 전 phase 게이트, custom_text 테스트). 최종 574 passed · tsc · guard.cjs·gameplay-clarity 통과. 프런트: 401/403/429/503은 `GuardScreen`으로 대체, 422는 "입력이 너무 길거나 형식이 맞지 않는다". 계약: `docs/spec/api_contract.md`의 "과잉 사용 방지 허들" 절(401/403/429/503 본문, 200자 422, 가드 매트릭스). 러너: `backend/scripts/run_selfplay.py --session-cookie`로 `rd_session` 쿠키를 직접 넘길 수 있고, 쿠키 없이 401을 받으면 안내 메시지를 내고 종료한다.

운영 메모:
- **로컬 개발·러너**: `backend/.env`에 `GUARD_AUTH=off`(기본값은 `on`)를 설정해 로그인 없이 사용. `run_selfplay.py` 등 러너는 이 값을 그대로 쓰거나 `--session-cookie`로 실제 로그인 세션을 넘긴다.
- **프로덕션**: `GUARD_AUTH=on` 유지 + Cloudflare 레이트 리밋(엔진 앞단) + Anthropic 콘솔 지출 한도로 이중 방어. 속도 제한 버킷(`IP_SESSIONS_PER_MINUTE`/`IP_ACTIONS_PER_MINUTE`)과 하루 한도(`USER_DAILY_ATTEMPTS`/`DAILY_ATTEMPT_CAP`)는 애플리케이션 레벨 방어선이며 Cloudflare가 앞단 방어선이다.
- **속도 제한 버킷은 프로세스 메모리에 산다** — uvicorn을 여러 워커로 띄우면 워커마다 별도 버킷이라 실제 한도가 워커 수만큼 늘어난다. 단일 워커로 운영하거나, 버킷 대신 Cloudflare 레이트 리밋을 사실상의 권위로 삼는다.
- **`SESSION_SECRET`는 프로덕션에서 반드시 설정해야 한다** — `GUARD_AUTH=on`인데 기본값(`dev-session-secret-change-me`)이면 `main.py`의 lifespan이 기동 시점에 `RuntimeError`를 낸다(의도된 실패 — 기본 시크릿으로 세션을 서명하지 않게 막는다).
- `users` 행을 지우는 것만으로는 그 사용자를 막지 못한다 — `attempts.user_id`가 FK 없이 sub 매칭이라 재로그인하면 새 `users` 행이 생겨 계속 판을 만들 수 있다(후속 과제: `users.blocked_at` 컬럼 + `require_user`에서 확인).
- alembic head는 `fbec9419f894`(`attempts_user_id`) — 개발 DB에는 세션 주인이 이미 적용함. 새 환경에서는 배포마다 `alembic upgrade head` 필요.

## 설계 방향 — 기획서 v8.1 원설계로 복귀 (브레인스토밍 대조 결과, 2026-09-16 오후)

브레인스토밍 중간안(조언자 계시·원숭이손 UI 이상화·관리자 노출 서사)은 기획서 5.5·5.6·5.7·A.3과 대조해 폐기했다. 남긴 것만 적는다.

| 항목 | 기획서 근거 | 채택 | 폐기 |
|---|---|---|---|
| F2 무의미 입력 | 규정 없음(5.1 발화=자원) | 규칙 게이트(한글 음절 없음·같은 글자 3회 반복·문장부호만) → 인물별 `fallback_lines` 즉답 · 분류기(gemma4 경량 판정: 질문·부탁·잡담·무의미) · 같은 장면 첫 1회 예산 면제 | — |
| F7 신의 질문 | 5.5 답은 맞다·틀리다·없었다·알 수 없다 / "맞다"는 노트 확인 표시 · 5.6 조언자는 로그만 안다 | ① 질문 전에 답 네 형식 안내(사실 질문이 보상받는 구조를 가르침) ② 조언 한 줄은 **세계 구조**(잠재 행동·인물 지식)에서만: "네 기록의 「…」. 내일 준에게 …을 물어봐라" ③ 닻(기록)→행동(질문/규칙)→보상(새 관찰) 사슬이 끊기면 조언 없음 ④ "확인했다"는 근거 ID 있을 때만 | 가설 판정(그렇다/아니다), 시나리오 조각 계시, **현재 리드 표의 사실 공개 문장("한 가지 더 — …")** — 개선 배치 때 들어온 5.6 이탈이며 무맥락의 근원 |
| F8 고아 단서 | A.3 파편은 "멸망" 순간 배치 · 4.9 파편은 확인 불가 · A.5 치지직 | **확정(2026-09-16 오후)**: 낮 노트에서 빼고 밤 결말 전환 안에서 **쿠키 문법(치지직 1초 + 단서 문장 + 관리자 음성 MA03/04/05)**으로 하루 하나. 코드 타임라인, mp4 아님. 정본 `REMAKE_DAY_이미지제작서_밤단서_v2.md`(P01~P05 근접 재생성, v1 문서는 삭제). 조언은 파편의 뜻을 풀지 않음 | v1의 원거리 정물 4장, 파편을 인물 발화에 녹이기 |
| F10 관리자 | 8.3 뒤에 숨은 인지자 · 4.8③ 손상 2층=관리자 손자국 | 현행 유지(기억 삭제·계획 수정) | — |
| F11 원숭이손 | 5.7 관리자 층 생성 "원할 법한 규칙+숨은 부작용 1" · 1회차 무조건, 2회차+ 전날 40%↑ 1회, 판당 2 · 부작용은 세계 인과, 규칙 누적 · 7.3 부작용 주장은 규칙 로그 자동 생성 | 5.7 표 4종(검진 회피·침묵·방송 차단·잠들기)을 **시나리오 분기**로 작성(소원 직후 비트에 뒤따르는 분기 1개) · 미연결 `make_paw` 연결 · 예산 감소 대가 제거 · 두 번째 원숭이손은 **빈 칸 겨냥** 미끼 · 거절은 무비용, 2회 연속 거절 시 그 판 종료 | 대화 통로·시간 도둑·판 밀림, 관리자 노출 서사, "그 회차 한정"(5.5·5.7 충돌, 구현도 지속형) |

두 번째 출현 조건은 **40%로 확정**(2026-09-16). 부작용 분기의 구체 내용은 시나리오 작성 사안.

F8 재검토 메모(2026-09-16 오후): 생성한 P01~P04(`output/imagegen/img_P0*_night_*.png`)가 단서로 읽히지 않는 이유 — ①차이(이상한 점)가 없는 정물 ②감각 캡션(냄새·차다·소리)은 그릴 수 없어 그림과 글이 분리 ③P02·P04가 같은 복도 설정 샷(제작서의 "원거리" 규칙이 원인) ④크기 기준 없음 ⑤1인칭 닻 없음. 대안: 근접·피사체 하나·내 침상 가장자리 포함·캡션은 보이는 흔적만 / 또는 낮 장면(C군)을 밤에 변형해 다시 보여주기. 사용자가 다시 생각하기로 함.

F7 답변이 답변 같지 않았던 이유(테스터6 15문답): 판정 0회(전부 알 수 없다), 이미 본 기록 되돌려주기, 합니다체+명령체 혼용, 면책 문장+무관 리드. 설계 문서 §2에 반영.

## 현재 구현이 기획서에서 벗어난 지점 (이번에 확인)

- 리드 표(`adapter.py` ~507)가 미관찰 사실을 조언자 답변에 붙인다 → 5.6 이탈
- 파편(`adapter.py` ~539)이 낮 비트 노트로 떨어진다 → A.3 이탈
- 원숭이손이 "설명 강제" 1종 + 발화 예산 -1 → 5.7 표 미구현, `make_paw` 미연결, 부작용 칸에 쓸 사건이 생기지 않음(테스터6 부작용 0점의 원인)
- 규칙은 판 단위로 지속되며 장면 행동의 분기(평소·억제·설명)와 잠재 행동을 고른다. 행동 하나가 바뀐 뒤의 **연쇄 분기는 없다** — 부작용 사슬 작성이 핵심 작업

## 지금 바로 할 일 (귀가 후 이어서 — 우선순위 순, 2026-09-16 18:30 기록)

> 오후 작업이 예상보다 오래 걸려 사용자가 18:30에 중단했다. 아래 1~2가 끝나야 로컬에서 다시 플레이할 수 있다.

### 1. 개발 계정 로그인 마무리 — 등급 A(인증), 계획 `docs/superpowers/plans/2026-09-16-dev-login.md` — **완료·main 머지**

귀가 후 20:39~21:01에 A등급 절차(task별 sonnet 검토 → opus 최종 리뷰 → 수정 1회)로 끝냈다. Task 1 리뷰(Important 1건: api_contract 기재 누락) → `34ce698`. Task 2(랜딩 `DevLoginForm`·`run_selfplay --dev-login`·헤드리스 `dev-login.cjs`) → `48a70ac`, 셀렉터 수정 `816f052`. opus 최종 리뷰 Important 2건(끄거나 계정 변경 시 기존 dev 세션이 14일간 유효하던 결함 → sub 대조 추가, 저장소 공개인데 계정 값이 문서·테스트에 적혀 있던 것 → 값은 `backend/.env`에만·추적 파일에서 제거) → `d659be3`·`be42385`, **590 passed**. `main`을 `be42385`로 ff-merge, 백엔드·프런트 재기동, 옛 비밀번호 401·새 비밀번호로 `dev-login.cjs` PASS 확인. 계정 id·비밀번호 값은 어떤 문서에도 남기지 않았다(비밀번호는 이번에 교체됨 — **값은 `backend/.env`에만 있다**).

### 2. Anthropic 모델 평가 — 등급 B(사용자 지정), 키는 평가 직후 제거 — **완료(측정·기록), 키 제거는 사용자 조치 남음**

키를 `.env`에 넣고 (a)~(e)까지 실행했다. (b) 어댑터 스모크 3종 OK — 단 Anthropic SDK 1.6.0에서 `Messages.create()`의 `temperature` 인자가 빠져 Haiku가 `TypeError`로 죽는 결함을 발견, `extra_body` 경유 전송으로 수정(`6a02a13`). (c) NPC 41문답 Haiku·Sonnet·Gemini(무료 키, 일부만) 비교 완료 — 러너의 발화 분류기 스텁 결함(매 턴 재생성 2+폴백 1이 provider와 무관하게 붙던 것)도 발견·수정. (d) Core self-play Sonnet·Opus·gemma4 대조군 3판 + gemma4 플레이어 1판 완료, `run_age7_check --provider anthropic`도 실행(1차는 채점기 VRAM 경합으로 Haiku 미달·Sonnet 2회 정지 → 채점기를 gemma4:12b(think off)로 통일 후 재측정해 kanana·Haiku·Sonnet 전부 4/5 통과). (e) `docs/model_evaluation.md` **부록 A.19** + 상단 "측정 결과" 열 + 변경 이력 row, `docs/metrics.yml` 16줄 기록 완료. **권고: Core `claude-sonnet-5` · NPC `claude-haiku-4-5`**(최종 결정은 사용자 몫). **(f) 키 제거는 아직이다** — 아래 "남은 것" ① 참고.

### 남은 것 (2026-09-16 밤 마감 시점)

1. **`backend/.env`의 `ANTHROPIC_API_KEY` 줄 제거는 사용자 조치** — 이 세션의 `.env` 편집은 권한 분류기가 막았다. 제거 후 `grep -c '^ANTHROPIC_API_KEY=' backend/.env` == 0 확인할 것.
2. **`feat/coherence-chain`의 `be42385` 이후 커밋(평가 러너·어댑터 수정·gemma4 통일, `6a02a13`~`06e0906`)은 아직 main에 머지되지 않았다.**
3. **`USER_DAILY_ATTEMPTS` 테스트 상향값을 되돌리고 백엔드를 재기동한다** — 컨트롤러가 오늘 밤 수행.
4. 2026-09-20 제출용 프로덕션 `.env`: Core `anthropic:claude-sonnet-5` · NPC `anthropic:claude-haiku-4-5` — 사용자 확정 후 전환.
5. Gemini 무료 키는 NPC 후보에서 제외(하루 20요청 상한).
6. F11 원숭이손은 아래 3번 그대로 미착수.
7. 클라이언트 IP는 `TRUST_PROXY=true`일 때 `CF-Connecting-IP`만 신뢰하도록 수정됨(2026-09-17). 배포 시 cloudflared 뒤에서 `TRUST_PROXY=true`.

### 3. F11 원숭이손 — 계획 `docs/superpowers/plans/2026-09-16-f11-monkey-paw-wishes.md` (8 task, 미착수)

엔진 부분 B등급, 소원 문장 C등급(시나리오 디렉터 확인 필요). 스펙 §3: 관리자가 만드는 소원 + 숨은 세계 인과 부작용, 두 번째 손은 정답률 40% 이상에서, 규칙은 회차 간 지속. Q군 삽화 `frontend/public/assets/clues/Q02~Q08`을 `imageMap`에 연결하는 것도 여기서.

### 4. 결정 대기·정리

- `output/npc-dialogue-2026-09-15`(28 파일, 42 MB) untrack 여부 — `/output/`은 이미 `.gitignore`에 있고 `git rm --cached`만 남았다. `output/voice`(35 파일)는 음원의 유일한 git 출처라 유지.
- 허들 후속: `users.blocked_at` + `require_user` 확인(행 삭제만으로는 차단 불가), 다중 워커 시 버킷 분리.
- F7 후속 티켓 9건(아래 절) — 머지 차단 아님.
- `docs/jekyll.md` 2026-09-16 마감 항목은 18:30에 추가함. 귀가 후 작업분은 새 소절로.

## F7 후속 티켓 (최종 리뷰에서 나온 경미 항목 — 머지 차단 아님)

- `door-handle` 리드가 `loop_n=5`인데 5회차 밤에는 신의 질문이 없어 도달 불가 → 4로 내리거나 삭제
- `test_scenario_leads.py`가 ask 리드의 target에 "어떤" 지식이 있는지만 확인 — ask 주제와 관련된 지식 id 매칭으로 강화. `test_fact_question_gets_verdict_prefix`는 기대 판정을 고정
- `ask()`의 `self._notes is not None` 가드가 confirmed 저장에만 있음 — 리드 노트 경로도 동일하게, 또는 NullNotesRepository
- 하네스 폴백 답 "지금은 답변을 정리하지 못했어…"가 해체 — 한다체로
- `find_anchor`가 관리자 방송(statement)도 닻으로 잡음 — observed로 제한 검토
- 여정 힌트가 종료된 판에서 "내일 …" — 문구 조정; 힌트가 잠긴 칸과 무관하게 순환 배정(기존)
- `adapter.py` 리드 표 위 주석이 옛 동작("해금") 설명 — 갱신
- 데드코드: `advisor_answer_messages`, `prompts.ADVISOR_ANSWER_SYSTEM`, `AdvisorAnswerOutput`(5종 리터럴) — 별도 정리 티켓
- `is_why_question` 부분 문자열 오탐(이유식·왜곡) — 실제 발화에서 드물어 보류

## 파일 지도

- 테스터6 기록: `docs/review-verification/2026-09-16-tester6/tester6.md`
- 밤 단서 제작서(치지직 시퀀스·P01~P05·Codex 브리프): `docs/REMAKE_DAY_이미지제작서_밤단서_v2.md` · 원숭이손 삽화: `docs/REMAKE_DAY_이미지제작서_원숭이손Q군_v1.md` · 붙여넣기 프롬프트: `output/imagegen/prompts_P_night_Q_paw.md`
- 리드 표·파편·인물 지식: `backend/apps/scenarios/scenario_a/adapter.py` (leads ~507, fragments ~539, 채연 지식 ~70, 준 지식 ~180)
- 신의 질문 답변·리드 선택: `backend/apps/engine/app/use_cases/intervention_interactor.py` (`ask` ~246, `select_lead` ~63, `options` ~372)
- 밤 파편 공개·결말: `backend/apps/engine/app/use_cases/night_interactor.py` (~318)
- NPC 발화 경로: `backend/apps/engine/app/use_cases/loop_interactor.py` (`_utter` ~238), 프롬프트 조립 `game_support.build_agent_messages`
- 밤 전환 화면: `frontend/components/screens/DoomTransition.tsx`, 이미지 매핑 `frontend/lib/imageMap.ts` (`doomImage`)
- 원숭이손: `loop_interactor._maybe_offer_paw` ~639, 부작용 실행 `scene_execution.py` ~77
- 운영 시나리오 A·B·C와 비용(외부 API 판당 비용·EC2·GPU): `docs/apiscenario.md`
- 개발 로그인: `backend/apps/engine/adapter/inbound/api/v1/auth_router.py`(`dev_login` 엔드포인트), `auth_interactor.dev_login`, `engine_dependency.get_auth_use_case`(DevAccountDTO 주입), 테스트 `tests/engine/test_dev_login.py`, 계획 `docs/superpowers/plans/2026-09-16-dev-login.md`
- 허들: `guards.py`(`require_user`·`ip_bucket`·`client_ip`), `guard_rules.py`(`TokenBucket`·`kst_day_start`), `session_interactor.start`, `frontend/components/screens/GuardScreen.tsx`, 테스트 `frontend/tests/guard.cjs`
- 오늘 로그: `docs/jekyll.md` 2026-09-16

## Anthropic 어댑터

- provider 값 `anthropic` (`.env`의 `CORE_LLM_PROVIDER`/`NPC_LLM_PROVIDER`), 모델 예시 `claude-sonnet-5`·`claude-opus-5`·`claude-haiku-4-5`(하이쿠는 `output_config.effort` 미전송). effort는 `ANTHROPIC_EFFORT`(기본 `low`)로 설정, 키는 `backend/.env`의 `ANTHROPIC_API_KEY`. 스모크: 이 세션의 `.env`에 키가 없어 **미실행**(`grep -c '^ANTHROPIC_API_KEY=.\+' backend/.env` == 0).
- thinking: 모델을 막론하고 `thinking` 파라미터를 보내지 않는다(Opus 5류에서 `disabled`는 도구 호출이 visible text로 새거나 `<thinking>` 태그가 누출되는 실패 모드가 있어, adaptive 기본을 그대로 둔다). 깊이 제어는 `output_config.effort`만 쓴다(하이쿠는 `effort`도 보내지 않는다).
- refusal/절단은 비재시도: `stop_reason`이 `refusal`·`max_tokens`·`model_context_window_exceeded`이면 `LLMRefusalError`를 낸다(`LLMParseError`가 아니다) — 재시도해도 같은 응답이므로 하네스가 재생성 없이 즉시 폴백한다.
- 스키마 strip: `output_config.format`이 거부하는 키(`minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`minLength`/`maxLength`/`maxItems`/`multipleOf`)는 제거하면서 그 값을 해당 필드 `description`에 `(제약: ...)`로 남긴다. `minItems`는 0/1일 때만 SDK와 동일하게 유지한다(그 외 값은 제거+description 기록).
- temperature는 하이쿠에만 전달한다(Opus 5/Sonnet 5는 거부). timeout은 `Settings.anthropic_timeout`(기본 120.0)으로 설정 가능.
- 테스터 노트: 비한글(영어·숫자·기호만) 입력은 규칙 게이트로 인물의 되묻기 대사가 나오며 이는 의도된 동작이다.

## 하지 말 것

- 이미지 파일명은 NFD로 저장된 것이 있다(`이미지제작서_v1`, `쿠키12종`). 셸 glob이 못 찾으면 python `unicodedata.normalize`로 연다. 새 파일은 NFC
- `pkill -f "uvicorn main:app --port 8500"`을 같은 셸 명령 안에서 쓰면 자기 자신을 죽인다(exit 144). `pkill -f "[u]vicorn …"` 패턴을 쓰고 기동은 `setsid nohup … &`로
- 테스터7 세션의 파일(`2026-09-16-tester7/`)과 그 세션의 미커밋 변경은 건드리지 않는다
- 검토 서브에이전트에게는 `git stash`·`checkout`·`reset` 등 상태를 바꾸는 git 명령을 금지한다고 명시한다(오늘 두 번 구현자 편집이 지워졌다)
- 개발 로그인(`DEV_LOGIN`)을 2026-09-20 전에 끄거나 지우지 않는다
- Anthropic 키는 평가가 끝나면 그날 바로 `.env`에서 지운다
