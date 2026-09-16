# 작업 이어하기 — 2026-09-16

> 이 문서 하나만 읽어도 이어서 작업할 수 있게 쓴다.
> 이전 인계(NPC 대화 개선 시점)는 `HANDOFF.md`(2026-09-15)에 그대로 있다.

## 현재 상태 — 테스터6 휴먼테스트와 개연성 설계

테스터6이 5회차를 완주했다(판 `2338ec9f`, 09:48~11:06, 8.8 → 64.2 → 94.2 ×3, 부작용 셀 0). 피드백 11건은 `review-verification/2026-09-16-tester6/tester6.md`에 원문·DB 대조·분류로 있다. 같은 날 다른 세션이 테스터7 기록(`review-verification/2026-09-16-tester7/`)을 따로 진행한다 — 서로 건드리지 않는다.

**즉시 수정 5건은 반영 완료, 미커밋.** F1 인물 대사 음원 보류(관리자·조언자·회고만 재생), F3 밤 근거 목록 "맨 위로" 고정 버튼, F4 신의 질문 답변 로그 높이 상한 제거, F5 규칙 없이 이미 하는 행동은 추천 규칙에서 제외, F6 관찰 기록·근거 목록의 회차 간 중복 문장 숨김. 검증: backend **462 passed** · tsc · 헤드리스 UI 7종 통과. 부수로 OAuth `credentials: "include"` 이후 깨져 있던 UI 테스트의 모의 CORS 헤더와 ToggleSwitch 셀렉터를 맞췄다.

**자산 제작·등록 (2026-09-16 오후)** — 밤 단서 P01~P05(9:16)와 원숭이손 삽화 Q02~Q08(3:2)을 사용자가 생성, 관리자 밤 방송 MA08~12 녹음 완료. 검수: P군 5장 전부 통과, Q군 6장 통과, Q04는 v1 보류(손잡이 허리 높이) 후 **v2 재생성 통과**(손잡이 문 상단). 통과분은 `frontend/public/assets/`(P), `assets/clues/`(Q), `audio/voice/`(MA08~12)에 복사하고 `voiceMap.ts`에 등록(대사 음원 34개). 음성은 형식·길이 확인 + 사용자 청취 검수 완료. 코드 참조(imageMap·DoomTransition)는 아직 없음 — Codex 브리프(P.6)로 구현 예정. 기록: `output/imagegen/P-v2-Q-v1-production.md`.
부수 수정: `VoicePlayer.tsx` BGM 페이드의 rAF 타임스탬프 음수 진행률로 볼륨이 0.25를 넘던 결함을 진행률 0 고정으로 수정(voice-playback 테스트가 재현 가능하게 실패하던 원인). 테스트 기대 수 29→34.

**인게임 확인 (2026-09-16 14:30)** — 헤드리스 UI 7종 전부 통과(gameplay-clarity·npc-followup·connected-investigation·five-loop-flow·voice-transitions·scene-illustrations·voice-playback). 실서버(8500·pigfarm DB) 셀프플레이 1회차 완주(판 `dfb1e585`, 플레이어 모델 kanana 상주 재사용, 69.8s): 발화 3·원숭이손 수락·밤 제출·신의 질문·규칙 적용까지 크래시 0, 하네스 재생성 0, 폴백 0. **F5 실동작 확인** — 채연이 규칙 없이 배급을 남긴 뒤 추천 규칙에 "채연: 배급을 남긴다"가 나오지 않음(옵션: 준 설명·은상 설명·은상 출처). 테스트 수정 2건: voice-playback 기대 수 34, connected-investigation의 근거 그림 크기 검사는 로드 완료를 기다린 뒤 검사(4MB 삽화 타이밍 실패 재현 2회 → 수정 후 통과).

**F8 밤 단서 시퀀스 — 구현 완료 (서브에이전트, 2026-09-16 14:40)** — 단서 표는 시나리오 `NightClueDTO` 5행이 단일 출처, `POST /nights/{id}/submit` 응답에 `night_clue {loop_n, caption, image_ids, voice_id, broadcast, outcome_line}`. 밤에 캡션(observed·scene)과 방송(reported·statement)을 「N회차 · 소등 후」 관찰·노트로 저장, 낮 노트의 고아 파편 5개 제거(배우 있는 진술·트럭 파편·7시 13분은 유지). `DoomTransition`: 결말 이미지 → 0.8s 방송 → 음원 50% 지점 치지직 1s(글로벌 CSS `.cookie-glitch` 재사용, 띠 3개, 2회차는 두 번) → 캡션 잔류 → 「계속」 탭(자동 진행 제거). 음원 실패 시 결말별 MA03/04/05 대체, 폐쇄는 MA06 이어 재생. 검증: backend **475 passed**(신규 13) · tsc · 헤드리스 6종 통과. 2회차 캡션은 방송과 중복되지 않게 "트럭 소리."로 정리(P.1). 부수: `test_e2e_flow`가 인스펙터 토큰을 하드코딩해 `.env` 토큰 교체 뒤 깨졌던 것을 설정값 참조로 수정.

