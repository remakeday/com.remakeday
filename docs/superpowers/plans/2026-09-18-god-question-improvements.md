# 신의 질문 개선 — 환급 · 조언 강조 · 사용법 안내 · 공개 사다리 (휴먼테스트 순서표 5번)

> **환급 철회 2026-09-18 저녁 (테스터12 F5)** — 이 문서의 환급 규칙(§1)은 설계 오류로 철회됐다. 새 규칙은 기획서 v9.0 §7.1 정정 문단 참고.

등급: **B (게임 로직·UI)** → 리뷰 Critical(비용: 동시 요청 레이스)로 **A 승격**. 사다리 문장·안내 답 문구는 **C (초안)** — 시나리오 디렉터 확인 전.

근거: 테스터9 F16(사용법 명시)·F19("알 수 없다" 편중 31/38≈82%)·F20 원칙 4(요약 먼저, 자세히는 펼쳐서), 테스터10 F5(목적·사용법 질문이 판정으로 들어가 전부 unknown). 설계 `docs/superpowers/specs/2026-09-16-coherence-chain-design.md` §2(F7 답변 형식), 기획서 v9.0 §4.4⑤·§7.1·§7.4.

## 사용자 결정 (2026-09-18)

1. "알 수 없다"면 질문 횟수 환급. 악용 방지 규칙 명시.
2. 조언(다음 행동 제안)을 답의 중심으로. 판정 배지 + 한 줄 답 먼저, 조언은 별도 블록, 근거·인용은 접기.
3. (a) 입력 위 안내에 두 사용법 명시 (b) 게임 목적·사용법 질문은 판정 대신 안내 답, 횟수 안 씀. 분류는 규칙(키워드 표) 우선.
4. 회차·점수 단계별 "신이 말해도 되는 사실" 사다리. 초안 문장, 정체 단어 금지.
5. 함께: xfail `test_spec_question_with_rice_word_is_supported` 원인 수정 후 xfail 제거. F10 `settle_status` 유지.

## 응답 계약 (`POST /nights/{night_id}/questions` — 필드 추가)

| 필드 | 뜻 |
|---|---|
| `kind: "answer" \| "guide"` (신규) | `guide`면 안내 답 — 판정 없음(`verdict=""`, `status="unknown"`, 근거·조언 없음), 횟수를 쓰지 않는다 |
| `refunded: boolean` (신규) | 이 질문이 "알 수 없다"라 횟수를 돌려받았는지. `remaining`은 이미 반영된 값 |

이벤트 `intervention_question`에도 `kind`·`refunded`를 남긴다(기본값 `answer`·`false` — 옛 이벤트 호환, 마이그레이션 없음).

## 1. 환급 규칙 (악용 방지)

`status == "unknown"`인 답(판정 질문, 모델 실패 포함)은 아래를 모두 만족할 때 횟수를 차감하지 않는다.

| 규칙 | 값 | 이유 |
|---|---|---|
| 같은 밤 환급 상한 | **3회** (`QUESTION_REFUNDS_PER_NIGHT`) | 기본 3회와 같은 수로 설명이 쉽다. 한 밤 모델 호출 최대 6회(검사 실패 재생성 포함 18회)로 비용 상한이 고정된다 |
| 같은 질문 재입력 | 환급 안 함 | 같은 밤 이전 질문과 공백·문장부호(`.,!?~…"'「」`)를 뺀 문자열이 같으면 환급하지 않는다(답은 한다) |
| 안내 질문 | 환급 대상 아님 | 애초에 차감하지 않는다. 상한도 쓰지 않는다 |

- 환급 사용 수는 저장하지 않고 계산한다: `len(night.questions) − (QUESTIONS_PER_NIGHT − night.questions_left)`. 안내 질문은 `night.questions`에 넣지 않으므로 식이 유지된다. 마이그레이션 없음.
- `supported`·`contradicted`·`왜` 질문의 `supported`는 환급하지 않는다.
- 남은 질문 0에서는 기존처럼 409(안내 질문 포함) — 입력창이 이미 숨는다.

## 2. 조언 강조 (GodScreen)

한 문답의 표시 순서:

