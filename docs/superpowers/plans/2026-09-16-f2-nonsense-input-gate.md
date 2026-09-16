# F2 무의미 입력 처리 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** "ㅋㅋㅋㅋ"·"……"·"왜왜왜왜" 같은 무의미 입력이 NPC 모델에 닿지 않게 하고, 잡담은 지식 블록 없이 답하게 해 첫 발화 동기 자백을 막는다.

**Architecture:** 모델 호출 전 2단. 1단은 순수 함수 규칙 게이트(도메인 엔티티), 2단은 Core 모델의 경량 분류 콜(유스케이스). 무의미 판정이면 인물별 `fallback_lines`를 즉답하고 같은 비트 첫 1회는 예산을 쓰지 않는다. 카운터는 스키마 없이 이벤트 로그에서 센다.

**Tech Stack:** FastAPI + SQLAlchemy(`backend/.venv`), Pydantic 출력 모델 + `run_with_harness`, FakeLLM 테스트.

**Spec:** `docs/superpowers/specs/2026-09-16-coherence-chain-design.md` §1

## Global Constraints

- 모델 호출 0회가 게이트의 정의다. gated 입력에서 `harness_event`가 하나도 남지 않아야 한다.
- 예산: 같은 (loop, beat)에서 gated 첫 1회는 면제, 두 번째부터 차감. 비트가 바뀌면 리셋.
- DB 마이그레이션 없음. 새 상태는 `UtteranceEvent` payload(JSONB) 필드로만 남긴다.
- 분류기 실패(하네스 폴백)는 막지 않는다 — 현행 경로로 진행.
- 테스트: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests`. 서버 재기동 금지, 커밋은 사용자 지시 뒤.
- 줄 번호는 2026-09-16 14:00 기준(`loop_interactor._utter` 242-367, `game_support.build_agent_messages` 50-140). 편집 전 `grep -n`.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `backend/apps/engine/domain/entities/utterance_rules.py` (신규) | `is_nonsense(text)` 순수 규칙 |
| `backend/apps/engine/app/use_cases/utterance_classifier.py` (신규) | `classify(llm, text) -> Label` 경량 콜 + 출력 모델 |
| `backend/apps/engine/app/dtos/llm_output_dto.py` | `UtteranceClassOutput` |
| `backend/apps/engine/app/dtos/event_log_dto.py:68-80` | `UtteranceEvent.classification/gated/budget_charged` |
| `backend/apps/engine/app/use_cases/game_support.py:50-140` | `build_agent_messages(include_knowledge=True)` |
| `backend/apps/engine/app/use_cases/loop_interactor.py:242-367` | `_utter` 앞단 분기 |
| `backend/tests/pure/test_utterance_rules.py` (신규), `backend/tests/engine/test_usecase_day.py` | 테스트 |

---

### Task 1: 규칙 게이트 (순수 함수)

**Files:**
- Create: `backend/apps/engine/domain/entities/utterance_rules.py`
- Test: `backend/tests/pure/test_utterance_rules.py`

**Interfaces:**
- Produces: `is_nonsense(text: str) -> bool`

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/pure/test_utterance_rules.py
import pytest
from apps.engine.domain.entities.utterance_rules import is_nonsense


@pytest.mark.parametrize("text", ["ㅋㅋㅋㅋ", "......", "……", "왜왜왜왜왜", "ㅠㅠ", "   ", "!!!!", "ㅇㅇㅇ", "아아아아"])
def test_nonsense_inputs_are_gated(text):
    assert is_nonsense(text)


@pytest.mark.parametrize("text", ["왜?", "응", "왜 안어", "밥 남겼어?", "채연아", "ㅋㅋ 왜 안 먹어", "왜왜 그래"])
def test_valid_inputs_pass(text):
    assert not is_nonsense(text)
```

- [ ] **Step 2: 실패 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/pure/test_utterance_rules.py`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: 구현**

```python
# backend/apps/engine/domain/entities/utterance_rules.py
"""플레이어 입력의 무의미 판정 — 모델 호출 전 규칙 게이트 (테스터6 F2)."""

import re

_SYLLABLE_RE = re.compile(r"[가-힣]")
_REPEAT_RE = re.compile(r"^(.)\1{2,}$")  # 같은 문자 3회 이상만으로 구성
_REPEAT_SYLLABLE_RE = re.compile(r"^([가-힣])\1{2,}$")  # 같은 음절 3회 이상만


