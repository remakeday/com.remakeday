# F11 원숭이손 소원 표 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기획서 5.7의 원숭이손을 구현한다 — 소원 4종이 세계 규칙으로 걸리고, 같은 날 뒤 비트에 숨은 부작용 분기가 실제 사건으로 일어나 관찰 기록에 남으며, 두 번째 원숭이손은 전날 밤 최저 칸을 겨냥한다. 발화 예산 감소 대가는 없앤다.

**Architecture:** 소원은 시나리오의 `paw_wishes` 표(작성 데이터)다. 수락하면 규칙 두 개가 걸린다: 보이는 규칙(소원)과 숨은 규칙(부작용, `source="paw_effect"`). 부작용 분기는 기존 잠재 행동(dormant scene action) 메커니즘으로 표현하므로 `execute_scene`가 그대로 실행하고 `rule_execution.side_effect`에 관찰 문장을 남겨 채점 주장이 자동 생성된다. 새 엔진 개념은 둘뿐: 규칙이 걸린 날만 나오는 고정 대사(`required_rules`), 발화 침묵(`effect="silence"`).

**Tech Stack:** FastAPI + SQLAlchemy(`backend/.venv`), Pydantic DTO, FakeLLM, Next.js + Playwright 헤드리스.

**Spec:** `docs/superpowers/specs/2026-09-16-coherence-chain-design.md` §3

## Global Constraints

- 출현: 1회차 2비트 무조건 1회. 2회차 이후 전날 밤 총점 **40% 이상**이면 그날 1회. 판당 최대 2. 거절은 무비용, 같은 판 2회 연속 거절 시 더 나오지 않는다.
- 부작용은 관찰 기록에 남는 사건이어야 한다. UI·예산을 건드리는 대가는 금지.
- 규칙은 판 단위로 지속된다(기획서 5.5). 원숭이손 규칙도 같다.
- 관리자 생성기(`make_paw`)는 제안 문구(`shown_reason`)만 쓴다. 규칙 선택은 코드. 실패 시 표의 기본 문구.
- DB 마이그레이션 없음: `RuleOrm.source`(String 16)에 `"paw_effect"`, `effect`(String 10)에 `"silence"`는 길이 안에 든다.
- 테스트: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests`. 서버 재기동 금지. 커밋은 사용자 지시 뒤.
- 줄 번호는 2026-09-16 14:00 기준. 특히 `adapter.py`는 F8·F7 작업으로 이동하므로 편집 전 `grep -n`.
- 소원 4종의 서술·대사·삽화 ID는 설계 문서 §3 초안이며 **시나리오 디렉터 확정본이 오면 그 문장으로 교체**한다. 구조는 동일.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `backend/apps/engine/app/dtos/scenario_dto.py` | `PawWishDTO`, `SceneDialogueDTO.required_rules`, `ScenarioBundleDTO.paw_wishes` |
| `backend/apps/scenarios/scenario_a/adapter.py` | 소원 4종 + 부작용 잠재 행동 4개 + 소원 조건부 대사 + 삽화 ID |
| `backend/apps/engine/domain/entities/cookie_rules.py:11-18` | `paw_should_offer`에 연속 거절 인자 |
| `backend/apps/engine/domain/entities/paw_rules.py` (신규) | 순수: 최저 칸 → 소원 키, 연속 거절 계산 |
| `backend/apps/engine/app/use_cases/loop_interactor.py:639-703` | `_maybe_offer_paw`·`respond_paw` 재작성, `_make_ambient` required_rules, `_utter` 침묵 |
| `backend/apps/engine/app/use_cases/scene_execution.py:77-89` | 예산 감소 대가 제거, `paw_effect` 규칙의 `side_effect` 문장 기록 |
| `backend/apps/engine/app/use_cases/manager_interactor.py:37-61` | `make_paw` → 제안 문구만 |
| `frontend/lib/imageMap.ts` | Q군 삽화 ID 매핑 |
| `frontend/tests/five-loop-flow.cjs` | 원숭이손 팝업·부작용 서술 기대 |

---

### Task 1: DTO — `PawWishDTO`, `required_rules`, `paw_wishes`

**Files:**
- Modify: `backend/apps/engine/app/dtos/scenario_dto.py:168-175` (`SceneDialogueDTO`), `ScenarioBundleDTO`
- Test: `backend/tests/pure/test_scenario_dto_paw.py` (신규)

**Interfaces:**
- Produces:

```python
class PawEffectDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str
    action: str          # 잠재 행동 이름 (scene_actions에 dormant로 존재해야 한다)
    beat: int = Field(ge=1, le=6)
    observation: str     # rule_execution.side_effect 문장 = 채점 주장 원문


class PawWishDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    target: str
    action: str
    effect: Literal["suppress", "enforce", "silence"]
    when_beat: int | None = None
    label: str                    # 팝업에 뜨는 세계 안 문장
    default_reason: str           # make_paw 실패 시 shown_reason
    target_cell: Literal["cause", "motive", "identity", "side_effect"]
    effects: list[PawEffectDTO] = Field(min_length=1)
    extra_rules: list[dict] = Field(default_factory=list)  # {"action":..., "effect":...} 같은 target에 함께 거는 보이는 규칙 (예: 침묵 + 소문 억제)