1. 질문 (흐리게)
2. **판정 배지 + 한 줄 답** — 배지는 `verdict`에서 끝 마침표를 뗀 짧은 말(맞다·아니다·그건 알 수 없다). `왜` 질문은 배지 "이유는 말할 수 없다", `guide`는 "안내", wh 질문 supported(`verdict=""`)는 배지 없음. 한 줄 답은 본문 첫 문장. 환급이면 배지 옆에 "횟수를 돌려받았다".
3. **조언 블록** — `next_observation`이 있으면 주황 테두리 블록, 제목 "내일 해 볼 일", 행동 문장(「…」 뒤)을 크게, 닻 "네 기록: …"은 작게. 계약 형식(`네 기록의 「X」. Y`)이 아니면 통째로 크게.
4. **접기 "자세히"** — 본문 나머지 문장 + 판정 설명(STATUS_LABEL) + detail + 근거 카드. 내용이 없으면 접기 자체를 생략.

## 3. 사용법·목적 안내

### (a) 입력 위 안내 문구

- 전: "이 목소리는 오늘 일어난 일만 안다. 무엇을 했는지 물어라." / "맞다 · 아니다 · 그건 알 수 없다"
- 후: "가설을 넣어 물으면 맞다·아니다로 판정받고, 누가·무엇을 물으면 기록에서 찾아 준다." / "기록으로 알 수 없는 질문은 횟수를 쓰지 않는다 · 한 밤 세 번까지. 게임 방법을 물어도 된다."
- 입력 예시 첫 줄(가설 있음): `예: “{가설 28자}” 맞아?` — 가설을 넣어 묻는 사용법을 보여 준다.

### (b) 안내 질문 분류 표 (규칙 우선, LLM 판단 없음)

판정 순서: ① 질문에 플레이 가능 인물 이름이 있으면 **안내 아님**(세계 질문) ② 아래 표를 위에서부터 검사해 첫 적중 분류의 답.

| 분류 | 패턴(공백 정리 후) | 적중 예 | 비적중 예(판정 질문으로 간다) | 판단 근거 |
|---|---|---|---|---|
| 목적 | `게임` 포함 | "이 게임이 뭔지 이해가 안되 목적이뭐야?" | — | "게임"은 인물 발화 금칙어라 기록에 없다 → 항상 메타 질문 |
| 목적 | 문장 첫머리 (그래서/그럼/근데)(이 게임의/내/나의/우리/우리의) + 목적·목표 + (이/은/는/가) + 뭐·뭔·무엇 | "목적이 뭐야" | "관리자의 목적이 뭐야"(동기 칸 질문) | 주어 없는 목적 질문만 메타 |
| 목적 | 멸망(한다는/한다니/이라는/이란/이/은) + (게/건/거/것) + 뭐·뭔·무슨·무엇 | "세상이 멸망한다는게 뭔소린가" | "왜 멸망해?", "트럭이 오면 멸망한다는 거야?" | 멸망의 **뜻**을 묻는 것만 메타, **이유**는 판정 |
| 목적 | 문장 첫머리 (그래서/그럼/이제/근데)(나는/내가/난/우리는) + 뭘·뭐를·무엇을 + 해야/하면 | "뭘 해야 돼" | "채연은 뭘 해야 돼?"(이름) | 주어가 나·없음일 때만 |
| 사용법 | (너에게/너한테/네게/신에게/당신에게) … (물어/질문) | "왜 너에게 질문해야 해?" | — | 기존 meta 경로를 흡수 |
| 사용법 | (질문/묻는/물어보는) + (법/방법), 문장 첫머리 (뭘/뭐를/무엇을/어떻게) + (물어/질문) | "어떻게 질문해?" | — | |

안내 답 문구 (초안 — 시나리오 디렉터 확인 전):

- 목적: "세계는 오늘 밤 멸망하고, 너는 다섯 번의 하루 안에 왜 멸망했는지 알아내야 한다. 밤마다 무슨 일이 원인이었는지, 누가 왜 그렇게 했는지 써라. 낮에는 사람들에게 묻고, 밤에는 나에게 기록을 확인하고, 규칙 하나로 다음 하루를 실험해라."
- 사용법: "가설을 넣어 물으면 맞다·아니다로 판정한다. 누가·무엇을 물으면 기록에서 찾아 준다. 기록으로 판단할 수 없으면 알 수 없다고 답하고, 그 질문은 한 밤 세 번까지 횟수에서 빼 준다."

범위: 원인·동기를 밝혀 쓰는 게임이라는 수준까지만. 정체·부작용 칸, 점수 기준은 말하지 않는다(기획서 §4.4⑤). 기존 meta 답("이곳의 규칙이나 오늘 본 일에 관해 물어봐…")과 조언("원본 노트를 확인하거나…")은 사용법 답으로 대체한다.

## 4. 회차별 공개 사다리

### 기획서 §7.4와의 관계 (설계)

