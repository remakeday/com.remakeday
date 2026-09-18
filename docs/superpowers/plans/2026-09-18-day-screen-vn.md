등급: **B (게임 UI 동작)** — task마다 구현(T1 백엔드 Claude 서브에이전트, T2~T5 프론트 Codex CLI — 사용자 지시), 마지막에 sonnet 전체 리뷰 1회, 수정 1회, 재검토는 컨트롤러 diff 확인.

# 낮 화면 재구성 — 비주얼노벨 대사창 구현 장부 (2026-09-18)

설계: `docs/superpowers/specs/2026-09-17-day-screen-vn-design.md`(09-17 사용자 승인). 사용자 착수 지시 2026-09-18 14:50 "프론트 작업해줘".

| Task | 담당 | 상태 |
|---|---|---|
| T1 서버 `lines` | Claude | 완료 15:02 — `sentence_rules.split_sentences`·`LineDTO`·`scene_execution` 줄 레코드·네 응답 `lines`, 계약 문서·`api.ts`, 테스트 +26(1008 passed), sonnet 검토 1회(따옴표 짝 수정) |
| T2 줄 표시 기반(`lineStyles`·reducer·`LineBox`) | Codex | 완료 15:15 — `lib/lineStyles.ts`(46)·`day/dayMode.ts`(33)·`day/LineBox.tsx`(81) |
| T3 낮 화면 조립 | Codex | 완료 15:15 — `day/SceneIntro`·`DialogueStage`·`AskBar`·`PawPopup` 신규, `DayScreen.tsx` 854→305, `page.tsx` `initialLines` 전달. tsc 통과, `next lint`는 Next 16에서 제거돼 미실행 |
| T4 공통 HUD·기록 패널 | Codex | 완료 15:32 — `hud/Hud`(38)·`RecordsPanel`(80)·`RecordLog`(75)·`GuideAndRules`(15), `page.tsx`에 HUD 1회 배치(guard/login 제외 전 phase), 관찰 상태를 page.tsx로 올려 HUD·밤 갤러리 공유, NEW = `loop_n === 현재 loop_n`, tsc 통과 |
| T5 헤드리스 정리·추가 | Codex | 구현, 브라우저 검증 차단 — 기존 8개 갱신·`day-screen-vn.cjs` 추가, tsc·구문 검사 통과. 10개 순차 실행 모두 sandbox 소켓 차단으로 Chrome 시작 실패. 아래 메모 참조 |
| 전체 리뷰 | sonnet | 완료 16:33 — Critical/Major 없음. Minor 3(문장 분할 따옴표 종류 확장, narration≠lines는 설계대로임을 주석으로, 진입 화면 2일째 문구가 EntryScreen 인라인과 GameplayGuide 두 곳) — 반영 안 함, 기록만 |

## T1 메모 (스펙과 다른 점)
- `voice_id`는 전부 None — 서버에 낮 방송 음원 ID 개념이 없어 프론트 `voiceMap.voiceForLine` 문구 매칭 유지.
- `speaker`는 인물 코드가 아니라 이름. `statement`·`fragment` 텍스트는 `이름: "…"` 접두를 그대로(표시 표에서 뗀다).
- `image_id`는 scene 줄 외에 삽화가 있는 action/rule_result 줄에도.
- 정상 답변 뒤 system 줄은 넣지 않음(gated만 system).

## 스크린샷 (PC 1440px, 실서버, 2026-09-18 15:37)
`frontend/tests/day-screen-vn-shots.cjs`(헤드리스, 개발 로그인 → /play) → `frontend/tests/.playwright-out/day-screen-vn/01-entry-hud … 11-scene2-intro.png`. 확인: 도입 1/7 줄·입력 잠금, 모두 보기 → 대화 모드(7/7, 시스템 줄), 질문 뒤 채연 답변 줄 8/9·카드 "이 장면 대화 완료" 흑백·게이지 1칸 감소, ◀ 거슬러 보기, 기록 패널(NEW·그림 보기·두 탭), 2번째 장면 도입.

## T5 메모 (2026-09-18)