```

- `SceneDialogueDTO.required_rules: list[SceneDialogueActionDTO] = Field(default_factory=list)` — `(actor→target, action)`이 그날 활성 규칙에 있어야 재생
- `ScenarioBundleDTO.paw_wishes: list[PawWishDTO] = Field(default_factory=list)`

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/pure/test_scenario_dto_paw.py
import pytest
from apps.engine.app.dtos.scenario_dto import PawWishDTO, PawEffectDTO, SceneDialogueDTO, SceneDialogueLineDTO, SceneDialogueActionDTO


def test_paw_wish_requires_one_effect():
    with pytest.raises(ValueError):
        PawWishDTO(key="k", target="채연", action="검진을 받는다", effect="suppress", label="l",
                   default_reason="r", target_cell="motive", effects=[])
    wish = PawWishDTO(key="k", target="채연", action="검진을 받는다", effect="suppress", label="l",
                      default_reason="r", target_cell="motive",
                      effects=[PawEffectDTO(actor="은상", action="담요를 두른다", beat=5, observation="o")])
    assert wish.effects[0].beat == 5


def test_dialogue_accepts_required_rules():
    d = SceneDialogueDTO(beat=2, required_rules=[SceneDialogueActionDTO(actor="은상", action="말을 하지 않는다")],
                         lines=[SceneDialogueLineDTO(code="jun", text="은상아, 왜 말 안 해?"),
                                SceneDialogueLineDTO(code="minseok", text="이상하네. 알려야 하나.")])
    assert d.required_rules[0].actor == "은상"
```

- [ ] **Step 2: 실패 확인** — ImportError `PawWishDTO`
- [ ] **Step 3: 구현** — 위 인터페이스 코드를 `scenario_dto.py`에 추가(`SceneDialogueDTO` 위에 `PawEffectDTO`·`PawWishDTO`, `SceneDialogueDTO`에 `required_rules`, `ScenarioBundleDTO`에 `paw_wishes`). `Literal` import 확인.
- [ ] **Step 4: 통과 확인** — 2 passed

---

### Task 2: 시나리오 — 소원 4종·부작용 잠재 행동·조건부 대사

**Files:**
- Modify: `backend/apps/scenarios/scenario_a/adapter.py` (scene_actions dormant 블록, scene_dialogues, 새 `paw_wishes=`, action vocabulary)
- Test: `backend/tests/engine/test_scenario_paw.py` (신규)

**Interfaces:**
- Produces: `bundle.paw_wishes` 4개(키 `skip-checkup`, `mute-eunsang`, `deaf-minseok`, `sleep-jun`); 각 `effects[].action`은 `scene_actions`에 dormant로 존재; 삽화 ID는 `clue-02`(소원 skip-checkup), `Q02`~`Q08`.

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/engine/test_scenario_paw.py
from apps.scenarios.scenario_a.adapter import build


def test_paw_wishes_are_backed_by_dormant_actions_and_vocab():
    bundle = build().bundle()
    scenario = build()
    dormant = {(a.actor, a.action) for a in bundle.scene_actions if a.dormant}
    vocab = set(scenario.action_vocabulary())
    keys = [w.key for w in bundle.paw_wishes]
    assert keys == ["skip-checkup", "mute-eunsang", "deaf-minseok", "sleep-jun"]
    for wish in bundle.paw_wishes:
        assert wish.action in vocab, wish.key
        for effect in wish.effects:
            assert (effect.actor, effect.action) in dormant, (wish.key, effect.action)
            assert effect.beat > 2  # 원숭이손은 2비트에 온다 — 부작용은 그 뒤


def test_wish_conditional_dialogue_exists_for_mute_eunsang():
    bundle = build().bundle()
    conditional = [d for d in bundle.scene_dialogues if d.required_rules]
    assert any(r.actor == "은상" and r.action == "말을 하지 않는다" for d in conditional for r in d.required_rules)