- 조언자는 여전히 **공개 기록만** 안다. 사다리 칸은 스토리보드·`hidden_truth`·`truth_claims`·결말 문장을 주는 것이 아니라, **관리자 방송·시설 안내처럼 세계가 흘리는 공개 사실**을 시나리오가 미리 적어 둔 것이다. 열린 칸은 공개 기록과 같은 자격(관찰 `observed`)으로 조언자 입력에 들어간다.
- 칸은 **질문이 그 주제를 물을 때만**(칸의 `cues` 적중) 입력에 붙는다. 묻지 않은 사실을 흘리지 않는다 — 판정 재료이지 단서 배포가 아니다. 노트·단서 기록에 자동으로 적히지 않는다. `supported` 판정의 근거가 되면 기존 규칙대로 확인 노트(`confirmed-ladder:{key}`)가 된다.
- 칸 문장 금지: 정체 단어(돼지·돈사·축산·살처분·수의사·열병·귀표·가축·동물), `truth_claims` 문장 그대로, 결말 문장. 테스트로 고정한다.

### 데이터 구조

```python
class AdvisorRungDTO(BaseModel):  # scenario_dto.py
    key: str            # 고유
    stage: int          # 1~5 — 이 단계부터 열린다
    cues: list[str]     # 질문 매칭 키워드 (최소 1)
    text: str           # 확인 가능한 사실 한두 문장
ScenarioBundleDTO.advisor_ladder: list[AdvisorRungDTO] = []
```

엔진이 만드는 관찰: `observation_id="ladder:{key}"`, `scene_title="세계에 알려진 사실"`, `beat=0`, `source_kind="scene"`, `verification="observed"`, `actor=None`, `loop_n=현재 회차`. 적중 칸은 단계 높은 순 최대 2개를 `relevant` 앞에 두고, 나머지를 기존 `advisor_context`가 채운다(합 8개 유지).

### 열림 기준 — 회차 바닥 + 점수로 한 칸 앞당김

`stage = max(loop_n, 1 + (best_total ≥ 25) + (best_total ≥ 50) + (best_total ≥ 75))`, `best_total` = 이 판에서 지금 회차까지 채점된 총점의 최댓값.

- **회차 바닥**: 점수가 낮아 막힌 플레이어(F19의 주 대상)도 회차마다 한 칸씩 열린다. 점수만으로 열면 도움이 필요한 사람일수록 닫힌다.
- **점수 앞당김**: 이해한 만큼 더 빨리 열린다(결말이 이해만큼 열리는 구조와 같은 방향). 25점마다 한 칸.
- **최댓값(ratchet)**: 한 번 열린 칸은 점수가 떨어져도 닫히지 않는다.
- 신의 질문은 1~4회차 밤에만 있으므로 칸은 1~4단계에 둔다.

### 사다리 초안 (시나리오 A)

| 단계 | key | cues | 문장 |
|---|---|---|---|
| 1 | checkup-paper | 검진·담당·흰 옷·이마·종이 | 오후 검진에서 담당자는 이마를 짚고 종이에 무언가 적은 뒤 지나간다. 검진 결과는 누구에게도 알려 주지 않는다. |
| 1 | ration-notebook | 배급·밥·쟁반·남기·남긴·남겼·수첩 | 민석의 수첩에는 날짜와 이름, 남은 쟁반 수가 적혀 있다. |
| 2 | transfer-night | 이송·트럭·실려·데려·비어 | 이송은 소등 뒤에 이루어진다. 이송된 사람의 자리는 다음 날 아침 깨끗하게 비어 있다. |
| 2 | chungsik-cough | 충식·기침 | 충식은 이송되기 전날 밤 기침을 했다. |
| 3 | paper-to-broadcast | 검진·종이·방송실·보고·알리·알린·명단 | 오후 검진 뒤 종이에 적힌 이름은 저녁에 방송실로 전달된다. |
| 3 | blanket-checkup | 담요·숨기·숨긴·숨겼·감추 | 담요를 두른 채 검진을 기다리면 담당자는 이마만 짚고 지나간다. |
| 4 | closure-count | 폐쇄·멸망·이상자·구역 | 구역 폐쇄 방송은 이상자로 적힌 이름이 셋에 이른 밤에 나온다. |
| 4 | next-zone | 옆 구역·다른 구역·관리자 | 방송실에서는 이 구역과 옆 구역의 상태를 함께 점검한다. |

1·2단계는 인물 지식·방송에 이미 있는 사실을 신이 확인해 줄 수 있게 한 것, 3·4단계는 원인 사슬의 고리(검진 기록→방송실, 숨김→검진 통과, 이상자 수→폐쇄, 옆 구역)를 사건 수준으로만 잇는다.

