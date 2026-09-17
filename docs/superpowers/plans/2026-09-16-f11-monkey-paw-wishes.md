# F11 원숭이손 소원 표 Implementation Plan

> ✅ **2026-09-17 재작성 완료** — 스펙 §3(2026-09-17 개정본, 방식 A) 기준으로 다시 썼다. 옛 계획(소원 `skip-checkup`·`mute-eunsang`·`deaf-minseok`·`sleep-jun`, 발화 침묵 `silence`, `required_rules`, 최저 칸 겨냥)은 폐기했다.
> **진행 2026-09-17:** Task 1~9 완료. 구현 중 반영: ② `checkup-record` 장면을 "종이를 읽는다" → "담당자가 소리 내어 '여기는 이상 없음.'"으로, 소원 문장을 "검진 담당자가 채연을 두고 무슨 말을 하는지 들린다."·행동을 `검진 결과를 듣는다`로 변경(인물은 글자를 못 읽는다 — 테스터9 F24, 컨트롤러 지시, 스펙 §3 같은 줄 수정). 잠재 행동 1인칭 `explanation`·소원별 `default_reason`은 스펙에 없어 서술에서 옮긴 초안을 넣었다. 신의 질문 "채연이 **밥**에서 소독약 냄새가 난다고 했어?"는 F7 `question_evidence`의 '밥' 주제 필터 때문에 아직 unknown — `test_spec_question_with_rice_word_is_supported`를 strict xfail로 남겼다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 원숭이손 소원 4종(`chaeyeon-honest`·`checkup-record`·`broadcast-room`·`band-meaning`)을 구현한다. 소원은 사실이지만 원인 사슬 밖을 가리키는 장면(보이는 규칙)을 만들고, 같은 날 뒤 비트에 원인 사슬을 한 칸 밀어내는 반대 사건(숨은 규칙)이 실제로 일어나 세계 상태(이상자·소문 지수)를 바꾸고, 전부 의도대로 일어난 날에만 부작용 관찰 문장이 관찰 기록에 남는다. 두 번째 원숭이손은 전날 밤 가장 높은 칸을 겨냥한다. 발화 예산 대가는 없앤다.

**Architecture:** 소원은 시나리오 표 `ScenarioBundleDTO.paw_wishes`(데이터)다. 수락하면 보이는 규칙 1개(`source="monkey_paw"`, 소원 장면)와 숨은 규칙 N개(`source="paw_effect"`, 마지막 규칙에 `hidden_side_effect`=관찰 문장)가 판 단위로 저장된다. 소원 장면·반대 사건은 전부 기존 **잠재 행동 + enforce/suppress 규칙**으로 표현하고, 새 엔진 개념은 5개뿐이다: ① `PawWishDTO`/`PawRuleDTO` ② `SceneActionDTO.paw_only`(신의 개입 후보 제외) ③ `SceneActionDTO.world_effect`(실행 시 전략 표로 세계 상태 변경, 새 관찰일 때 1회) ④ 수락 즉시 장면 ⑤ 부작용 관찰 문장 공개 조건. 규칙 선택은 순수 함수 `choose_wish`, 제안 문구만 관리자 모델(`make_paw_reason`)이 쓴다.

**Tech Stack:** FastAPI + SQLAlchemy(`backend/.venv`), Pydantic DTO, FakeLLM, Next.js(TypeScript).

**Spec:** `docs/superpowers/specs/2026-09-16-coherence-chain-design.md` §3 (유일한 기준)

**검토 등급:** B(게임 로직)

## Global Constraints