```

- [ ] **Step 2: 실패 확인** — AttributeError `paw_wishes` 비어 있음
- [ ] **Step 3: 시나리오 작성**

행동 어휘(`adapter.py` ~487-506)에 추가: `"검진을 받는다"`(있으면 생략), `"말을 하지 않는다"`, `"방송을 듣지 못한다"`, `"하루 종일 잔다"`, `"담요를 두른다"`, `"은상 얘기를 하러 간다"`, `"채연에게 묻는다"`, `"출처를 말하지 못한다"`.

`scene_actions` dormant 블록 끝에 부작용 잠재 행동 4개:

```python
            # ── 원숭이손 부작용 분기 (paw_effect 규칙이 걸린 날에만) ──
            SceneActionDTO(beat=5, actor="은상", action="담요를 두른다", witnesses=["준"], dormant=True,
                narration="저녁 쟁반이 넷 남았다. 은상도 담요를 벗지 않는다.",
                explanation="좀 추워서. 그냥 그래.",
                suppressed_narration="은상은 담요를 두르지 않는다.",
                illustrations=[IllustrationDTO(image_id="Q02", caption="저녁에 음식이 남은 쟁반이 넷 놓여 있다.")]),
            SceneActionDTO(beat=5, actor="민석", action="은상 얘기를 하러 간다", witnesses=["준"], dormant=True,
                narration="민석이 은상이 이상하다고 방송실 문 앞까지 간다.",
                explanation="은상이 하루 종일 말을 안 했잖아. 이상한 건 알리랬어.",
                suppressed_narration="민석은 방송실 쪽으로 가지 않았다.",
                illustrations=[IllustrationDTO(image_id="Q04", caption="민석이 방송실 문 앞에 서 있고, 구석에 은상이 담요를 두르고 있다.")]),
            SceneActionDTO(beat=3, actor="민석", action="채연에게 묻는다", witnesses=["채연"], dormant=True,
                narration="민석이 수첩을 덮어 둔 채 채연에게 무엇을 남겼는지 묻는다.",
                explanation="방송을 못 들어서. 뭘 적어야 하는지 몰라서 물어봤어.",
                suppressed_narration="민석은 채연에게 묻지 않는다.",
                illustrations=[IllustrationDTO(image_id="Q06", caption="덮인 수첩 옆에서 민석이 채연 쪽으로 몸을 기울인다.")]),
            SceneActionDTO(beat=5, actor="은상", action="출처를 말하지 못한다", witnesses=["민석"], dormant=True,
                narration="은상이 누구에게 들었는지 말하지 못한다. 준은 아직 자고 있다.",
                explanation="누가 그랬더라. 준이 자니까 물어볼 수가 없어.",
                suppressed_narration="은상은 출처를 말한다.",
                illustrations=[IllustrationDTO(image_id="Q08", caption="은상이 준의 침상 앞에 서서 담요 덩어리를 내려다본다.")]),
```

소원 장면 삽화는 소원 규칙이 억제하는 기존 행동의 `suppressed_narration` 옆에 붙일 수 없으므로(억제 시 삽화 없음), 소원 서술도 잠재 행동으로 둔다:

```python
            SceneActionDTO(beat=4, actor="채연", action="검진에서 지나쳐진다", witnesses=["은상"], dormant=True,
                narration="담당자가 채연 침상을 지나친다. 채연은 담요를 두른 채 그대로다.",
                explanation="안 봤어. 그냥 지나갔어.",
                suppressed_narration="",
                illustrations=[IllustrationDTO(image_id="clue-02", caption="검진 담당자가 채연 침상 앞을 지나친다.")]),
            SceneActionDTO(beat=2, actor="은상", action="입을 열지 않는다", witnesses=["준"], dormant=True,
                narration="은상이 구석 침상에 앉아 입을 열지 않는다.",
                explanation="……",
                suppressed_narration="",
                illustrations=[IllustrationDTO(image_id="Q03", caption="은상이 구석 침상에서 벽을 보고 앉아 있다.")]),
            SceneActionDTO(beat=1, actor="민석", action="방송을 흘려듣는다", witnesses=["준"], dormant=True,
                narration="방송이 나오는데 민석은 다른 쪽을 보고 있다.",
                explanation="뭐라고 했어? 못 들었어.",
                suppressed_narration="",
                illustrations=[IllustrationDTO(image_id="Q05", caption="스피커 불이 켜졌는데 한 사람만 등을 돌리고 있다.")]),
            SceneActionDTO(beat=2, actor="준", action="담요를 뒤집어쓰고 잔다", witnesses=["은상"], dormant=True,
                narration="준이 담요를 머리까지 덮고 잔다. 낮인데.",
                explanation="",
                suppressed_narration="",
                illustrations=[IllustrationDTO(image_id="Q07", caption="담요가 머리까지 덮여 사람 모양 덩어리만 있다.")]),
```

`paw_wishes=`(bundle 인자, `advisor_leads` 뒤):

```python
        paw_wishes=[
            PawWishDTO(key="skip-checkup", target="채연", action="검진을 받는다", effect="suppress", when_beat=4,
                label="오늘 검진은 채연을 보지 않는다.", target_cell="motive",
                default_reason="채연이 검진에서 벗어난다. 담요 아래에서 무슨 말을 하는지 들을 수 있다.",
                extra_rules=[{"action": "검진에서 지나쳐진다", "effect": "enforce"}],
                effects=[PawEffectDTO(actor="은상", action="담요를 두른다", beat=5,
                                      observation="검진이 채연을 건너뛴 날 저녁, 쟁반이 넷 남고 은상도 담요를 벗지 않았다.")]),
            PawWishDTO(key="mute-eunsang", target="은상", action="말을 하지 않는다", effect="silence", when_beat=None,
                label="은상은 오늘 말을 하지 않는다.", target_cell="cause",
                default_reason="소문이 멈춘다. 누가 무엇을 직접 봤는지 가려낼 수 있다.",
                extra_rules=[{"action": "소문을 낸다", "effect": "suppress"}, {"action": "입을 열지 않는다", "effect": "enforce"}],
                effects=[PawEffectDTO(actor="민석", action="은상 얘기를 하러 간다", beat=5,
                                      observation="은상이 말을 하지 않은 날 저녁, 민석이 은상이 이상하다고 방송실 문 앞까지 갔다.")]),
            PawWishDTO(key="deaf-minseok", target="민석", action="방송을 듣지 못한다", effect="enforce", when_beat=1,
                label="민석은 오늘 방송을 듣지 못한다.", target_cell="cause",
                default_reason="규칙을 모르는 민석이 어떻게 움직이는지 볼 수 있다.",
                extra_rules=[{"action": "방송을 흘려듣는다", "effect": "enforce"}, {"action": "기록한다", "effect": "suppress"}],
                effects=[PawEffectDTO(actor="민석", action="채연에게 묻는다", beat=3,
                                      observation="민석이 방송을 못 들은 날, 수첩에 적는 대신 채연에게 무엇을 남겼는지 물었다.")]),
            PawWishDTO(key="sleep-jun", target="준", action="하루 종일 잔다", effect="silence", when_beat=None,
                label="준은 오늘 하루 종일 잔다.", target_cell="identity",
                default_reason="준이 조용하면 다른 아이들이 준 없이 무엇을 말하는지 들을 수 있다.",
                extra_rules=[{"action": "손목띠를 만진다", "effect": "suppress"}, {"action": "담요를 뒤집어쓰고 잔다", "effect": "enforce"}],
                effects=[PawEffectDTO(actor="은상", action="출처를 말하지 못한다", beat=5,
                                      observation="준이 하루 종일 잔 날, 은상은 누구에게 들었는지 말하지 못했다.")]),
        ],