- 기존 8개 스크립트에 서버 순서의 `lines`, 도입/응답 읽기, AskBar meter·묻기, HUD 기록·안내/RecordLog 선택자를 적용했다. `voice-playback`에는 HUD observations 응답을 추가했다. `dev-login`은 수정하지 않았다.
- `day-screen-vn.cjs`: 390/1440px 첫 줄·잠금·▶/◀·모두 보기·답변 누적·장면을 넘는 하루 이력·종류별 스타일·게이지·흑백 초상·HUD 위치·두 탭·NEW·기록 그림·도입 뒤 원숭이손을 검증한다. 진입 전에는 1일째, fixture의 회차 시작 뒤 아침/낮/밤/신 화면에서는 3일째를 확인한다.
- `vn-helpers.cjs`: Line fixture, 마지막 줄까지 읽기, meter 값 확인만 공유한다.
- BGM 조사: `<audio src="/audio/game-bgm.mp3">`는 `play/page.tsx`의 고정 위치이며 `DayScreen` 밖이다. `five-loop-flow`와 `guard`는 헤더·route 구현상 **가짜 API** 테스트다. 기존 `five-loop-flow` 응답에 `lines`가 없어 `DayScreen` 렌더 중 `TypeError: Cannot read properties of undefined (reading '0')`가 나는 것을 React 서버 렌더로 재현했다. `lines` 제공 시 렌더 성공. 기존 오디오 동일성 검증을 유지하고 도입→대화·낮→밤 검사와 렌더 오류 선행 검사를 추가했다. 컴포넌트는 변경하지 않았으며 브라우저에서 오디오 회귀 여부의 최종 확인은 남아 있다.
- 확인: `cd frontend && npx tsc --noEmit` PASS, 대상 10개 및 helper의 `node --check` PASS, `git diff --check` PASS.
- 실행: 지정 NODE_PATH로 dev-login → guard → gameplay-clarity → npc-followup → connected-investigation → scene-illustrations → voice-playback → voice-transitions → five-loop-flow → day-screen-vn을 **순차 실행**. 모두 FAIL(환경): 첫 오류 `browserType.launch: Target page, context or browser has been closed`. Chrome 로그의 원인은 `setsockopt: Operation not permitted`(dev-login은 `shutdown: Operation not permitted`); localhost HTTP 확인도 `failed to open socket: Operation not permitted`로 차단됐다. 실행 로그: `/tmp/t5-results/<script>.log`, 요약: `/tmp/t5-results/results.json`.
- 서버 시작/재시작, 보이는 브라우저, 백엔드/제품 컴포넌트 수정, 커밋 없음. 소켓 접근이 허용된 환경에서 10개 UI 테스트 통과 확인 후 T5 완료 처리한다.

## 사용자 추가 요청 (15:45~15:52, Codex 큐 T6→T7→T8)
- T6: 플레이 안내를 1일째 진입 화면에 전부 표시(2일째부터는 [기록·안내] 패널로 재열람), 인물 카드 4칸은 그림 없이 이름만.
- T7: 남은 대화 게이지를 "기상 — 7:12" 제목 줄 아래로, 라벨 "남은 대화 횟수"; 비트 표기 "장면 1/6".
- T8: 대사창 본문에 좌우 패딩·최대 폭.
- 헤드리스 실행·스크린샷은 Codex 샌드박스 제약으로 컨트롤러가 체인 종료 뒤 일괄 실행.

## 헤드리스 실행 (컨트롤러, 16:12~16:25, T8 뒤)
10종 순차: PASS 8(gameplay-clarity·npc-followup·scene-illustrations·voice-playback·voice-transitions·guard·dev-login·five-loop-flow — BGM 요소 동일성 단언 포함, 회귀 아님), FAIL 2 → T9(Codex): `day-screen-vn.cjs` hudPosition boundingBox null(가시성 대기 누락), `connected-investigation.cjs` 기록 패널 그림 보기에서 Tab이 대화상자 밖으로 나감(RecordsPanel 포커스 트랩 부재 — 실제 접근성 결함).
스크린샷 갱신 16:11: 12-entry-guide(진입 안내 전체)·13-cards-names-only·14-gauge-under-title 추가, 나머지 재촬영. 진입 화면 요약 문장이 두 번 보이는 점 사용자에게 보고.

## T9~T11 (Codex) · 마무리
- T9: `RecordsPanel` 포커스 트랩(Tab/Shift+Tab 순환) 추가 — 실제 접근성 결함 수정. `day-screen-vn.cjs` boundingBox 가시성 대기.
- T10: `RecordLog` 그림 보기에서 돌아올 때 opener를 요소 참조 대신 `data-observation-id`로 재조회해 포커스 복귀.
- T11: 플레이 안내 4줄로 축약(사용자 요청 "꼭 필요한 것만"), 진입 화면 중복 요약 문장 제거, `connected-investigation.cjs` 포커스 대기 조건을 body가 아닌 opener 버튼으로(컨트롤러가 디버그로 원인 확인).
- 최종: 백엔드 1008 passed, tsc 통과, 헤드리스 10종 전부 통과(컨트롤러 실행), 스크린샷 14장 갱신.
- 남은 것: EntryScreen 2일째 인라인 문구 정리, 문장 분할기 「」·' 따옴표, 9b 트럭 방송 연결(5회차 하루 끝 지점), 390px 실기기 확인(헤드리스 390 뷰포트만 통과), 테스터7 F2·테스터9 F15는 범위 밖.

## T12·T13 (Codex, 16:40~16:53)
- T12: 제목 블록 세 줄(기상 — 7:12 / 장면 1/6 / 남은 대화 횟수 게이지). T13: HUD [기록·안내] → [기록]·[안내] 두 버튼, 각자 탭 없는 패널(공용 셸에 포커스 트랩). 헤드리스 10종 통과(컨트롤러), 스크린샷 09-record-panel·10-guide-panel로 교체.

## astra 재구현 (사용자 결정 16:50 — 별도 브랜치에서 처음부터)
워크트리 `/home/kimchungsik/projects/com.remakeday-astra`, 브랜치 `feat/day-screen-astra`(기준 `1be2dc3` = T1 백엔드까지), 프론트 dev 3510. Codex `-m gpt-6-astra`(reasoning high)로 A(구현: T2~T4 + 사용자 조정 전부 한 세션) → B(헤드리스 갱신·신규, `FRONTEND_URL` 환경변수) 순. 헤드리스 실행·스크린샷은 컨트롤러(3510). 백엔드 CORS가 3500만 허용해 실서버 스크린샷은 비교 시점에 3500을 잠시 astra 워크트리로 바꿔 찍는다. 완료 후 두 결과 비교는 사용자가 고른다.