- 출현(유지): 1회차 2비트 무조건 1회. 2회차 이후 전날 밤 총점 40% 이상이면 그날 1회. 판당 최대 2(제안 시 `paw_offered_count` 증가 — 현행 유지). 거절은 무비용. 같은 판 2회 연속 거절 시 더 나오지 않는다.
- 금지: 정보원 제거, 발화 침묵, UI·예산 대가. 어떤 경로에서도 `budget_left`가 소원 때문에 줄지 않는다.
- 규칙은 판 단위로 지속된다(기획서 5.5). 소원을 받은 뒤 모든 날에 소원 장면과 반대 사건이 반복된다.
- 시나리오 고유 명사·소원 키는 `adapter.py` 값으로만 존재한다. 엔진 코드는 키 이름을 모른다(1회차 고정 소원 = 표의 첫 소원).
- 타입/상태 분기는 표 데이터·전략 dict로. `isinstance` 금지.
- 소원 전용 행동 8개는 `action_vocab`에 넣지 않는다(`배급을 다 먹는다`는 이미 있음). DB 마이그레이션 없음(`RuleOrm.source` String(16)에 `paw_effect`).
- 시나리오 문장(소원 문구·서술·대사·캡션)은 스펙 초안 그대로, 코드 주석 `# 초안 — 시나리오 디렉터 확인 전`.
- 테스트: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests`. 기준선 604 passed / 1 failed(`test_guards.py::test_user_daily_limit_is_five` — 기존 실패, 무관).
- 서버 재기동 금지. 커밋 금지(사용자 지시 뒤).
- 편집 전 `grep -n`으로 줄 위치 확인(줄 번호는 적지 않는다 — F7·F2·F8 작업으로 계속 움직인다).

---

## File Structure

| 파일 | 책임 |
|---|---|
| `backend/apps/engine/app/dtos/scenario_dto.py` | `PawRuleDTO`·`PawWishDTO`, `ScenarioBundleDTO.paw_wishes`, `SceneActionDTO.paw_only`·`world_effect` |
| `backend/apps/engine/app/dtos/event_log_dto.py` | `MonkeyPawOfferEvent.wish_key`(이미 제안한 소원 추적) |
| `backend/apps/scenarios/scenario_a/adapter.py` | 소원 4종, `paw_only` 잠재 행동 9개, 조건부 대사 4개, 민석 `question_replies` ③ 변형 |
| `backend/apps/engine/domain/entities/paw_rules.py` (신규) | 순수: `choose_wish`(최고 칸 겨냥·동점·소진) |
| `backend/apps/engine/domain/entities/cookie_rules.py` | `paw_should_offer(..., consecutive_declines)` |
| `backend/apps/engine/domain/value_objects/game_constants.py` | `PAW_DECLINE_LIMIT = 2` |
| `backend/apps/engine/app/use_cases/scene_execution.py` | paw-cost 제거, 부작용 관찰 문장 공개 조건, 새로 일어난 행동 콜백(`on_action`) |
| `backend/apps/engine/app/use_cases/loop_interactor.py` | `_maybe_offer_paw`(표·겨냥), `respond_paw`(규칙 저장·수락 즉시 장면·응답 확장), 세계 효과 전략 표, `active_rules`에서 숨은 규칙 제외 |
| `backend/apps/engine/app/use_cases/manager_interactor.py`, `prompts.py`, `llm_output_dto.py` | `make_paw` → `make_paw_reason`(제안 문구만) |
| `backend/apps/engine/app/use_cases/inspector_interactor.py` | `paw_rules` 필터에 `paw_effect` 포함 |
| `backend/apps/engine/dependencies/engine_dependency.py` | `rule_templates(bundle)` 추출, `paw_only` 제외 |
| `docs/spec/api_contract.md` | `paw_offer.rule_label`=소원 문장, `respond_paw` 응답 확장, `rules[].source`에 `paw_effect`, 예산 대가 문장 삭제 |
| `frontend/contracts/api.ts` | `PawRespondRes` 확장, `HarnessRes.rules[].source`에 `paw_effect` |
| `frontend/components/Retrospective.tsx` | `SOURCE_LABEL.paw_effect` 한 줄(타입 확장에 따른 필수 변경) |
| `frontend/lib/imageMap.ts` | Q02·Q03·Q04(v2)·Q06·Q08 등록(재작성 필요 이미지 미등록) |
| `frontend/components/GameplayGuide.tsx` | 원숭이손 대가 문장 교체 |
| `frontend/components/screens/DayScreen.tsx`, `frontend/tests/five-loop-flow.cjs` | 수락 즉시 장면 표시·헤드리스 기대 (Task 9) |

---

### Task 1: DTO — 소원 표·`paw_only`·`world_effect`·제안 이벤트 키

**Files:**
- Modify: `backend/apps/engine/app/dtos/scenario_dto.py`, `backend/apps/engine/app/dtos/event_log_dto.py`
- Test: `backend/tests/pure/test_scenario_dto_paw.py` (신규)

**Interfaces (Produces):**

```python
class PawRuleDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str
    action: str
    effect: Literal["suppress", "enforce"]
    beat: int = Field(ge=1, le=6)


class PawWishDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    label: str                      # 팝업 소원 문장
    default_reason: str             # make_paw_reason 실패 시 제안 문구
    target_cell: Literal["cause", "motive", "identity"]   # 부작용 칸은 겨냥 대상이 아니다
    reveal: PawRuleDTO              # 보이는 규칙(소원 장면)
    effects: list[PawRuleDTO] = Field(min_length=1)       # 숨은 규칙(반대 사건), 마지막이 관찰 문장 비트
    observation: str                # 부작용 관찰 문장 = 채점 주장 원문
```

- `SceneActionDTO.paw_only: bool = False`, `SceneActionDTO.world_effect: Literal["flag_actor", "rumor"] | None = None`
- `ScenarioBundleDTO.paw_wishes: list[PawWishDTO] = Field(default_factory=list)`
- `MonkeyPawOfferEvent.wish_key: str | None = None`

- [x] **Step 1: 실패 테스트** — `PawWishDTO`가 `effects=[]`와 `effect="silence"`를 거부, `target_cell="side_effect"` 거부, `SceneActionDTO` 기본값 `paw_only=False`·`world_effect=None`, `world_effect="rumor"` 허용.
- [x] **Step 2: 실패 확인** — ImportError `PawWishDTO`
- [x] **Step 3: 구현** — 위 인터페이스 추가(`SceneDialogueActionDTO` 위)
- [x] **Step 4: 통과 확인**

---

### Task 2: 시나리오 — 소원 4종·잠재 행동 9개·조건부 대사·민석 변형 답

**Files:**
- Modify: `backend/apps/scenarios/scenario_a/adapter.py` (dormant 블록 끝, `scene_dialogues` 각 비트 기본 대사 앞, 민석 `question_replies` 맨 앞, `paw_wishes=` 새 인자)
- Test: `backend/tests/engine/test_scenario_paw.py` (신규)

**데이터(스펙 §3 초안 그대로):**

| 소원 | reveal | effects (순서 = 실행 순서) | target_cell |
|---|---|---|---|
| `chaeyeon-honest` | enforce 채연 `속마음을 말한다` @2 | suppress 채연 `배급을 남긴다` @3 → enforce 채연 `배급을 다 먹는다` @3 → enforce 은상 `담요를 두른다` @5 | motive |
| `checkup-record` | enforce 채연 `검진 결과를 듣는다` @4 | enforce 채연 `밤에 기침한다` @6 | cause |
| `broadcast-room` | enforce 민석 `방송실에서 은상 얘기를 한다` @2 | suppress 민석 `기록한다` @3 → enforce 민석 `수첩을 덮어 둔다` @3 | motive |
| `band-meaning` | enforce 준 `번호를 맞춰 본다` @2 | enforce 은상 `번호 소문을 낸다` @5 | identity |

잠재 행동(`dormant=True, paw_only=True`, 목격자·세계 효과·삽화):
- 채연 `속마음을 말한다` @2 목격 준, Q03 / 채연 `배급을 다 먹는다` @3 목격 민석 / 은상 `담요를 두른다` @5 목격 준, `flag_actor`, Q02
- 채연 `검진 결과를 듣는다` @4, clue-03 / 채연 `밤에 기침한다` @6 목격 은상·준, `flag_actor`
- 민석 `방송실에서 은상 얘기를 한다` @2 목격 없음, Q04 / 민석 `수첩을 덮어 둔다` @3 목격 채연, Q06
- 준 `번호를 맞춰 본다` @2 목격 은상 / 은상 `번호 소문을 낸다` @5 목격 민석, `rumor`, `known_source`, Q08

조건부 대사(각 비트 기본 대사 앞): ①@3 채연 `배급을 다 먹는다`, ③@3 민석 `수첩을 덮어 둔다`, ④@5 은상 `번호 소문을 낸다`+민석 `방송실에 간다`, ②@6 채연 `밤에 기침한다`.
민석 `question_replies` 맨 앞: `required_actions=[(2, 민석, 방송실에서 은상 얘기를 한다)]`.

- [x] **Step 1: 실패 테스트**

```python
def test_paw_wish_table_is_backed_by_scene_actions():
    bundle = build().bundle()
    assert [w.key for w in bundle.paw_wishes] == ["chaeyeon-honest", "checkup-record", "broadcast-room", "band-meaning"]
    assert [w.target_cell for w in bundle.paw_wishes] == ["motive", "cause", "motive", "identity"]
    actions = {(a.beat, a.actor, a.action): a for a in bundle.scene_actions}
    for wish in bundle.paw_wishes:
        for rule in [wish.reveal, *wish.effects]:
            action = actions[(rule.beat, rule.actor, rule.action)]
            # enforce 대상은 소원 전용 잠재 행동, suppress 대상은 평소 행동
            assert (action.paw_only and action.dormant) == (rule.effect == "enforce")
        assert all(e.beat > wish.reveal.beat >= 2 for e in wish.effects)
        assert wish.effects[-1].beat == max(e.beat for e in wish.effects)