def is_nonsense(text: str) -> bool:
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return True
    if not _SYLLABLE_RE.search(stripped):
        return True  # 완성 음절 0개: 자모·기호·점만
    if _REPEAT_SYLLABLE_RE.match(stripped):
        return True  # "왜왜왜왜", "아아아아"
    return False
```

> "ㅋㅋ 왜 안 먹어"는 음절이 있고 반복만으로 구성되지 않으므로 통과한다. "왜왜 그래"도 통과.

- [ ] **Step 4: 통과 확인**

Run: 위 명령 → Expected: 16 passed

---

### Task 2: 분류기 콜과 출력 모델

**Files:**
- Modify: `backend/apps/engine/app/dtos/llm_output_dto.py` (`AdvisorAnswerOutput` 위쪽 아무 곳)
- Create: `backend/apps/engine/app/use_cases/utterance_classifier.py`
- Test: `backend/tests/engine/test_utterance_classifier.py`

**Interfaces:**
- Produces:
  - `UtteranceClassOutput(label: Literal["question","request","chat","nonsense"])`
  - `classify(llm, text: str) -> tuple[str | None, HarnessReport]` — 폴백이면 `(None, report)`

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/engine/test_utterance_classifier.py
from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.use_cases.utterance_classifier import classify


def test_classifier_returns_label():
    label, report = classify(FakeLLM([{"label": "chat"}]), "오늘 날씨 어때")
    assert label == "chat"
    assert report.role == "classifier"


def test_classifier_fallback_is_none():
    label, report = classify(FakeLLM([]), "왜 안어")
    assert label is None
    assert report.fallback_used
```

- [ ] **Step 2: 실패 확인** — Run: `PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_utterance_classifier.py` → ModuleNotFoundError

- [ ] **Step 3: 구현**

`llm_output_dto.py`에 추가:

```python
class UtteranceClassOutput(StrictModel):
    label: Literal["question", "request", "chat", "nonsense"]
```

```python
# backend/apps/engine/app/use_cases/utterance_classifier.py
"""플레이어 입력 분류 — 질문·부탁·잡담·무의미. 라벨 하나만 낸다 (테스터6 F2)."""

from apps.engine.app.dtos.llm_output_dto import UtteranceClassOutput
from apps.engine.app.use_cases.game_support import system_msg, user_msg
from apps.engine.app.use_cases.harness import run_with_harness

_SYSTEM = (
    "플레이어가 대피소의 친구에게 건넨 한 줄을 넷 중 하나로 분류한다. "
    "question: 무엇을 묻는다(오타·줄임말이어도 뜻이 잡히면 포함). "
    "request: 무엇을 해 달라고 한다. "
    "chat: 인사·감탄·잡담처럼 정보를 묻지도 시키지도 않는다. "
    "nonsense: 뜻을 잡을 수 없는 글자·기호·반복. "
    "출력은 JSON {\"label\": ...} 하나뿐이다."
)


def classify(llm, text: str):
    out, report = run_with_harness(
        llm, [system_msg(_SYSTEM), user_msg(text)], UtteranceClassOutput,
        role="classifier", harness_on=True, temperature=0,
    )
    return (out.label if out else None), report
```

> `user_msg`가 `game_support`에 없으면 같은 파일의 `system_msg` 옆에 `def user_msg(content): return MessageDTO(role="user", content=content)`가 있는지 확인하고, 없으면 추가한다.

- [ ] **Step 4: 통과 확인** — Expected: 2 passed

---

### Task 3: 이벤트 필드와 지식 제외 옵션

**Files:**
- Modify: `backend/apps/engine/app/dtos/event_log_dto.py:68-80`
- Modify: `backend/apps/engine/app/use_cases/game_support.py:50-140`
- Test: `backend/tests/engine/test_usecase_day.py`

**Interfaces:**
- Produces: `UtteranceEvent.classification: str | None = None`, `gated: bool = False`, `budget_charged: bool = True`; `build_agent_messages(..., include_knowledge: bool = True)`

- [ ] **Step 1: 실패하는 테스트**