- 리뷰 지적(근접): 3·4단계 `blanket-checkup`·`closure-count`·`next-zone`이 정답에 가깝다 → **사용자 결정 A: 현재 문장 유지** (2026-09-18. 테스터 전원 "너무 어렵다", 노트 비채점으로 난이도 상승, 후반에만 열림 — 3단계는 3회차 또는 50점, 4단계는 4회차 또는 75점 이상).

## 5. xfail 원인 — `question_evidence` '밥' 필터

- 증상: "채연이 밥에서 소독약 냄새가 난다고 했어?" → 모델이 소원 관찰을 `supported`로 골라도 unknown.
- 원인: 주제 표 첫 줄이 **음식 명사**(밥·배급·음식)를 "남김" 주제의 트리거로 쓴다. 증거는 남김 낱말(남기·쟁반…)이 있어야 통과하므로, 남김과 무관한 밥 질문에서 관련 기록이 떨어진다.
- 수정: 남김 주제 트리거에서 음식 명사(밥·배급·음식)를 뺀다. 남김을 묻는 질문은 "남기/남긴/남겼/쟁반/몫"으로 계속 걸린다. 음식 명사만 있는 질문은 인물 필터(또는 전체)로 간다.

## 작업 (TDD)

| # | 작업 | 파일 | 테스트 |
|---|---|---|---|
| T1 | xfail 원인 수정 | `intervention_interactor.py` `question_evidence` | `test_paw_wishes.py` xfail 제거 → 통과, 기존 남김 질문 테스트 유지 |
| T2 | 순수 함수: 안내 분류·환급·사다리 단계 | `advisor_advice.py`, `game_constants.py` | `test_advisor_advice.py`: 분류 표 적중/비적중, 인물 이름 제외, 환급(상한·재입력·status), `ladder_stage`(회차 바닥·점수 앞당김·ratchet), `open_rungs`(단계·cue) |
| T3 | 인터랙터 배선 | `intervention_interactor.py`, `event_log_dto.py`, `engine_dependency.py` | `test_usecase_intervention.py`: unknown 환급·상한 3·같은 질문 재입력 차감·supported 차감·안내 질문 무차감·모델 호출 없음·노트 없음, 사다리 칸 근거로 supported·잠긴 칸 미사용·점수 앞당김 |
| T4 | 시나리오 사다리 데이터 | `scenario_dto.py`, `scenario_a/adapter.py` | `test_scenario_leads.py`: 단계별 2칸·키 고유·금칙 단어·truth_claims 문장 미포함 |
| T5 | 프론트 | `api.ts`, `GodScreen.tsx` | `npx tsc --noEmit`, 헤드리스 기대값(`connected-investigation.cjs`·`five-loop-flow.cjs`) 문구만 갱신(실행 안 함) |
| T6 | 계약 문서 | `docs/spec/api_contract.md` 신의 질문 절 | — |
| T7 | 스모크 | 로컬 ollama 조언자 모델 | 사다리 전/후 unknown 비율 감 |

기존 테스트 의미 변경(사용자 결정 반영):
- `test_question_without_public_record_is_unknown_and_consumes_one_question` → unknown이면 환급(`remaining == 3`, `refunded`).
- `test_meta_question_with_why_cue_still_gets_supported_verdict` → 안내 답(`kind="guide"`, 판정 없음, 횟수 유지).

## 결과 (2026-09-18)

- 관련 pytest 22파일 **425 passed**(전체 pytest는 테스트 DB 공유로 돌리지 않음), `lint-imports` 4 kept, 프론트 `tsc --noEmit` 클린. 헤드리스는 기대값만 갱신·미실행.
- 스모크(로컬 ollama `gemma4:12b` think off, `scripts/core_probes.py`의 DB 없는 공개 관찰 11건, 질문 10개, temperature 0):

  | 조건 | unknown | 사다리 칸이 근거에 오른 질문 |
  |---|---:|---:|
  | 4회차 · 사다리 없음 | 10/10 | — |
  | 4회차 · 사다리 전부 열림 | 7/10 | 9/10 |
  | 1회차 · 사다리 1단계만 | 9/10 | 4/10 (잠긴 2~4단계 칸은 입력에 안 붙음) |

  - 안내 질문 3개("이 게임이…", "멸망한다는게…", "뭘 해야 돼")는 모델 호출 없이 `guide`, "서로의 규칙이 있는가"는 판정 질문으로 갔다.
  - 사다리 칸을 근거로 고르고도 unknown인 3건 중 2건은 모델이 사실 문장 뒤에 "…가능성이 높다"를 덧붙여 F10 헤지 강등(`settle_status`)에 걸렸다. 판정은 보수적으로 두고 환급으로 보상한다 — 프롬프트 조정은 범위 밖.
  - 1회차에서 "검진 뒤 적힌 이름이 방송실로 가?"가 본문 "…가는지는 확실치 않다"인데 `맞다.`로 나왔다(F10 계열, 헤지 어휘 누락). `_HEDGE_CUES`에 "확실치 않"·"확실하지 않"을 추가하고 테스트로 고정했다.