def test_paw_only_actions_stay_out_of_vocab():  # 9개, 새 행동 8개는 어휘에 없다
def test_world_effects_are_on_counter_events():  # 은상 담요 flag_actor, 채연 기침 flag_actor, 은상 번호 소문 rumor
def test_wish_dialogues_precede_default_dialogue_of_their_beat():
```

- [x] **Step 2: 실패 확인** — `paw_wishes` 비어 있음
- [x] **Step 3: 시나리오 작성** — 위 표. 새 문장 전부 `# 초안 — 시나리오 디렉터 확인 전` 주석. `suppressed_narration`은 잠재 행동이라 실행되지 않으므로 `""`.
- [x] **Step 4: 통과 확인** + 전체 스위트(잠재 행동 수·대사 순서를 고정한 기존 테스트 확인)

---

### Task 3: 조립 — `rule_templates`에서 `paw_only` 제외

**Files:**
- Modify: `backend/apps/engine/dependencies/engine_dependency.py` (`get_intervention_interactor`의 인라인 목록 → `rule_templates(bundle)` 함수)
- Test: `backend/tests/engine/test_scenario_paw.py`

- [x] **Step 1: 실패 테스트** — `rule_templates(build().bundle())`의 `(target, action)`에 `paw_only` 행동이 없고, 평소·기존 잠재 행동(`따라간다` 등)은 있다.
- [x] **Step 2: 실패 확인** — ImportError
- [x] **Step 3: 구현** — 기존 목록식을 함수로 옮기고 `if not opportunity.paw_only` 조건 추가
- [x] **Step 4: 통과 확인**

---

### Task 4: 순수 규칙 — `choose_wish`, 연속 거절

**Files:**
- Create: `backend/apps/engine/domain/entities/paw_rules.py`
- Modify: `cookie_rules.py`(`paw_should_offer`), `game_constants.py`(`PAW_DECLINE_LIMIT = 2`)
- Test: `backend/tests/pure/test_paw_rules.py` (신규)

**Interfaces:**

```python
TARGET_DEPTH = ("identity", "motive", "cause")  # 7.1 깊이 순 — 동점이면 깊은 칸

def choose_wish(loop_n: int, prev_cells: dict[str, float] | None, wishes: list, used_keys: set[str]):
    """1회차: 표의 첫 미사용 소원. 이후: 부작용 칸을 뺀 세 칸을 (점수 내림차순, 깊이) 순으로 훑어
    그 칸을 겨냥하는 첫 미사용 소원. 모두 소진이면 None."""

def paw_should_offer(loop_n, yesterday_score, offered_so_far, consecutive_declines: int = 0) -> bool
```