```

> `SceneActionDTO`가 빈 `suppressed_narration`을 허용하는지 확인(`grep -n suppressed_narration scenario_dto.py`). 필수 문자열이면 `"—"` 대신 실제 문장("채연은 검진을 받았다." 등)을 넣는다.

소원 조건부 대사(`scene_dialogues` 끝):

```python
            SceneDialogueDTO(beat=2,
                required_rules=[SceneDialogueActionDTO(actor="은상", action="말을 하지 않는다")],
                lines=[
                    SceneDialogueLineDTO(code="jun", text="은상아, 왜 말 안 해?"),
                    SceneDialogueLineDTO(code="minseok", text="이상하네. 알려야 하나."),
                ]),
            SceneDialogueDTO(beat=2,
                required_rules=[SceneDialogueActionDTO(actor="준", action="하루 종일 잔다")],
                lines=[
                    SceneDialogueLineDTO(code="eunsang", text="준아, 일어나 봐. 준아?"),
                    SceneDialogueLineDTO(code="minseok", text="낮인데 왜 자지. 아픈 건가."),
                ]),
```

- [ ] **Step 4: 통과 확인** — `PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_scenario_paw.py` → 2 passed. 이어서 전체 스위트 — 어휘·잠재 행동 추가로 깨지는 기존 테스트가 있으면 그 기대가 "잠재 행동 수"나 "어휘 목록"을 고정한 것인지 확인해 갱신.

---

### Task 3: 순수 규칙 — 소원 선택과 연속 거절

**Files:**
- Create: `backend/apps/engine/domain/entities/paw_rules.py`
- Modify: `backend/apps/engine/domain/entities/cookie_rules.py:11-18`
- Test: `backend/tests/pure/test_paw_rules.py`

**Interfaces:**
- Produces:
  - `choose_wish(loop_n: int, prev_cells: dict | None, wishes: list, used_keys: set[str]) -> wish | None` — loop 1 → `skip-checkup`; 그 외 `prev_cells` 최저 칸의 `target_cell` 소원(동률이면 표 순서), 이미 쓴 키 제외, 없으면 표 순서 첫 미사용
  - `paw_should_offer(loop_n, yesterday_score, offered_so_far, consecutive_declines: int = 0) -> bool` — `consecutive_declines >= 2`면 False

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/pure/test_paw_rules.py
from types import SimpleNamespace as NS
from apps.engine.domain.entities.paw_rules import choose_wish
from apps.engine.domain.entities.cookie_rules import paw_should_offer

W = [NS(key="skip-checkup", target_cell="motive"), NS(key="mute-eunsang", target_cell="cause"),
     NS(key="deaf-minseok", target_cell="cause"), NS(key="sleep-jun", target_cell="identity")]


def test_first_loop_is_fixed():
    assert choose_wish(1, None, W, set()).key == "skip-checkup"


def test_second_paw_targets_lowest_cell():
    cells = {"cause": 100.0, "motive": 83.3, "identity": 0.0, "side_effect": 0.0}
    assert choose_wish(3, cells, W, {"skip-checkup"}).key == "sleep-jun"  # side_effect는 소원 대상 아님 → identity


def test_used_keys_are_skipped_and_fallback_is_table_order():
    cells = {"cause": 0.0, "motive": 50.0, "identity": 50.0, "side_effect": 0.0}
    assert choose_wish(2, cells, W, {"mute-eunsang"}).key == "deaf-minseok"
    assert choose_wish(2, {"cause": 100.0, "motive": 100.0, "identity": 100.0, "side_effect": 0.0}, W,
                       {"skip-checkup", "mute-eunsang", "deaf-minseok"}).key == "sleep-jun"


def test_two_consecutive_declines_stop_offers():
    assert paw_should_offer(3, 60.0, 1, consecutive_declines=1)
    assert not paw_should_offer(3, 60.0, 1, consecutive_declines=2)
```

- [ ] **Step 2: 실패 확인** — ModuleNotFoundError / TypeError
- [ ] **Step 3: 구현**