## 리뷰 반영 (수정 1회, A등급 승격)

리뷰 Critical(비용) 1건·Important 1건을 반영했다. 최종 리뷰는 opus.

### 1. (Critical) 같은 밤 동시 요청 레이스 → 밤 행 잠금

- 증상: `ask()`가 `questions_left`·`questions`를 읽고 환급 여부를 계산해 차감하는 구간에 잠금이 없었다. 같은 밤 병렬 POST가 서로의 차감을 못 보고 통과해 환급 상한 3·한 밤 모델 호출 상한 6을 넘고, `questions = asked + [text]` 덮어쓰기로 질문 기록이 유실됐다.
- 수정: `scene_transaction.py`에 `NightTransaction`(낮 장면 `SceneTransaction`의 잠금 단계만 바꾼 하위 클래스, Template Method). 밤 행을 `with_for_update()` + `populate_existing`으로 잠가 다시 읽고, 그 밤의 회차 행도 다시 읽는다(기다리는 동안 규칙 선택이 회차를 닫았을 수 있다 — 라우터 소유 확인이 회차를 이미 세션에 올려 두므로 새로 읽지 않으면 옛 상태로 판정한다). 인터랙터는 `ask`·`choose_rule`을 `with self._night_transaction(night_id)`로 감싸고, 컴포지션 루트가 `NightTransaction(session)`을 주입한다(낮 장면 `scene_transaction=SceneTransaction(session)`과 같은 방식). 포트 `SceneTransactionPort`의 인자 이름은 `loop_id` → `row_id`(낮=회차, 밤=밤).
- **모델 호출 위치: 잠금 안.** 같은 밤의 두 번째 요청은 첫 요청의 모델 응답 시간만큼 기다린다(→ opus 최종 리뷰 C1에서 기다리지 않고 409로 바뀜, 아래 절). 한 사용자·한 밤이고 입력창이 응답 중 비활성이라 실제로 겹치는 건 중복 클릭·재전송뿐이므로 수용한다. 낮 장면 발화도 회차 잠금 안에서 모델을 부른다. 잠금 밖(예약 차감 → 결과로 환급 확정 2단계)은 예약 상태·실패 시 되돌림이 추가로 필요해 이득 대비 복잡하다. 요청 세션의 DB 연결은 이전에도 모델 호출 동안 열려 있었으므로(소유 확인 조회로 트랜잭션 시작) 연결 점유는 늘지 않는다. 모델 호출 감사(`harness_event`)는 기존 규칙대로 별도 세션에 즉시 커밋돼 롤백돼도 남는다.
- 잠금 필요성 점검:
  - `choose_rule`: **같은 잠금 적용.** 동시 선택 둘이 모두 `rule_chosen=False`를 보고 통과했다(모델 비용은 없지만 한 밤 규칙 두 개 적용 또는 같은 `rule_id` 충돌 500). 이제 규칙 추가·`rule_chosen`·회차 닫기가 한 커밋이다.
  - `preview_rule`: 적용 안 함. 모델 호출 없는 유한 문법 해석이고 미리보기 이벤트만 남긴다. 적용은 `choose_rule`이 마지막 미리보기를 잠금 안에서 확인한다.
  - `options`: 적용 안 함. 모델 호출 없이 결정론으로 한 번 계산해 저장한다. 동시 조회는 같은 목록을 두 번 쓸 뿐이다. `ask`가 잠금을 쥔 동안 첫 조회의 저장은 행 잠금으로 기다리지만, 프론트는 규칙 단계에서만 후보를 부른다.