```python
# backend/tests/engine/test_usecase_day.py (추가)
def test_agent_messages_can_omit_knowledge_block():
    from apps.engine.app.use_cases.game_support import build_agent_messages
    scenario = build_a()
    char = next(c for c in scenario.bundle().characters if c.code == "chaeyeon")
    with_k = build_agent_messages(scenario.bundle(), char, suspicion=0, trust=0, opposite=False,
                                  rules_text="", memory=[], user_text="안녕", loop_n=1, age7_on=True)
    without = build_agent_messages(scenario.bundle(), char, suspicion=0, trust=0, opposite=False,
                                   rules_text="", memory=[], user_text="안녕", loop_n=1, age7_on=True,
                                   include_knowledge=False)
    assert "[하루 시작 전부터 아는 것]" in with_k[0].content
    assert "[하루 시작 전부터 아는 것]" not in without[0].content
    assert "이송될 거라고 믿는다" not in without[0].content
```

- [ ] **Step 2: 실패 확인** — TypeError: unexpected keyword `include_knowledge`

- [ ] **Step 3: 구현**

`event_log_dto.py` `UtteranceEvent`에 세 필드 추가(`response` 뒤):

```python
    classification: str | None = None  # question | request | chat | nonsense | None(분류 실패)
    gated: bool = False  # 규칙 게이트·무의미 판정으로 모델 호출 없이 즉답
    budget_charged: bool = True
```

`game_support.build_agent_messages` 서명에 `include_knowledge: bool = True` 추가하고, `knowledge = [...]` 줄 다음의 `if knowledge:`를 `if knowledge and include_knowledge:`로 바꾼다.

- [ ] **Step 4: 통과 확인** — `PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_usecase_day.py` → all passed

---

### Task 4: `_utter` 앞단 분기 — 게이트·분류·예산

**Files:**
- Modify: `backend/apps/engine/app/use_cases/loop_interactor.py:242-367`
- Test: `backend/tests/engine/test_usecase_day.py`

**Interfaces:**
- Consumes: `is_nonsense`, `classify`, `pick_fallback_line`(game_support), `include_knowledge`
- Produces: gated 응답 `{"utterance_id", "observations": [], "reply": <fallback>, "npc": {..., "uttered": False}, "budget_left", "beat", "tool_used": False, "gated": True}`; 이벤트 `gated=True, classification=..., budget_charged=...`

- [ ] **Step 1: 실패하는 테스트**

```python
def _harness_events(db_session, attempt):
    return [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "harness_event"]


def test_nonsense_is_gated_without_model_call_and_first_is_free(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    assert res["gated"] is True
    assert res["reply"] in npc.fallback_lines
    assert res["budget_left"] == 8
    assert res["npc"]["uttered"] is False
    assert _harness_events(db_session, attempt) == []


def test_second_nonsense_in_same_beat_is_charged(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    inter.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    res = inter.utter(info["loop_id"], npc.code, "......")
    assert res["budget_left"] == 7
    events = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "utterance"]
    assert [e.budget_charged for e in events] == [False, True]


def test_classifier_nonsense_is_gated_and_chat_omits_knowledge(db_session):
    # 큐: 분류기 nonsense → 즉답 / 분류기 chat + NPC 답 → 모델 호출은 지식 없이
    inter, scenario, attempt, info = make_day(db_session, [_agent_reply("응, 안녕.")])
    inter._core_llm = FakeLLM([{"label": "nonsense"}, {"label": "chat"}])
    npc = _first_npc(scenario)
    first = inter.utter(info["loop_id"], npc.code, "뭐라는거야ㅋ")
    assert first["gated"] is True and first["budget_left"] == 8
    second = inter.utter(info["loop_id"], npc.code, "안녕 좋은 아침")
    assert second["reply"] == "응, 안녕."
    agent_calls = [e for e in _harness_events(db_session, attempt) if e.role == "agent"]
    assert agent_calls and "[하루 시작 전부터 아는 것]" not in agent_calls[-1].call_records[0]["messages"][0]["content"]


def test_classifier_fallback_keeps_current_path(db_session):
    inter, scenario, attempt, info = make_day(db_session, [_agent_reply("배 안 고파.")])
    inter._core_llm = FakeLLM([])
    npc = _first_npc(scenario)
    res = inter.utter(info["loop_id"], npc.code, "왜 안어")
    assert res["reply"] == "배 안 고파."
    events = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "utterance"]
    assert events[-1].classification is None and events[-1].gated is False
```

> `inter._core_llm` 속성명은 `grep -n "core_llm" loop_interactor.py`로 확인한다. `make_day`의 `core_llm=FakeLLM()`은 빈 큐라 분류기가 폴백하므로 기존 테스트는 현행 경로를 탄다.

- [ ] **Step 2: 실패 확인** — KeyError `gated` 등

- [ ] **Step 3: 구현**

`loop_interactor.py` import에 추가:

```python
from apps.engine.domain.entities.utterance_rules import is_nonsense
from apps.engine.app.use_cases.utterance_classifier import classify
from apps.engine.app.use_cases.game_support import pick_fallback_line
```

`_utter`에서 `npc.uttered_beat == loop.beat` 검사 **직후**, `rule_rows = ...` **직전**에 삽입:

```python
        classification = None
        gated = is_nonsense(text)
        if not gated:
            label, report = classify(self._core_llm, text)
            record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=loop.beat)
            classification = label
            gated = label == "nonsense"
        if gated:
            return self._gated_reply(loop, char, text, utterance_id, classification)
        include_knowledge = classification != "chat"
```

`build_agent_messages(...)` 호출에 `include_knowledge=include_knowledge,`를 넘긴다.

정상 경로의 `ev.UtteranceEvent(...)`에 `classification=classification, gated=False, budget_charged=True`를 추가한다.

클래스에 메서드 추가(`_utter` 바로 아래):

```python
    def _gated_reply(self, loop, char, text, utterance_id, classification):
        """무의미 입력 — 모델 호출 없이 인물 말투로 되묻는다. 같은 비트 첫 1회는 예산 면제."""
        prior = [e for e in self._events.query(loop.attempt_id, type=ev.EventType.UTTERANCE, loop_n=loop.loop_n)
                 if e.beat == loop.beat and e.gated]
        charged = bool(prior)
        if charged:
            try:
                state = loop_rules.apply_utterance(self._loop_state(loop))
            except loop_rules.DomainError as e:
                raise GameStateError(str(e)) from e
            loop.budget_left = state.budget_left
        reply = pick_fallback_line(char)
        response = {
            "utterance_id": utterance_id, "observations": [], "reply": reply,
            "npc": {"code": char.code, "name": char.name, "mood": "calm", "uttered": False},
            "budget_left": loop.budget_left, "beat": loop.beat, "tool_used": False, "gated": True,
        }
        self._events.record(loop.attempt_id, ev.UtteranceEvent(
            loop_n=loop.loop_n, beat=loop.beat, target=char.name, text=text, reply=reply,
            budget_left=loop.budget_left, suspicion_delta=0, trust_delta=0, disclosure_level=0,
            utterance_id=utterance_id, response=response,
            classification=classification, gated=True, budget_charged=charged))
        self._loops.save()
        return response
```

> 주의: 기존 코드의 `state = loop_rules.apply_utterance(...)`(예산 차감 검사)는 게이트 분기보다 **앞**에 있다. 게이트 분기를 그 줄보다 앞으로 옮기거나, `apply_utterance` 호출을 게이트 분기 뒤로 내린다. 예산 0일 때 무의미 입력은 첫 1회 면제라 예외가 나면 안 된다 — `_gated_reply`에서만 차감한다.

- [ ] **Step 4: 통과 확인** — `PYTHONPATH=. .venv/bin/pytest -q tests` → all passed. `test_failed_model_response_preserves_budget_and_is_not_npc_ignorance` 등 기존 테스트는 분류기 폴백 경로로 그대로 통과해야 한다.

---

### Task 5: 프런트 확인과 계약 문서

**Files:**
- Modify: `frontend/contracts/api.ts` (발화 응답 타입에 `gated?: boolean`), `docs/spec/api_contract.md`
- Test: `frontend/tests/npc-followup.cjs` (모의 응답에 `gated:true` 케이스 1개)

- [ ] **Step 1:** `api.ts` 발화 응답 타입(`UtteranceRes` 또는 동명)에 `gated?: boolean` 추가. DayScreen은 `reply`를 그대로 말풍선에 그리므로 화면 변경은 없다. `npc.uttered=false`라 같은 비트 재발화 잠금이 걸리지 않는 것이 의도다 — DayScreen의 "이 장면에서 이미 대화" 딤 처리가 `uttered`를 보는지 확인(`grep -n uttered components/screens/DayScreen.tsx`).
- [ ] **Step 2:** `npc-followup.cjs`에 gated 응답 케이스: 말풍선에 fallback 문장이 뜨고 "오늘 남은 대화" 숫자가 줄지 않는지.
- [ ] **Step 3:** `npx tsc --noEmit`, `npc-followup.cjs` 실행 → 통과. `api_contract.md`에 `gated`·`classification` 설명 추가.
- [ ] **Step 4:** 전체 백엔드 스위트 재실행 후 결과 보고. 커밋 금지.