```python
# backend/apps/engine/domain/entities/paw_rules.py
"""원숭이손 소원 선택 — 1회차 고정, 이후 전날 밤 최저 칸 겨냥 (기획서 5.7 '유혹')."""

_CELL_ORDER = ("cause", "motive", "identity")  # side_effect는 소원이 겨냥하지 않는다


def choose_wish(loop_n, prev_cells, wishes, used_keys):
    unused = [w for w in wishes if w.key not in used_keys]
    if not unused:
        return None
    if loop_n == 1:
        return next((w for w in unused if w.key == "skip-checkup"), unused[0])
    if prev_cells:
        lowest = min(_CELL_ORDER, key=lambda c: (prev_cells.get(c, 0.0), _CELL_ORDER.index(c)))
        for w in unused:
            if w.target_cell == lowest:
                return w
    return unused[0]
```

`cookie_rules.paw_should_offer`에 `consecutive_declines: int = 0` 인자를 추가하고 첫 줄에 `if consecutive_declines >= 2: return False`.

- [ ] **Step 4: 통과 확인** — 4 passed; `tests/engine/test_domain_p2p5.py::test_paw_conditions`도 통과 유지

---

### Task 4: 제안·수락 — `_maybe_offer_paw`·`respond_paw` 재작성

**Files:**
- Modify: `backend/apps/engine/app/use_cases/loop_interactor.py:639-703`, `manager_interactor.py:37-61`
- Test: `backend/tests/engine/test_usecase_day.py`

**Interfaces:**
- Consumes: `bundle.paw_wishes`, `choose_wish`, `paw_should_offer`, `self._loops.score_of`, 밤 셀 점수(`answer_scored` 이벤트 `cell_scores` — `self._events.query(attempt_id, loop_n=loop_n-1)`에서 `type=="answer_scored"`)
- Produces: `loop.pending_paw = {"offer_id", "offer_index", "wish_key", "label", "shown_reason", "show_reason"}`; 수락 시 규칙: 보이는 규칙 `source="monkey_paw"`(소원 본체 + `extra_rules`), 숨은 규칙 `source="paw_effect"`(effects마다 `enforce`, `hidden_side_effect=observation`), `RuleAppliedEvent`는 본체 1건만. `make_paw(wish)`는 `shown_reason` 문자열만 반환.

- [ ] **Step 1: 실패하는 테스트**

```python
def _cells(db_session, attempt, loop_n, cells):
    from apps.engine.app.dtos import event_log_dto as ev
    EventLogRepository(db_session).record(attempt.id, ev.AnswerScoredEvent(
        loop_n=loop_n, total=sum(cells.values()) / 4, passed=True, cell_scores=cells, per_truth_claim=[]))


def test_first_paw_is_skip_checkup_and_accept_adds_visible_and_hidden_rules(db_session):
    day, _, attempt, info = make_day(db_session, [])
    scene = day.advance_beat(info["loop_id"])
    offer = scene["paw_offer"]
    assert offer["rule_label"] == "오늘 검진은 채연을 보지 않는다."
    day.respond_paw(info["loop_id"], offer["offer_id"], True)
    rules = RuleRepository(db_session).list(attempt.id)
    assert {(r.source, r.target, r.action, r.effect) for r in rules} >= {
        ("monkey_paw", "채연", "검진을 받는다", "suppress"),
        ("monkey_paw", "채연", "검진에서 지나쳐진다", "enforce"),
        ("paw_effect", "은상", "담요를 두른다", "enforce"),
    }
    hidden = next(r for r in rules if r.source == "paw_effect")
    assert hidden.hidden_side_effect.startswith("검진이 채연을 건너뛴 날")


def test_second_paw_targets_lowest_cell(db_session):
    day, _, attempt, info = make_day(db_session, [])
    first = LoopRepository(db_session).get(info["loop_id"])
    first.state, first.score = "closed", 60
    db_session.commit()
    _cells(db_session, attempt, 1, {"cause": 100.0, "motive": 83.3, "identity": 0.0, "side_effect": 0.0})
    info = day.start_loop(attempt.id)
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    assert offer["rule_label"] == "준은 오늘 하루 종일 잔다."


def test_two_declines_end_offers_for_the_attempt(db_session):
    day, _, attempt, info = make_day(db_session, [])
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    day.respond_paw(info["loop_id"], offer["offer_id"], False)
    loop = LoopRepository(db_session).get(info["loop_id"]); loop.state, loop.score = "closed", 60; db_session.commit()
    info = day.start_loop(attempt.id)
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    assert offer is not None
    day.respond_paw(info["loop_id"], offer["offer_id"], False)
    loop = LoopRepository(db_session).get(info["loop_id"]); loop.state, loop.score = "closed", 60; db_session.commit()
    info = day.start_loop(attempt.id)
    assert day.advance_beat(info["loop_id"])["paw_offer"] is None
```

> `AnswerScoredEvent`의 정확한 필드는 `grep -n "class AnswerScoredEvent" -A 10 event_log_dto.py`로 맞춘다. 판당 최대 2 상한(`PAW_MAX_PER_ATTEMPT`)이 세 번째 테스트와 충돌하면 거절은 `paw_offered_count`에 세지 않도록 `respond_paw`에서 거절 시 카운트를 되돌린다(거절은 무비용).

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현**

`loop_interactor.py` import: `from apps.engine.domain.entities.paw_rules import choose_wish`.