- 테스트(`test_usecase_intervention.py`, 실제 DB 세션 둘·스레드·컴포지션 루트 배선): 두 요청이 모두 모델 호출 안에 들어오면 서로 만나는 가짜 모델로 레이스를 재현.

  | 테스트 | 수정 전 | 수정 후 |
  |---|---|---|
  | 환급 2회 쓴 밤에 unknown 질문 둘 동시 | 둘 다 환급(`[True, True]`) | 하나만 환급, `questions_left=2`, 질문 기록 4개 둘 다 보존 |
  | 환급 3회·남은 1회 밤에 질문 둘 동시 | 모델 호출 2회(한 밤 7회) | 모델 호출 1회, 다른 요청 409, 기록 6개 |
  | 규칙 선택 둘 동시 | 두 번째가 409가 아닌 오류(같은 `rule_id` 충돌) | 하나 적용·하나 409, 규칙 1개 |
  | 소유 확인이 회차를 먼저 읽은 세션 + 규칙 선택 뒤 질문 | (회차 다시 읽기를 뺐을 때) 닫힌 회차에 질문 통과 | 409, 모델 호출 0 |

  교착 없이 끝난다(4개 약 4초).

### 2. (Important) 안내 질문 이름 뒤 경계

- 증상: `guide_kind`의 이름 매칭이 앞 경계만 봐서 "게임 준비 어떻게 해?"·"이 게임 준비물이 뭐야?"가 "준"으로 인물 질문이 돼 안내 대신 판정으로 갔다.
- 수정: 이름 뒤에 `이`(선택) + 조사·호격(한테서·에게서·한테·에게·께서·께·랑·하고·처럼·보다·까지·부터·으로·로·야·아·가·는·은·를·을·의·도·만·과·와, 선택)이 오고 그 뒤로 한글이 더 이어지지 않을 때만 인물로 본다. 문장부호·공백·문장 끝은 경계다.
- 표 테스트(`test_advisor_advice.py`): 준비·준비물·준수·수준 → 안내(`purpose`), "준한테 물어봐도 돼?"·"준이 뭐 했어?"·"준아, 게임이 뭐야?"·"준이가 게임이라고 했어?"·"채연이랑 게임 얘기했어?" 등 → 인물(None). 수정 전 3건 실패 → 수정 후 통과.
- 남은 한계: 목록 밖 접미("준씨", "준네")는 인물로 보지 않는다. 문장에 "게임" 같은 안내 낱말이 함께 있을 때만 안내로 새므로 영향이 작다.

### 반영하지 않음

- 사다리 3·4단계 정답 근접 — 사용자 결정 A(유지). §4에 기록.
- GodScreen 범위 밖 변경 분리 — 커밋 시점 사안.

### 검증

- 관련 pytest 18파일 **381 passed**(advisor·attempt_ownership·e2e·guards·question_rule_flow·scene_transaction·usecase_day·usecase_intervention·npc_dialogue_contract·paw_wishes·advisor_leads·night_writing_advisor·question_polarity·question_stage_isolation·question_triggered_rule·scenario_leads·connected_investigation·usecase_night). 전체 pytest는 테스트 DB 공유로 돌리지 않음.
- `lint-imports` 4 kept.

## opus 최종 리뷰 반영 (수정 1회)

Critical 1건(C1)·Important 3건(I1~I3)·Minor 묶음을 반영했다. 이후는 컨트롤러 범위 재검토.

### C1. (Critical) 연결 풀 고갈 → 모델 호출 뒤 롤백 → 무료 재호출

- 증상(리뷰 probe): 밤 잠금을 기다리는 요청들이 연결을 쥔 채 쌓여 요청 풀이 차면, 잠금 안의 감사 기록(`harness_event`, 별도 세션)이 두 번째 연결을 못 얻고 `pool_timeout` 뒤 예외 → 요청 전체 롤백. 모델은 이미 불렀는데 차감·질문 기록이 사라져 같은 요청을 무료로 반복할 수 있었다(풀 2개 중 1개 점유, 남은 1회 밤에 4번 질문 → 모델 호출 4회).
- 수정 1 — 잠금은 기다리지 않는다: `NightTransaction._lock`을 `with_for_update(nowait=True)`로. 잠금 실패(`LockNotAvailable`)는 포트의 `RowBusy`로 올리고, 인터랙터 `_night_turn`이 `GameStateError`로 바꿔 기존 409 매핑을 탄다(질문 "앞 질문에 답하는 중이다. 답을 받은 뒤 다시 물어라.", 규칙 선택 "앞 요청을 처리하는 중이다. 잠시 뒤 다시 골라라."). 프론트는 기존대로 409 `detail`을 오류 토스트로 보여 준다. 기다리는 요청이 연결을 쥐고 쌓이지 않는다. `lock_timeout`보다 NOWAIT를 고른 이유: 입력창이 응답 중 비활성이라 같은 밤 동시 요청은 중복 클릭·재전송뿐이고, 짧게라도 기다리면 모델 응답 시간(수 초)보다 짧은 값으로는 어차피 실패한다.
- 수정 2 — 감사 기록은 주 트랜잭션을 롤백시키지 않는다: `EventLogRepository._record_audit`가 감사 전용 작은 엔진(`core.matrix.grid_oracle_database_manager.get_audit_engine`, 풀 2+2, 대기 5초, 세션 URL별 캐시)에 쓰고, `SQLAlchemyError`는 로깅만 하고 삼킨다.
  - 선택 이유(비용 무결성): 격리만으로도 "모델을 불렀으면 차감·질문 기록이 커밋된다"는 보장이 선다. 전용 풀을 함께 둔 건 요청 풀이 찼을 때 감사 기록이 30초(기본 `pool_timeout`) 동안 요청 연결과 밤 잠금을 쥔 채 기다리다 사라지는 것을 막기 위해서다 — 회고의 `model_calls` 집계가 이 기록으로 센다. 감사가 끝내 실패하면 기록만 잃고(로그에 남음) 비용 쪽은 잃지 않는다.
  - 이 저장소는 낮 장면(`SceneTransaction`)도 같이 쓰므로 낮 발화의 감사 기록도 같은 격리를 받는다. 낮 장면 잠금 자체는 바꾸지 않았다(범위 밖).