- [x] **Step 1: 실패 테스트** — 1회차 첫 소원 / 원인 최고 → `checkup-record` / 동기 최고·첫 소원 사용 → `broadcast-room` / 정체 최고 → `band-meaning` / 동점 → 깊은 칸(정체) / 부작용 칸 최고는 무시 / 최고 칸 소진 → 다음 칸 / 전부 소진 → None / `paw_should_offer(3, 60, 1, consecutive_declines=2)` False
- [x] **Step 2: 실패 확인**
- [x] **Step 3: 구현**
- [x] **Step 4: 통과 확인** (+ `test_domain_p2p5.py::test_paw_conditions` 유지)

---

### Task 5: 장면 실행 — 예산 대가 제거, 부작용 관찰 문장 공개 조건, 새 행동 콜백

**Files:**
- Modify: `backend/apps/engine/app/use_cases/scene_execution.py`
- Test: `backend/tests/pure/test_review_failure_boundaries.py`(옛 paw-cost 테스트 2개 교체), `backend/tests/pure/test_paw_scene_execution.py` (신규), 예산 대가를 기대하던 `test_connected_investigation.py`·`test_scene_transaction.py` 기대값 갱신

**Interfaces:**
- `PAW_EFFECT_SOURCE = "paw_effect"`
- `execute_scene(event_log, loop, bundle, rules, on_action=None)` — `on_action(opportunity)`은 행동이 억제되지 않고 **그 행동 관찰이 이번 호출에서 처음 생겼을 때만** 호출된다(재실행 중복 방지).
- 규칙 실행 결과를 `outcomes[(rule_id, beat)] = (result, actual_action)`로 누적. `paw_effect` 규칙이 `hidden_side_effect`를 갖고 obeyed이면, 그 문장을 가진 소원의 `effects` 전부가 그날 의도대로(`_INTENDED_ACTION = {"enforce": 행동명, "suppress": None}`, result `obeyed`) 실행됐는지 확인 → 맞으면 `paw-effect-{beat}-{rule_id}` 키로 `rule_result` 관찰 공개, 서술에 덧붙이고 `RuleExecutionEvent.side_effect`에 기록.

- [x] **Step 1: 실패 테스트**
  - 옛 설명 규칙(`monkey_paw` + `알고 있는 관찰을 설명한다`) 두 개 → 설명 1회, `budget_left` 불변, side_effect 없음
  - `on_action`이 같은 비트를 두 번 실행해도 1회만 호출된다
  - ① 숨은 규칙 3개를 저장한 가짜 규칙 목록으로 비트 3·5 실행 → 비트 5에서 관찰 문장 1건, side_effect 1건
  - 같은 조건 + 플레이어 규칙 채연 `배급을 남긴다` enforce @3(나중 규칙) → 관찰 문장 없음, side_effect 전부 None
- [x] **Step 2: 실패 확인**
- [x] **Step 3: 구현** — `shared_costs`·`cost_key`·paw-cost 블록 삭제, 위 조건 추가
- [x] **Step 4: 통과 확인** + `test_connected_investigation.py::test_paw_benefit_and_cost_occur_in_linked_scene_only`는 Task 6에서 새 기대로 교체

---

### Task 6: 제안·수락 — `_maybe_offer_paw`, `respond_paw`, 세계 효과, 관리자 문구

**Files:**
- Modify: `loop_interactor.py`, `manager_interactor.py`, `prompts.py`(`MANAGER_PAW_ADDENDUM`), `llm_output_dto.py`(`ManagerPawOutput` → `shown_reason`만)
- Test: `backend/tests/engine/test_paw_wishes.py` (신규), `test_connected_investigation.py`(옛 paw 테스트 교체)