`_maybe_offer_paw` 전체 교체:

```python
    def _maybe_offer_paw(self, loop, bundle) -> dict | None:
        if loop.beat != 2 or loop.pending_paw is not None or not bundle.paw_wishes:
            return None
        attempt = self._attempts.get(loop.attempt_id)
        offers = [e for e in self._events.query(loop.attempt_id) if e.type == "monkey_paw_offer"]
        declines = 0
        for e in reversed(offers):
            if e.accepted:
                break
            declines += 1
        if not paw_should_offer(loop.loop_n, self._prev_score(loop), attempt.paw_offered_count,
                                consecutive_declines=declines):
            return None
        used = {r.shown_reason for r in self._rules.list(loop.attempt_id) if r.source == "monkey_paw"}
        used_keys = {r.action for r in self._rules.list(loop.attempt_id) if r.source == "monkey_paw"}
        prev_cells = None
        if loop.loop_n > 1:
            scored = [e for e in self._events.query(loop.attempt_id, loop_n=loop.loop_n - 1) if e.type == "answer_scored"]
            prev_cells = scored[-1].cell_scores if scored else None
        wish = choose_wish(loop.loop_n, prev_cells,
                           bundle.paw_wishes, {w.key for w in bundle.paw_wishes if w.action in used_keys})
        if wish is None:
            return None
        shown_reason = self._manager.make_paw_reason(wish) or wish.default_reason
        attempt.paw_offered_count += 1
        offer_id = str(uuid.uuid4())[:8]
        show_reason = (not self._paw_reason_ab_on) or ab_assign(str(loop.attempt_id))
        loop.pending_paw = {
            "offer_id": offer_id, "offer_index": attempt.paw_offered_count, "wish_key": wish.key,
            "label": wish.label, "shown_reason": shown_reason, "show_reason": show_reason,
        }
        self._attempts.save()
        return {"offer_id": offer_id, "rule_label": wish.label,
                "shown_reason": shown_reason if show_reason else None}
```

`respond_paw` 수락 분기 교체:

```python
        if accept:
            wish = next(w for w in self._scenario.bundle().paw_wishes if w.key == paw["wish_key"])
            specs = [(wish.action, wish.effect, wish.when_beat)] + [
                (x["action"], x["effect"], wish.when_beat) for x in wish.extra_rules]
            for action, effect, when in specs:
                self._rules.add(self._rule_orm_cls(
                    attempt_id=loop.attempt_id, rule_id=rule_id if action == wish.action else self._rules.next_rule_id(loop.attempt_id),
                    source="monkey_paw", target=wish.target, when_beat=when, effect=effect, action=action,
                    shown_reason=paw["shown_reason"] if paw["show_reason"] else None,
                    hidden_side_effect=None, created_loop=loop.loop_n))
            for effect in wish.effects:
                self._rules.add(self._rule_orm_cls(
                    attempt_id=loop.attempt_id, rule_id=self._rules.next_rule_id(loop.attempt_id),
                    source="paw_effect", target=effect.actor, when_beat=effect.beat, effect="enforce",
                    action=effect.action, shown_reason=None, hidden_side_effect=effect.observation,
                    created_loop=loop.loop_n))
            self._events.record(loop.attempt_id, ev.RuleAppliedEvent(
                loop_n=loop.loop_n, rule_id=rule_id, source="monkey_paw", conflict=False))
            rule_label = paw["label"]
        else:
            attempt = self._attempts.get(loop.attempt_id)
            attempt.paw_offered_count = max(0, attempt.paw_offered_count - 1)  # 거절은 무비용
            self._attempts.save()
```

> `next_rule_id`가 같은 트랜잭션 안에서 연속 호출 시 같은 ID를 돌려주면(추가 전 count 기반) 규칙을 하나 add할 때마다 `flush`하거나, ID를 `R{n}`으로 직접 증가시킨다. 첫 테스트가 잡아낸다.

`manager_interactor.py`에 추가(기존 `make_paw`는 남겨도 되지만 미사용이면 삭제):

```python
    def make_paw_reason(self, wish) -> str | None:
        """제안 문구만 쓴다. 규칙 선택은 코드다 (기획서 5.7: 정답을 아는 층이 '원할 법한' 말을 고른다)."""
        sys = prompts.MANAGER_SYSTEM.format(
            hidden_truth=self._scenario.hidden_truth(), budget_left=0, npc_states="(생략)",
            user_utterances="(생략)", rules="(생략)", yesterday_score="(생략)",
        ) + (f"\n\n추가 지시: 규칙 '{wish.label}'을 플레이어가 받고 싶게 만드는 한 문장을 쓴다. "
             "세계 안의 말투, 부작용은 절대 말하지 않는다. 출력 JSON {\"shown_reason\": ...}")

        class _Out(StrictModel):
            shown_reason: str = Field(min_length=1, max_length=120)

        out, _ = run_with_harness(self._llm, [system_msg(sys)], _Out, role="manager_paw", harness_on=True)
        return out.shown_reason if out else None
```

> `StrictModel`·`Field` import는 `llm_output_dto`에서 가져온다. 테스트의 `core_llm=FakeLLM()`은 빈 큐라 `None` → `default_reason`이 쓰인다.