- "호출 예약"(모델 호출 전 차감 커밋) 검토 → 채택하지 않음: 커밋하면 행 잠금이 풀려 같은 밤 동시 요청 409가 깨지고, 예약 상태·환급 확정 2단계·실패 되돌림이 필요하다. 위 두 수정 뒤 모델 호출 후 롤백이 남는 경로는 이미 잡은 요청 연결에서의 DB 장애(커밋 실패)뿐이며, 그때는 다음 요청의 잠금 조회도 모델 호출 전에 실패한다.
- 테스트(`test_usecase_intervention.py`, 실제 DB 세션·컴포지션 루트 배선):

  | 테스트 | 수정 전 | 수정 후 |
  |---|---|---|
  | `test_full_request_pool_does_not_make_the_last_question_free` (리뷰 probe: 풀 2개 중 1개 점유, 환급 소진·남은 1회 밤에 4번 질문) | 감사 `TimeoutError`로 롤백, 모델 호출 4회 | 모델 호출 1회, 나머지 3번 409, `questions_left=0` |
  | `test_model_call_audit_failure_does_not_roll_back_the_charge` (감사 엔진 예외 주입) | (주입 지점 없음) 롤백 → 무료 재호출 | 첫 요청 커밋, 이후 409, 모델 호출 1회, `intervention_question`만 남고 `harness_event` 없음, 로그 남음 |
  | `test_question_while_the_same_night_is_answering_is_409_without_waiting` | 뒤 요청이 앞 요청 끝까지 대기 | 앞 요청이 모델 호출 안에 멈춘 동안 뒤 요청 즉시 409, 모델 호출 1회 |
  | `test_refund_cap_holds_when_a_second_question_arrives_during_an_answer` (옛 동시 환급 상한 테스트 대체) | 대기 후 둘 다 처리 | 뒤 요청 409 → 다시 보내면 환급 상한 3으로 차감, 질문 기록 4개 |
  | `test_rule_choice_while_another_choice_is_applying_is_409_and_one_rule_applies` | 대기 후 "이미 규칙을 정했다" | 즉시 409, 규칙 1개 |

- 동시성 테스트의 1초 타이밍 의존 제거: `_MeetingModel`(1초 대기)·`Barrier(timeout=1)` 대신 앞 요청을 이벤트로 잠금 안에 세워 두고, 뒤 요청이 돌아온 순간 앞 요청이 아직 멈춰 있는지(`first_still_held`)로 "기다리지 않음"을 판정한다. 10초는 실패 시에만 닿는 안전 상한. 파일 전체 약 2초(수정 전 레드 실행은 약 44초).

### I1. 안내 분류 오분류

- 목적 행 "뭘 해야/하면" 뒤에 짧은 어미(돼·되지·될까·해·하지·할까·하나·하냐·하는 거야, 선택 `요`)와 문장 끝만 허용. 사용법 두 행은 뒤에 같은 문장의 짧은 끝(문장부호 없는 10자 이내)만 허용 — 문장부호 뒤에 다른 질문이 붙으면 판정 질문.
- 음성 테스트 5건(`test_question_with_a_world_goal_or_a_follow_up_is_not_a_guide_question`): "뭘 하면 이송돼?", "뭘 해야 검진을 통과해?", "무엇을 하면 구역이 폐쇄돼?", "뭐 하면 멸망을 막아?", "너한테 물어봐도 돼? 트럭 언제 와" — 수정 전 5건 실패(purpose 4·usage 1) → 통과. 기존 양성 표본 유지, 끝을 좁혀도 안내로 남아야 하는 "뭘 해야 돼요?"·"뭘 해야 하는 거야?" 추가.