**Interfaces:**
- `ManagerInteractor.make_paw_reason(wish) -> tuple[str | None, report]` — 소원 문장을 받고 싶게 만드는 한 문장. 부작용은 말하지 않는다. 실패 시 `None` → `wish.default_reason`.
- `loop.pending_paw = {"offer_id", "offer_index", "wish_key", "label", "shown_reason", "show_reason"}`
- 제안 응답(현행 유지): `{"offer_id", "rule_label": wish.label, "shown_reason": str|None}`
- `MonkeyPawOfferEvent(..., wish_key=wish.key)` — 수락·거절 모두 기록. 이미 제안한 키 = 이벤트의 `wish_key` 집합. 연속 거절 = 이벤트 끝에서부터 `accepted=False` 개수.
- `respond_paw(loop_id, offer_id, accept)` — `scene_transaction(loop_id)` 안에서 실행. 수락 시:
  - 보이는 규칙: `source="monkey_paw"`, `reveal`의 target/action/effect/beat, `shown_reason`(A/B), `hidden_side_effect=None`, `RuleAppliedEvent` 1건
  - 숨은 규칙: `effects`마다 `source="paw_effect"`, 마지막에만 `hidden_side_effect=wish.observation`
  - 수락 즉시 장면: `reveal.beat == loop.beat`면 `execute_scene`·`_disclose_scene`를 현재 비트로 다시 돌리고 새로 생긴 관찰만 응답에 싣는다
  - 응답: `{"applied", "rule_label", "narration": str|None, "illustrations": [...], "observations": [...]}`
- 세계 효과 전략 표: `_WORLD_EFFECTS = {"flag_actor": 행위자 flagged_abnormal=True, "rumor": loop.rumor_index += 1}`, 없으면 무효과. `start_loop`·`advance_beat`·수락 즉시 장면의 `execute_scene`에 `on_action`으로 넘긴다.
- `start_loop` 응답 `active_rules`에서 `paw_effect` 규칙 제외(숨은 규칙은 플레이어에게 보이지 않는다).

- [x] **Step 1: 실패 테스트** (`test_paw_wishes.py`)
  - 1회차 제안 문구가 ① 소원 문장, `shown_reason`=기본 문구
  - ① 수락: 규칙 4개(보이는 1·숨은 3), 관찰 문장은 마지막 숨은 규칙에만. 수락 응답에 소원 서술·Q03·새 관찰, `scene-2` 관찰·노트 중복 없음. 비트 3 반대 사건+조건부 대사 선행, 비트 5 관찰 문장 1건·노트·은상 `flagged_abnormal`. 전 과정 `budget_left` 불변. `active_rules`에 숨은 규칙 없음. 다음 회차에도 소원 장면(2비트 평소 흐름)·관찰 문장 반복
  - ② 수락: 비트 4 기록 장면(clue-03), 비트 6 기침·관찰 문장·채연 `flagged_abnormal`·조건부 대사
  - ③ 수락: 즉시 장면(Q04), 비트 3 기록 억제·덮인 수첩·관찰 문장·조건부 대사, 보고 질문 규칙이 있으면 민석이 ③ 변형 답
  - ④ 수락: 즉시 장면, 비트 5 번호 소문·`rumor_index` +1·관찰 문장·조건부 대사
  - 안 받은 판: 소원 장면·반대 사건·관찰 문장 없음, 민석 보고 답은 기존 답
  - 겨냥 통합: 2회차 전날 `answer_scored` 원인 최고 → ② 제안 / 2회 연속 거절 뒤 미출현 / 전부 소진이면 미출현·`paw_offered_count` 불변
  - 신의 질문: ① 수락 판 관찰로 "채연이 밥에서 소독약 냄새가 난다고 했어?" → 검색 문맥에 소원 관찰 포함, supported 근거 인용 시 `맞다.` / "배급이 오염됐어?" unknown → `그건 알 수 없다.`
- [x] **Step 2: 실패 확인**
- [x] **Step 3: 구현**
- [x] **Step 4: 통과 확인** + 전체 스위트

---

### Task 7: 인스펙터·계약 문서

**Files:**
- Modify: `inspector_interactor.py`(`paw_rules` 필터 `in ("monkey_paw", "paw_effect")`), `docs/spec/api_contract.md`
- Test: `backend/tests/engine/test_paw_wishes.py`