- [ ] **Step 4: 통과 확인** — 위 3개 + 전체. `test_connected_investigation.py::test_paw_benefit_and_cost_occur_in_linked_scene_only`는 Task 5에서 갱신하므로 이 시점엔 실패해도 된다.

---

### Task 5: 부작용 실행 — 예산 대가 제거, `paw_effect` 관찰 문장 기록

**Files:**
- Modify: `backend/apps/engine/app/use_cases/scene_execution.py:77-89`
- Test: `backend/tests/engine/test_connected_investigation.py:203-221`

**Interfaces:**
- Produces: `paw_effect` 규칙이 obeyed로 실행될 때 `RuleExecutionEvent.side_effect = rule.hidden_side_effect`, 그리고 같은 문장을 `disclose(... key=f"paw-effect-{beat}-{rule_id}", source_kind="rule_result", rule_id=rule.rule_id)`로 공개. `night_interactor._make_side_effect_claims`는 변경 없이 이 문장을 줍는다.

- [ ] **Step 1: 기존 테스트를 새 기대로 교체**

```python
def test_paw_side_effect_happens_in_a_later_scene_as_an_observation(db_session):
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    day, _, attempt, info = make_day(db_session, [])
    scene = day.advance_beat(info["loop_id"])          # beat 2 — 제안
    day.respond_paw(info["loop_id"], scene["paw_offer"]["offer_id"], True)
    before = LoopRepository(db_session).get(info["loop_id"]).budget_left
    day.advance_beat(info["loop_id"])                  # beat 3
    fourth = day.advance_beat(info["loop_id"])         # beat 4 — 검진 건너뜀
    assert "담당자가 채연 침상을 지나친다" in fourth["narration"]
    fifth = day.advance_beat(info["loop_id"])          # beat 5 — 부작용
    assert "은상도 담요를 벗지 않는다" in fifth["narration"]
    assert LoopRepository(db_session).get(info["loop_id"]).budget_left == before
    executions = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "rule_execution"]
    effect = next(e for e in executions if e.side_effect)
    assert effect.side_effect.startswith("검진이 채연을 건너뛴 날")
    notes = NoteRepository(db_session).list(attempt.id)
    assert any(n.text == effect.side_effect for n in notes)
```

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현** — `scene_execution.py`의 `side_effect = None` 이후 블록(`if (rule.source == "monkey_paw" and action == EXPLAIN_ACTION ...)` 전체)을 아래로 교체:

```python
            side_effect = None
            if rule.source == "paw_effect" and result == "obeyed" and rule.hidden_side_effect:
                side_effect = rule.hidden_side_effect
                cost = disclose(event_log, loop, beat, key=f"paw-effect-{beat.n}-{rule.rule_id}",
                                text=side_effect, actor=opportunity.actor, source_kind="rule_result", rule_id=rule.rule_id)
                narration.append(side_effect)
                evidence.append(cost.observation_id)
```

`shared_costs`·`cost_key` 관련 줄은 삭제한다. `Rule` 도메인 엔티티(`rule_rules.Rule`)에 `hidden_side_effect`가 없으면 `loop_interactor._to_domain_rule`과 `Rule` dataclass에 `hidden_side_effect: str | None = None`을 추가한다.

- [ ] **Step 4: 통과 확인** — 전체 스위트. `test_five_loop_rules.py::test_paw_side_effect_is_not_an_answer_requirement`가 `side_effect` 문장 형식을 고정했다면 새 문장으로 갱신.

---

### Task 6: 침묵 규칙과 조건부 대사

**Files:**
- Modify: `backend/apps/engine/app/use_cases/loop_interactor.py` (`_utter` 규칙 계산 직후, `_make_ambient:510-535`)
- Test: `backend/tests/engine/test_usecase_day.py`

**Interfaces:**
- Produces: 활성 규칙에 `effect == "silence"`가 있으면 `_utter`는 모델 호출 없이 `{"reply": f"{char.name}은(는) 입을 다문 채 고개를 젓는다.", "npc": {..., "uttered": True}, "observations": [<statement 관찰>], ...}`을 돌려주고 예산을 쓴다. `_make_ambient`는 `dialogue.required_rules`가 그날 활성 규칙 `(target, action)`에 전부 있을 때만 재생.

- [ ] **Step 1: 실패하는 테스트**

```python
def test_silence_rule_returns_narration_without_model_call_and_spends_budget(db_session):
    day, scenario, attempt, info = make_day(db_session, [_agent_reply("안 나와야 하는 답")])
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="monkey_paw", target="은상",
                                           when_beat=None, effect="silence", action="말을 하지 않는다", created_loop=1))
    res = day.utter(info["loop_id"], "eunsang", "은상아, 오늘 뭐 들었어?")
    assert res["reply"] == "은상은(는) 입을 다문 채 고개를 젓는다."
    assert res["budget_left"] == 7
    assert [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "harness_event"] == []


def test_conditional_dialogue_plays_only_with_required_rule(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    scene = day.advance_beat(info["loop_id"])
    assert all("왜 말 안 해" not in l["text"] for l in (scene.get("ambient") or {}).get("lines", []))
    loop = LoopRepository(db_session).get(info["loop_id"]); loop.state, loop.score = "closed", 60; db_session.commit()
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R9", source="monkey_paw", target="은상",
                                           when_beat=None, effect="silence", action="말을 하지 않는다", created_loop=2))
    info = day.start_loop(attempt.id)
    scene = day.advance_beat(info["loop_id"])
    assert any("왜 말 안 해" in l["text"] for l in scene["ambient"]["lines"])
```