**환경 변경 감지(이 세션 외부, 14:25)**: `backend/.env`의 `GOOGLE_OAUTH_REDIRECT_URI`·`FRONTEND_BASE_URL`이 `https://api.remakeday.com`·`https://remakeday.com`으로, `INSPECTOR_TOKEN` 교체, `NPC_LLM_MODEL=kanana1.5:8b-q4km`(HANDOFF 정본은 gemma4:12b). 백업 `.env.bak.20260916`. 로컬 OAuth 로그인은 이 값으로는 localhost에서 동작하지 않는다 — 배포 세션의 의도인지 확인 필요.

**서버**: 백엔드 8500 재기동됨(14:45, F8 반영)(NPC·Core `ollama:gemma4:12b`, embedding gemini), 프런트 3500. `/play` 200.

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

## 지금 바로 할 일 (우선순위 순)

1. **F7 구현 완료** (feat/coherence-chain, commits 40c4c47..HEAD). `POST /nights/{night_id}/questions` 응답에 `verdict`, `answer` 3부 형식, `unlocked_note(null)`, `next_observation(조언·null)`, `status`/`evidence` 추가. status="supported"일 때 kind "confirmed" 노트 저장. 리드 표 사실 공개 문장·면책 문장 제거. 검증: backend **490 passed** · tsc · 헤드리스 3종. DB: `alembic upgrade head` 적용. 다음: F2 · F11 구현 계획 착수
2. F7+F8 **캡션만으로 흐름 선검증** — 리드 표에서 사실 공개 문장 제거, 조언을 구조 기반 고정형으로, 파편을 낮 노트에서 빼고 결말 전환 뒤로. 러너 dry-run으로 5회차 사슬 확인
3. F2 규칙 게이트 → 분류기 순으로 구현. 테스트: "ㅋㅋㅋㅋ"·"......"·"왜왜왜왜"는 모델 호출 0, "왜?"·"왜 안어"는 통과
4. ~~밤 단서 이미지·Q군 제작~~ 완료. 남은 것: 밤 단서 시퀀스 실플레이 확인(구현 완료)(Codex, v2 P.6), 소원 구현 때 Q군 `imageMap` 연결
5. 커밋 — 즉시 수정 5건 + 문서. 커밋 전 `git status`로 테스터7 세션의 파일과 섞이지 않는지 확인


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
- 오늘 로그: `docs/jekyll.md` 2026-09-16

## Anthropic 어댑터

- provider 값 `anthropic` (`.env`의 `CORE_LLM_PROVIDER`/`NPC_LLM_PROVIDER`), 모델 예시 `claude-sonnet-5`·`claude-opus-5`·`claude-haiku-4-5`(하이쿠는 `output_config.effort` 미전송). effort는 `ANTHROPIC_EFFORT`(기본 `low`)로 설정, 키는 `backend/.env`의 `ANTHROPIC_API_KEY`. 스모크: 이 세션의 `.env`에 키가 없어 **미실행**(`grep -c '^ANTHROPIC_API_KEY=.\+' backend/.env` == 0).
- thinking: 하이쿠가 아닌 모델에는 `thinking: {"type": "disabled"}`를 보낸다(effort `high` 이하에서 허용). 하이쿠에는 `thinking`도 `output_config.effort`도 보내지 않는다.
- refusal/절단은 비재시도: `stop_reason`이 `refusal`·`max_tokens`·`model_context_window_exceeded`이면 `LLMRefusalError`를 낸다(`LLMParseError`가 아니다) — 재시도해도 같은 응답이므로 하네스가 재생성 없이 즉시 폴백한다.
- 스키마 strip: `output_config.format`이 거부하는 키(`minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`minLength`/`maxLength`/`maxItems`/`multipleOf`)는 제거하면서 그 값을 해당 필드 `description`에 `(제약: ...)`로 남긴다. `minItems`는 0/1일 때만 SDK와 동일하게 유지한다(그 외 값은 제거+description 기록).
- temperature는 하이쿠에만 전달한다(Opus 5/Sonnet 5는 거부). timeout은 `Settings.anthropic_timeout`(기본 120.0)으로 설정 가능.
- 테스터 노트: 비한글(영어·숫자·기호만) 입력은 규칙 게이트로 인물의 되묻기 대사가 나오며 이는 의도된 동작이다.

## 하지 말 것

- 이미지 파일명은 NFD로 저장된 것이 있다(`이미지제작서_v1`, `쿠키12종`). 셸 glob이 못 찾으면 python `unicodedata.normalize`로 연다. 새 파일은 NFC
- `pkill -f "uvicorn main:app --port 8500"`을 같은 셸 명령 안에서 쓰면 자기 자신을 죽인다(exit 144). `pkill -f "[u]vicorn …"` 패턴을 쓰고 기동은 `setsid nohup … &`로
- 테스터7 세션의 파일(`2026-09-16-tester7/`)과 그 세션의 미커밋 변경은 건드리지 않는다