- [x] **Step 1: 실패 테스트** — 수락 판의 `inspector_view(...)["paw_rules"]`에 `paw_effect` 규칙과 `hidden_side_effect`가 있다
- [x] **Step 2: 구현·통과**
- [x] **Step 3: 계약 문서** — `paw_offer.rule_label`=소원 문장, `respond_paw` 응답 확장, `rules[].source`에 `paw_effect`, 예산 대가·옛 설명 중복 문장 교체

---

### Task 8: 프론트(충돌 없는 파일) — 계약 타입·삽화 등록·안내 문장

**Files:**
- Modify: `frontend/contracts/api.ts`, `frontend/components/Retrospective.tsx`(라벨 한 줄), `frontend/lib/imageMap.ts`, `frontend/components/GameplayGuide.tsx`

- [x] **Step 1:** `PawRespondRes`에 `narration: string | null; illustrations: Illustration[]; observations: Observation[]`, `HarnessRes.rules[].source`에 `"paw_effect"`, `SOURCE_LABEL.paw_effect`
- [x] **Step 2:** `CLUE_IMAGES`에 `Q02-evening-four-trays-v1`, `Q03-eunsang-silent-corner-v1`, `Q04-minseok-reports-eunsang-v2`, `Q06-notebook-closed-v1`, `Q08-eunsang-at-jun-bunk-v1`. Q05·Q07 미등록(보관), 신규 Q09~Q11은 파일이 나오면 등록
- [x] **Step 3:** 안내 문장 — "특별한 규칙의 대가로 그날의 대화 횟수가 더 줄어들 수 있다."를 대가 내용을 밝히지 않는 문장으로 교체하고, 받은 규칙이 남은 모든 날에 걸린다는 한 줄 추가(`gameplay-clarity.cjs`가 찾는 "특별한 규칙의 대가" 구절 유지)
- [x] **Step 4:** `cd frontend && npx tsc --noEmit` — 다른 작업의 진행 중 오류와 구분해 기록

---

### Task 9: 프론트 소원 장면 표시·헤드리스 — 완료 (2026-09-17)

**Files:**
- Modify: `frontend/components/screens/DayScreen.tsx`, `frontend/tests/five-loop-flow.cjs`

- [x] **Step 1:** `DayScreen.tsx`의 `respondPaw` 성공 처리에서 `res.narration`이 있으면 현재 비트 화면의 서술 뒤에 덧붙이고, `res.illustrations`를 현재 비트 삽화에 추가, `res.observations`를 관찰 목록에 병합(수락 즉시 장면). 거절·뒤 비트 소원이면 응답 필드가 비어 변화 없음
- [x] **Step 2:** `five-loop-flow.cjs` 모의 응답(1회차에만 2·3비트를 거친다. 원래 테스트에 원숭이손 경로가 없어 새로 넣었다) — 2비트 `paw_offer.rule_label`을 "채연이 오늘은 밥을 왜 안 먹는지 솔직하게 말한다.", `/paw/respond` 응답에 소원 서술·`illustrations:[{image_id:"Q03",...}]`, 3비트 응답에 반대 사건 서술("쟁반이 빈다"). 팝업 문구·수락 뒤 소원 서술·Q03 이미지(`img[src$="Q03-eunsang-silent-corner-v1.png"]`)·3비트 서술 기대 추가
- [x] **Step 3:** `npx tsc --noEmit`; 헤드리스를 **한 번에 하나씩** `five-loop-flow.cjs` → `gameplay-clarity.cjs` → `npc-followup.cjs` → `scene-illustrations.cjs`
- [x] **Step 4:** `run_npc_dialogue_check.py --dry-run`(가짜 Manager에 `make_paw_reason` 추가 필요했음) 통과, 원숭이손 5회차 사슬은 임시 FakeLLM 스크립트로 확인(①·② 제안, 3~5회차 반복, 부작용 주장 1→2건, 은상·채연 이상자, 예산 불변). 러너 dry-run으로 5회차 사슬에서 원숭이손 제안·반대 사건·부작용 주장 생성 확인, 결과를 `docs/model_evaluation.md` 규칙대로 기록할지 컨트롤러가 결정