- [ ] **Step 2: 실패 확인**
- [ ] **Step 3: 구현**

`_utter`에서 `active_rules = [...]` 계산 직후:

```python
        if any(r.effect == "silence" for r in active_rules):
            reply = f"{char.name}은(는) 입을 다문 채 고개를 젓는다."
            npc.uttered_beat = loop.beat
            loop.budget_left = state.budget_left
            observation = disclose(self._events, loop, bundle.beats[loop.beat - 1],
                                   key=observation_key, text=reply, actor=char.name, source_kind="statement")
            self._notes.upsert(loop.attempt_id, kind="fragment", text=reply, loop_n=loop.loop_n,
                               source_key=observation.observation_id)
            response = {"utterance_id": utterance_id, "observations": [observation.model_dump()], "reply": reply,
                        "npc": {"code": char.code, "name": char.name, "mood": npc.mood, "uttered": True},
                        "budget_left": loop.budget_left, "beat": loop.beat, "tool_used": False}
            self._events.record(loop.attempt_id, ev.UtteranceEvent(
                loop_n=loop.loop_n, beat=loop.beat, target=char.name, text=text, reply=reply,
                budget_left=loop.budget_left, suspicion_delta=0, trust_delta=0, disclosure_level=0,
                utterance_id=utterance_id, response=response))
            self._loops.save()
            return response
```

> F2 계획이 먼저 적용됐다면 `state`가 게이트 뒤로 옮겨져 있다. 침묵 분기는 F2의 게이트·분류 **뒤**, 예산 차감(`apply_utterance`) **뒤**에 둔다(침묵은 예산을 쓴다).

`_make_ambient`의 `eligible = True` 앞에:

```python
            active = {(r.target, r.action) for r in self._rules.list(loop.attempt_id)}
            if any((r.actor, r.action) not in active for r in dialogue.required_rules):
                continue
```

`execute_scene`(scene_execution.py)에서 `applicable` 규칙 필터가 `effect`를 보지 않으므로 `silence` 규칙이 장면 행동에 섞이지 않게 `rules = [r for r in rules if r.effect != "silence"]`를 함수 첫 줄에 둔다.

- [ ] **Step 4: 통과 확인** — 전체 스위트

---

### Task 7: 프런트 — Q군 삽화 매핑과 헤드리스 기대

**Files:**
- Modify: `frontend/lib/imageMap.ts` (`CLUE_IMAGES` 또는 `clueImage`)
- Test: `frontend/tests/five-loop-flow.cjs`

- [ ] **Step 1:** `imageMap.ts`의 `clueImage(imageId)`가 `Q02`~`Q08`을 `/assets/clues/Q0N-<slug>-v1.png`(Q04는 `-v2`)로 돌려주게 매핑을 추가한다. 파일명은 `ls frontend/public/assets/clues/ | grep Q0`로 확인.
- [ ] **Step 2:** `five-loop-flow.cjs`의 원숭이손 모의 응답 `rule_label`을 `"오늘 검진은 채연을 보지 않는다."`로, 다음 비트 모의 응답 `narration`에 부작용 문장과 `illustrations: [{image_id: "Q02", caption: "..."}]`를 넣고, 팝업 문구·삽화 `img[src$="Q02-evening-four-trays-v1.png"]`가 보이는지 기대를 추가한다.
- [ ] **Step 3:** `npx tsc --noEmit`; `five-loop-flow.cjs`, `gameplay-clarity.cjs`, `scene-illustrations.cjs` 순차 실행 → 통과.

---

### Task 8: 회고·문서·전체 검증

**Files:**
- Modify: `frontend/components/Retrospective.tsx:92-107` ("설계된 대가"가 `paw_effect` 규칙의 `hidden_side_effect`를 보여주는지 확인 — 인스펙터 노출 경로 `inspector_interactor.py:113-132`가 `source=="monkey_paw"`만 고르면 `paw_effect`도 포함)
- Modify: `docs/spec/api_contract.md`, `docs/HANDOFF-26-09-16.md`

- [ ] **Step 1:** 인스펙터·회고에서 숨은 규칙이 "설계된 대가"로 보이도록 소스 필터를 `in ("monkey_paw", "paw_effect")`로 넓힌다. 회고 이전(하네스 뷰)에서는 `hidden_side_effect`가 가려지는 기존 마스킹을 유지.
- [ ] **Step 2:** 계약 문서에 `paw_offer.rule_label`이 소원 문장이 됐음과 `rules[].source` 값 `paw_effect` 추가.
- [ ] **Step 3:** 전체: 백엔드 스위트, `tsc`, 헤드리스 7종 순차. 결과를 세션 주인에게 보고. 커밋 금지.
- [ ] **Step 4:** 러너 dry-run(`backend/scripts` 중 모델 호출 없는 dry-run 러너를 `grep -l dry` 로 찾아) 5회차 사슬에서 원숭이손 2회 제안·부작용 관찰·부작용 주장 생성이 나오는지 확인.