### I2. 사다리 원문 누출

- `status == "unknown"`이면 근거에서 `ladder:` 칸을 뺀다 — 모델이 고른 근거든 폴백 근거든. 남은 근거가 없으면 `detail=None`. `supported`·`contradicted` 근거의 칸은 그대로다.
- 화면: 근거 카드에서 `ladder:` id는 회차·장면·"장면에서 관찰" 없이 "세계에 알려진 사실" 카드(`WorldFactCard`)로 따로 표시.
- 테스트: `test_unknown_answer_never_shows_rung_text_as_a_confirmed_record`(probe "검진 결과는 어디로 가?" — 수정 전 `detail`에 "1회차 · 관찰: (칸 원문)" + 환급), `test_unknown_answer_drops_a_rung_the_model_cited`(헤지 강등 unknown).
- 남은 한계: 모델 본문(answer)이 칸 문장을 풀어 쓴 뒤 헤지로 unknown이 되면 본문에는 남는다(스모크 3건 중 2건 유형). 환급 상한 3·같은 질문 차감으로 묶여 있다.

### I3. 정본 충돌·절 번호

- 기획서 v9.0 §7.1: 사다리 예외 한 문장, "횟수 환급과 안내 답" 문단(상한 3·재입력 차감·모델 실패 제외·호출 6회/재생성 포함 18회·안내 답). §7.4: "예외 — 공개 사다리" 문단. 상단 패치 기록 한 줄.
- 번호 정정(§4.8⑤→§4.4⑤, §5.5·§5.6→§7.1·§7.4): `advisor_advice.py` 모듈 docstring·안내 주석, `intervention_interactor.py` 조언·사다리 주석, `scenario_dto.py` `AdvisorRungDTO`, `scenario_a/adapter.py` 사다리 주석, `api_contract.md` 신의 질문 절, 이 계획서.

### Minor

- 모델 실패 질문 재입력: 이벤트 `model_failed`(기본 false, 옛 이벤트 호환)를 남기고 같은 질문 비교는 `kind=="answer"`이고 `model_failed`가 아닌 이전 질문만. 상한 집계식은 그대로. 테스트: 실패 질문 4번 → 환급 3번 후 차감 / 답한 unknown 재입력은 차감 유지.
- 안내 문답을 최근 대화 2쌍·같은 질문 비교(`intervention_interactor._ask`)와 회고 `questions_asked`(`inspector_interactor.harness_view`)에서 제외. 테스트 `test_guide_question_is_not_part_of_the_recent_conversation`, `test_retrospective_question_count_excludes_guide_answers`.
- `GodScreen.tsx`: 머리 문구 "낮 대화와 별도로 세 번 물을 수 있다. 알 수 없다는 답에는 횟수를 쓰지 않는다.", 안내 답은 접지 않고 전문 표시, 질문 응답 대기 중 "규칙을 고른다" 비활성, "횟수를 돌려받았다" `text-sm opacity-60` → `text-base opacity-80`(입력 위 안내 문구와 같은 단계).
- §1 표 비용 수치: 한 밤 모델 호출 6회(재생성 포함 18회).

### 보고만 (범위 밖 — 별도 A등급)

- `POST /nights/{id}/submit`(`night_interactor.py` `submit`): 잠금·버킷 없음 → 동시 제출로 채점 모델 호출 N배.
- `start_loop` planner 호출: 회차 행 잠금 없음.
- 낮 장면 `SceneTransaction`: 회차 잠금이 기다리는 방식이라 C1과 같은 풀 적체 구조(감사 기록 격리는 이번에 함께 적용됨).

### 검증

- 관련 pytest 24파일 **484 passed**: advisor_advice·attempt_ownership·connected_investigation·e2e_flow·event_log·five_loop_rules·guards·paw_wishes·question_rule_flow·scenario_leads·scene_transaction·usecase_day·usecase_intervention·usecase_night·advisor_leads·night_writing_advisor·question_polarity·question_stage_isolation·question_triggered_rule·journey_and_reveal·night_clue·npc_dialogue_contract·remake_day·rule_enforcement. 전체 pytest는 테스트 DB 공유로 돌리지 않음.
- `lint-imports` 4 kept, 프론트 `tsc --noEmit` 클린. 헤드리스 미실행.
