# F7 신의 질문 답변 형식 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 신의 질문 답변을 「판정 → 근거 → 조언」 3부 고정형으로 바꾸고, 조언자가 숨은 사실을 흘리던 리드 표를 세계 구조(잠재 행동·인물 지식)에서만 조언을 만드는 표로 교체한다.

**Architecture:** 백엔드 `InterventionInteractor.ask()`가 LLM 답변 뒤에 결정론적으로 판정 접두·조언을 조립한다. `AdvisorLeadDTO`는 `text`(사실 문장)를 잃고 `anchor_cues`·`target`·`ask`/`rule_action`을 얻는다. 조언은 플레이어의 공개 관찰 중 닻이 있을 때만 생성한다. 프런트는 답변 위에 안내 한 줄과 판정 라벨을 보여준다.

**Tech Stack:** FastAPI + SQLAlchemy(백엔드, `backend/.venv`), Pydantic DTO, FakeLLM 테스트(`tests/engine`), Next.js + Playwright 헤드리스(`frontend/tests/*.cjs`).

**Spec:** `docs/superpowers/specs/2026-09-16-coherence-chain-design.md` §2

## Global Constraints

- 조언자는 그 판의 로그와 세계 구조만 안다. `hidden_truth`·`truth_claims`·`ending_lines`는 어떤 경로로도 프롬프트나 응답에 들어가지 않는다 (기획서 5.6).
- 답변 말투는 짧은 한다체. `합니다`·`습니다`·`입니다`가 답변에 나오면 재생성.
- "확인했다/확인됐다"류 단정은 근거 ID(`evidence`)가 하나 이상 있을 때만 허용.
- 테스트 실행: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests` (기준 462 passed). 프런트: `cd frontend && npx tsc --noEmit`, 헤드리스는 `NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/<name>.cjs` 를 **한 번에 하나씩**.
- 서버 재기동 금지(백엔드 8500은 reload 없음 — 세션 주인이 재기동). 커밋은 사용자 지시 뒤에만.
- 줄 번호는 2026-09-16 14:00 기준. 편집 전 `grep -n`으로 다시 찾는다.

---

## File Structure

| 파일 | 책임 |
|---|---|
| `backend/apps/engine/app/dtos/scenario_dto.py` | `AdvisorLeadDTO` 필드 교체 |
| `backend/apps/scenarios/scenario_a/adapter.py` | 리드 표 재작성(~507), 준·은상 지식 추가(~181, ~156), 준 잠재 행동 "포대를 들여다본다" 추가(scene_actions 뒤쪽 dormant 블록) |
| `backend/apps/engine/app/use_cases/advisor_advice.py` (신규) | 순수 함수: 닻 찾기, 조언 문장 조립, 판정 접두, "왜" 질문 판별, 말투·단정 검사 |
| `backend/apps/engine/app/use_cases/intervention_interactor.py` | `ask()`에서 리드 text 제거, 판정·조언 조립, 검사 추가 |
| `backend/tests/engine/test_advisor_advice.py` (신규) | 순수 함수 테스트 |
| `backend/tests/engine/test_usecase_intervention.py` | 리드 관련 기존 테스트 갱신 |
| `frontend/components/screens/GodScreen.tsx` | 안내 한 줄 + 판정 라벨 표기, "새 단서" 박스 제거 |
| `frontend/contracts/api.ts` | `GodQuestionRes.verdict` 추가 |
| `frontend/tests/five-loop-flow.cjs`, `connected-investigation.cjs` | `unlocked_note` 기대 제거, 안내·판정 기대 추가 |

---

### Task 1: 순수 함수 — 판정 접두·"왜" 질문·말투 검사

**Files:**
- Create: `backend/apps/engine/app/use_cases/advisor_advice.py`
- Test: `backend/tests/engine/test_advisor_advice.py`

**Interfaces:**
- Produces:
  - `is_why_question(text: str) -> bool`
  - `verdict_prefix(status: str, why: bool) -> str` — `"맞다."`, `"아니다."`, `"그건 알 수 없다."`, why면 `"왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."`
  - `polite_register_check(out) -> str | None` — 하네스 fact_check 서명(출력 모델을 받아 위반 문자열 또는 None)
  - `unbacked_confirmation_check(out) -> str | None` — `evidence`가 비었는데 answer에 `확인했|확인됐|확인되었|확인하였` 이 있으면 위반

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# backend/tests/engine/test_advisor_advice.py
from types import SimpleNamespace as NS

from apps.engine.app.use_cases.advisor_advice import (
    is_why_question, verdict_prefix, polite_register_check, unbacked_confirmation_check,
)


def test_why_question_detection():
    assert is_why_question("충식이는 왜 이송된거야?")
    assert is_why_question("이송된 이유가 뭐야")
    assert is_why_question("어떻게 아는 거야?")
    assert not is_why_question("채연이 오늘 배급을 남겼어?")


def test_verdict_prefix_by_status():
    assert verdict_prefix("supported", False) == "맞다."
    assert verdict_prefix("contradicted", False) == "아니다."
    assert verdict_prefix("unknown", False) == "그건 알 수 없다."
    assert verdict_prefix("unknown", True) == "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."
    assert verdict_prefix("supported", True) == "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."


def test_polite_register_is_rejected():
    assert polite_register_check(NS(answer="충식이는 기침을 많이 했다고 합니다.")) == "register: 합니다체"
    assert polite_register_check(NS(answer="충식이는 기침을 많이 했다.")) is None


def test_confirmation_without_evidence_is_rejected():
    assert unbacked_confirmation_check(NS(answer="트럭 옆면 글자를 확인했습니다.", evidence=[])) == "unbacked_confirmation"
    assert unbacked_confirmation_check(NS(answer="트럭 옆면 글자를 확인했다.", evidence=[NS(id="x")])) is None
    assert unbacked_confirmation_check(NS(answer="네 기록에는 없다.", evidence=[])) is None
```

- [ ] **Step 2: 실패 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_advisor_advice.py`
Expected: FAIL with `ModuleNotFoundError: apps.engine.app.use_cases.advisor_advice`

- [ ] **Step 3: 최소 구현**

```python
# backend/apps/engine/app/use_cases/advisor_advice.py
"""신의 질문 답변 조립 — 판정·조언은 결정론, 진실은 모른다 (기획서 5.5·5.6)."""

import re

_WHY_CUES = ("왜", "이유", "어떻게", "어째서", "뭐 때문")
_POLITE_RE = re.compile(r"(습니다|합니다|입니다)")
_CONFIRM_RE = re.compile(r"확인(했|됐|되었|하였)")

WHY_PREFIX = "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."
_VERDICT = {"supported": "맞다.", "contradicted": "아니다.", "unknown": "그건 알 수 없다."}


def is_why_question(text: str) -> bool:
    return any(cue in text for cue in _WHY_CUES)


def verdict_prefix(status: str, why: bool) -> str:
    if why:
        return WHY_PREFIX
    return _VERDICT.get(status, _VERDICT["unknown"])


def polite_register_check(out) -> str | None:
    if _POLITE_RE.search(str(getattr(out, "answer", "") or "")):
        return "register: 합니다체"
    return None


def unbacked_confirmation_check(out) -> str | None:
    answer = str(getattr(out, "answer", "") or "")
    if _CONFIRM_RE.search(answer) and not list(getattr(out, "evidence", []) or []):
        return "unbacked_confirmation"
    return None
```

- [ ] **Step 4: 통과 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_advisor_advice.py`
Expected: 4 passed

---

### Task 2: 리드 DTO 교체와 조언 문장 조립

**Files:**
- Modify: `backend/apps/engine/app/dtos/scenario_dto.py:142-152` (`AdvisorLeadDTO`)
- Modify: `backend/apps/engine/app/use_cases/advisor_advice.py`
- Test: `backend/tests/engine/test_advisor_advice.py`

**Interfaces:**
- Consumes: 공개 관찰 객체(`observation_id`, `text`, `actor`, `loop_n`, `scene_title` 속성)
- Produces:
  - `AdvisorLeadDTO(key, loop_n, cues, anchor_cues, target, ask: str | None = None, rule_action: str | None = None)` — `ask`와 `rule_action` 중 정확히 하나
  - `find_anchor(lead, observations) -> observation | None` — `anchor_cues` 중 하나라도 `text`에 포함된 가장 최근(리스트 뒤쪽) 관찰
  - `advice_sentence(lead, anchor) -> str`

- [ ] **Step 1: 실패하는 테스트 추가**

```python
# backend/tests/engine/test_advisor_advice.py (추가)
import pytest
from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
from apps.engine.app.use_cases.advisor_advice import find_anchor, advice_sentence


def _lead(**kw):
    base = dict(key="band", loop_n=2, cues=["손목띠"], anchor_cues=["손목띠", "띠"], target="준",
                rule_action="가진 것을 보여준다")
    base.update(kw)
    return AdvisorLeadDTO(**base)


def test_lead_requires_exactly_one_of_ask_or_rule_action():
    with pytest.raises(ValueError):
        AdvisorLeadDTO(key="x", loop_n=1, cues=[], anchor_cues=["a"], target="준")
    with pytest.raises(ValueError):
        AdvisorLeadDTO(key="x", loop_n=1, cues=[], anchor_cues=["a"], target="준", ask="a", rule_action="b")


def test_find_anchor_prefers_latest_matching_observation():
    obs = [NS(text="준이 손목띠를 불빛에 비춰 본다.", actor="준", loop_n=1, scene_title="오전"),
           NS(text="채연이 쟁반을 밀어낸다.", actor="채연", loop_n=1, scene_title="정오"),
           NS(text="준이 숫자가 적힌 띠를 들여다본다.", actor="준", loop_n=2, scene_title="오전")]
    assert find_anchor(_lead(), obs) is obs[2]
    assert find_anchor(_lead(anchor_cues=["거울"]), obs) is None


def test_advice_sentence_forms():
    anchor = NS(text="준이 손목띠를 불빛에 비춰 본다.", actor="준", loop_n=1, scene_title="오전")
    assert advice_sentence(_lead(), anchor) == "네 기록의 「준이 손목띠를 불빛에 비춰 본다.」. 준: 가진 것을 보여준다 규칙을 걸어 봐라."
    ask = _lead(rule_action=None, ask="손목띠 밑에 뭐가 있는지")
    assert advice_sentence(ask, anchor) == "네 기록의 「준이 손목띠를 불빛에 비춰 본다.」. 내일 준에게 손목띠 밑에 뭐가 있는지 물어봐라."
```

- [ ] **Step 2: 실패 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_advisor_advice.py`
Expected: FAIL — `AdvisorLeadDTO` has no field `anchor_cues` / `find_anchor` not defined

- [ ] **Step 3: DTO 교체**

`backend/apps/engine/app/dtos/scenario_dto.py`의 `AdvisorLeadDTO`를 아래로 바꾼다 (`text`·`direction` 제거).

```python
class AdvisorLeadDTO(BaseModel):
    """신의 질문 뒤에 붙는 조언 — 세계 구조(인물 지식·잠재 행동)만 가리킨다. 숨은 사실은 싣지 않는다 (기획서 5.6)."""

    model_config = ConfigDict(extra="forbid")

    key: str  # 한 판 1회 dedup 식별자 (노트 source_key)
    loop_n: int = Field(ge=1, le=5)  # 이 회차부터 후보
    cues: list[str] = Field(default_factory=list)  # 질문 매칭 키워드
    anchor_cues: list[str]  # 플레이어 공개 관찰에서 닻을 찾는 키워드 — 없으면 조언 생략
    target: str  # 다음 낮에 물을 인물 또는 규칙 대상
    ask: str | None = None  # "…을 물어봐라"의 목적어
    rule_action: str | None = None  # "{target}: {action} 규칙을 걸어 봐라"

    @model_validator(mode="after")
    def _one_of(self):
        if bool(self.ask) == bool(self.rule_action):
            raise ValueError("ask와 rule_action 중 정확히 하나를 채운다")
        return self
```

파일 상단 import에 `model_validator`가 없으면 `from pydantic import BaseModel, ConfigDict, Field, model_validator`로 추가한다.

- [ ] **Step 4: 조언 조립 구현**

`advisor_advice.py`에 추가:

```python
def find_anchor(lead, observations):
    for observation in reversed(list(observations)):
        if any(cue in observation.text for cue in lead.anchor_cues):
            return observation
    return None


def advice_sentence(lead, anchor) -> str:
    head = f"네 기록의 「{anchor.text}」."
    if lead.ask:
        return f"{head} 내일 {lead.target}에게 {lead.ask} 물어봐라."
    return f"{head} {lead.target}: {lead.rule_action} 규칙을 걸어 봐라."
```

- [ ] **Step 5: 통과 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_advisor_advice.py`
Expected: 7 passed. 이 시점에 `adapter.py`의 옛 리드 표 때문에 전체 스위트는 깨진다 — Task 3에서 고친다.

---

### Task 3: 시나리오 리드 표 재작성과 준·은상 지식·잠재 행동 추가

**Files:**
- Modify: `backend/apps/scenarios/scenario_a/adapter.py:507-537` (advisor_leads), `:181-186` (준 knowledge), `:156-159` (은상 knowledge), scene_actions의 dormant 블록 끝(`"밤에 깨어 있는다"` 항목 뒤)
- Test: `backend/tests/engine/test_domain_p1.py` 또는 새 `backend/tests/engine/test_scenario_leads.py`

**Interfaces:**
- Produces: `bundle.advisor_leads` 10개, 전부 새 DTO 형식. 준 지식 2개·은상 지식 1개 추가. 잠재 행동 `준: 포대를 들여다본다`(beat 3).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# backend/tests/engine/test_scenario_leads.py
from apps.scenarios.scenario_a.adapter import build


def test_leads_only_point_at_world_structure():
    bundle = build().bundle()
    knowledge_targets = {c.name for c in bundle.characters for _ in c.knowledge}
    dormant = {(a.actor, a.action) for a in bundle.scene_actions if a.dormant}
    assert len(bundle.advisor_leads) == 10
    for lead in bundle.advisor_leads:
        assert not hasattr(lead, "text")
        if lead.rule_action:
            assert (lead.target, lead.rule_action) in dormant, lead.key
        else:
            assert lead.target in knowledge_targets, lead.key
    assert "ration-truck" not in {l.key for l in bundle.advisor_leads}


def test_jun_knows_sack_letters_and_mirror_absence():
    bundle = build().bundle()
    jun = next(c for c in bundle.characters if c.code == "jun")
    ids = {k.id for k in jun.knowledge}
    assert {"jun-before-start-sack", "jun-before-start-face"} <= ids
    assert any(a.actor == "준" and a.action == "포대를 들여다본다" and a.dormant and a.beat == 3
               for a in bundle.scene_actions)
```

- [ ] **Step 2: 실패 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_scenario_leads.py`
Expected: FAIL — 옛 `AdvisorLeadDTO(text=...)` 생성에서 ValidationError

- [ ] **Step 3: 리드 표 교체**

`adapter.py`의 `advisor_leads=[ ... ]` 블록 전체를 아래로 교체한다.

```python
        advisor_leads=[
            AdvisorLeadDTO(key="checkup-paper", loop_n=1, cues=["검진", "아프", "열", "담당"],
                anchor_cues=["검진", "이마"], target="민석", ask="검진이 끝난 뒤 무엇을 적었는지"),
            AdvisorLeadDTO(key="broadcast-door", loop_n=1, cues=["방송", "관리자", "보고"],
                anchor_cues=["방송실"], target="은상", rule_action="따라간다"),
            AdvisorLeadDTO(key="ration-source", loop_n=1, cues=["배급", "밥", "쟁반", "포대"],
                anchor_cues=["배급"], target="준", ask="배급이 어디서 오는지"),
            AdvisorLeadDTO(key="truck-night", loop_n=2, cues=["트럭", "이송", "충식", "돌아오"],
                anchor_cues=["이송", "실려", "트럭"], target="준", rule_action="밤에 깨어 있는다"),
            AdvisorLeadDTO(key="band-number", loop_n=2, cues=["손목띠", "숫자", "번호", "귀표"],
                anchor_cues=["손목띠", "띠"], target="준", rule_action="가진 것을 보여준다"),
            AdvisorLeadDTO(key="rumor-half", loop_n=3, cues=["소문", "은상", "속닥", "들었"],
                anchor_cues=["속닥", "귓속말", "소문"], target="은상", rule_action="들은 것을 그대로 전한다"),
            AdvisorLeadDTO(key="blanket-quiet", loop_n=3, cues=["담요", "채연", "검진"],
                anchor_cues=["담요"], target="채연", ask="검진에서 무슨 말을 들었는지"),
            AdvisorLeadDTO(key="sack-letters", loop_n=4, cues=["글자", "포대", "바깥", "트럭"],
                anchor_cues=["포대"], target="준", rule_action="포대를 들여다본다"),
            AdvisorLeadDTO(key="no-mirror", loop_n=4, cues=["거울", "얼굴", "모습"],
                anchor_cues=["거울"], target="준", ask="네 얼굴을 본 적이 있는지"),
            AdvisorLeadDTO(key="door-handle", loop_n=5, cues=["문", "손잡이", "밖", "나가"],
                anchor_cues=["손잡이", "문"], target="준", ask="문손잡이가 왜 저렇게 높은지"),
        ],
```

- [ ] **Step 4: 지식·잠재 행동 추가**

준 `knowledge` 리스트(`jun-before-start-told-eunsang` 뒤)에 두 줄:

```python
                    KnowledgeDTO(id="jun-before-start-sack", kind="observed", text="배급 포대 옆면에 글자가 있다. 읽을 줄 몰라서 무슨 뜻인지는 모른다."),
                    KnowledgeDTO(id="jun-before-start-face", kind="observed", text="여기서 내 얼굴을 본 적이 없다. 다른 애들 얼굴은 안다고 생각했는데 설명하려니 못 하겠다."),
```

은상 `knowledge` 리스트(`eunsang-before-start-checkup` 뒤)에 한 줄:

```python
                    KnowledgeDTO(id="eunsang-before-start-face", kind="observed", text="거울을 본 기억이 없다. 내 얼굴이 어떻게 생겼는지 모른다."),
```

`scene_actions`의 dormant 블록 마지막(`준: 밤에 깨어 있는다`) 뒤에:

```python
            SceneActionDTO(beat=3, actor="준", action="포대를 들여다본다", witnesses=["민석"], dormant=True,
                narration="준이 배급대 밑의 포대를 끌어내 옆면을 들여다본다. 큰 글자가 찍혀 있는데 아무도 읽지 못한다.",
                explanation="포대 옆에 글자가 있길래 봤어. 못 읽겠어. 트럭 옆에 있던 거랑 비슷한데.",
                suppressed_narration="준은 포대를 건드리지 않는다."),
```

행동 어휘 목록(`adapter.py` ~487-506, `action_vocabulary` 원천)에 `"포대를 들여다본다"`를 추가한다. 위치는 `"밤에 깨어 있는다"` 옆.

- [ ] **Step 5: 통과 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_scenario_leads.py`
Expected: 2 passed

---

### Task 4: `ask()` 재조립 — 판정·근거·조언, 리드 text 제거, 검사 추가

**Files:**
- Modify: `backend/apps/engine/app/use_cases/intervention_interactor.py:246-370` (`ask`), `:63-74` (`select_lead` 유지)
- Test: `backend/tests/engine/test_usecase_intervention.py`

**Interfaces:**
- Consumes: Task 1·2의 함수, `self._advisor_leads`(새 DTO)
- Produces: `ask()` 반환에 `verdict: str` 추가, `answer`는 `"{verdict_prefix} {본문}"` 형식, `unlocked_note`는 항상 `None`(필드는 유지), `next_observation`은 조언 문장 또는 `None`, 이벤트 `InterventionQuestionEvent.unlocked_note=None`

- [ ] **Step 1: 기존 리드 테스트 3개를 새 동작으로 교체**

`tests/engine/test_usecase_intervention.py`에서 `make_lead`와 `test_question_unlocks_lead_note_and_direction_even_on_fallback`, `test_same_lead_is_not_unlocked_twice`, `test_future_loop_lead_stays_locked`를 아래로 바꾼다.

```python
def make_lead(key="k1", loop_n=1, cues=("배급",), anchor_cues=("배급",), target="채연",
              ask="배급이 어디서 오는지", rule_action=None):
    from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
    return AdvisorLeadDTO(key=key, loop_n=loop_n, cues=list(cues), anchor_cues=list(anchor_cues),
                          target=target, ask=ask, rule_action=rule_action)


```

> 닻 재료는 이 파일에 이미 있는 `publish_scene_action(inter, night, action, rule_id=None)` 헬퍼(F5 때 추가, `action-1-채연-{action}` 키로 관찰 공개)를 쓴다. 헬퍼가 관찰 ID를 반환하지 않으면 `return observation.observation_id`를 붙여 반환하게 고친다. 닻 문장이 필요한 테스트는 `action` 문자열에 닻 단어("배급")를 넣는다.

```python
def test_advice_is_anchored_to_player_record_and_not_a_hidden_fact(db_session):
    lead = make_lead(anchor_cues=("배급",), target="준", ask="배급이 어디서 오는지")
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["unlocked_note"] is None
    assert "한 가지 더" not in res["answer"]
    assert res["next_observation"].startswith("네 기록의 「")
    assert res["next_observation"].endswith("내일 준에게 배급이 어디서 오는지 물어봐라.")
    assert res["answer"].startswith("왜인지는 내가 말할 수 없다.")
    notes = NoteRepository(db_session).list(attempt.id)
    assert any(n.source_key == "advisor-lead-k1" for n in notes)


def test_advice_is_skipped_without_anchor(db_session):
    lead = make_lead(anchor_cues=("거울",))
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["next_observation"] is None or "네 기록의" not in res["next_observation"]
    assert not any(n.source_key.startswith("advisor-lead-") for n in NoteRepository(db_session).list(attempt.id))


def test_same_lead_is_not_advised_twice(db_session):
    lead = make_lead()
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    first = inter.ask(night.id, "배급이 왜 이래?")
    second = inter.ask(night.id, "배급 얘기 또 물을게")
    assert "네 기록의" in first["next_observation"]
    assert second["next_observation"] is None or "네 기록의" not in second["next_observation"]


def test_future_loop_lead_stays_locked(db_session):
    lead = make_lead(loop_n=3)
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["next_observation"] is None or "네 기록의" not in res["next_observation"]


def test_fact_question_gets_verdict_prefix(db_session):
    inter, attempt, night = make_intervention(db_session, [
        {"question_kind": "proposition", "answer": "채연은 쟁반을 반쯤 남기고 옆으로 밀었다.",
         "evidence": []}])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert res["answer"].split(" ", 1)[0] in {"맞다.", "그건", "아니다."}
    assert res["verdict"] in {"맞다.", "아니다.", "그건 알 수 없다."}


def test_polite_register_triggers_regeneration(db_session):
    polite = {"question_kind": "proposition", "answer": "채연은 쟁반을 남겼습니다.", "evidence": []}
    plain = {"question_kind": "proposition", "answer": "채연은 쟁반을 남겼다.", "evidence": []}
    inter, attempt, night = make_intervention(db_session, [polite, plain])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert "습니다" not in res["answer"]
    reports = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "harness_event"]
    assert reports[-1].attempts == 2
```

> `make_intervention`의 큐 항목 형식은 이 파일의 다른 테스트(`test_open_question_cites_original_observation_without_promoting_a_new_fact` 등)가 `AdvisorReplyOutput` JSON dict를 넣는 방식을 그대로 따른다 — 그 테스트를 열어 정확한 dict 형태(특히 `evidence` 항목의 `id`/`quote`/`relation`)를 복사한다.

- [ ] **Step 2: 실패 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_usecase_intervention.py`
Expected: 새 테스트 6개 FAIL(`verdict` 키 없음, `한 가지 더` 존재 등), 나머지는 PASS 유지

- [ ] **Step 3: `ask()` 수정**

`intervention_interactor.py` 상단 import에 추가:

```python
from apps.engine.app.use_cases.advisor_advice import (
    advice_sentence, find_anchor, is_why_question, polite_register_check,
    unbacked_confirmation_check, verdict_prefix,
)
```

`task = (...)` 문자열의 첫 문장 `"플레이어의 추리를 돕는 대화 상대다. 원래 질문에 자연스럽고 짧게 2~3문장으로 직접 답하라. "`를 아래로 바꾼다:

```python
                "플레이어의 추리를 돕는 목소리다. 짧은 한다체로 최대 3문장. 합니다체·습니다체는 쓰지 않는다. "
                "첫 문장은 판정이 아니라 근거다 — 판정은 시스템이 앞에 붙인다. "
                "플레이어가 이미 본 기록을 그대로 되풀이하지 말고, 기록 둘을 잇는 관계나 질문이 놓친 사실 하나를 말하라. "
```

`run_with_harness(...)` 호출의 `fact_checks=[grounding, _no_raw_record_check]`를 `fact_checks=[grounding, _no_raw_record_check, polite_register_check, unbacked_confirmation_check]`로 바꾼다.

`if status == "unknown": ... detail = "확인된 기록:..."` 블록에서 `detail += "\n" + question_limit(text)` 줄을 삭제한다(면책 문장 제거). `question_limit` 함수는 다른 참조가 없으면 함께 삭제한다(`grep -n question_limit`).

`next_observation = None` 부터 `# 질문 보상 — ...` 블록 끝(`next_observation = lead.direction`)까지를 아래로 교체한다:

```python
        why = is_why_question(text)
        verdict = verdict_prefix(status, why)
        answer = f"{verdict} {answer}".strip()
        # 조언 — 세계 구조에서만, 플레이어 기록에 닻이 있을 때만 (기획서 5.6)
        next_observation = None
        unlocked_note = None
        if self._advisor_leads:
            used = {n.source_key.removeprefix("advisor-lead-")
                    for n in self._notes.list(loop.attempt_id)
                    if n.source_key.startswith("advisor-lead-")}
            lead = select_lead(text, self._advisor_leads, used, loop.loop_n)
            anchor = find_anchor(lead, observations) if lead else None
            if lead and anchor:
                next_observation = advice_sentence(lead, anchor)
                self._notes.upsert(loop.attempt_id, kind="fragment", text=next_observation,
                                   loop_n=loop.loop_n, source_key=f"advisor-lead-{lead.key}")
        if next_observation is None and meta:
            next_observation = "원본 노트를 확인하거나 규칙 선택에서 다음 날 관찰할 행동을 고를 수 있다."
```

반환 dict와 이벤트에 `verdict`를 넣는다:

```python
        self._events.record(loop.attempt_id, ev.InterventionQuestionEvent(
            loop_n=loop.loop_n, q_index=3-night.questions_left, question=text, answer=answer,
            hit_cause_chain=bool(evidence), confirmed_note_id=None, detail=detail,
            status=status, evidence_ids=ids, next_observation=next_observation,
            unlocked_note=unlocked_note))
        return {"answer": answer, "verdict": verdict, "detail": detail, "remaining": night.questions_left,
                "status": status, "evidence_ids": ids, "evidence": [o.model_dump() for o in evidence],
                "next_observation": next_observation, "unlocked_note": unlocked_note}
```

`select_lead`는 cue 무적중이어도 가장 이른 리드를 돌려준다. 닻 조건이 있으니 그대로 둔다.

- [ ] **Step 4: 전체 스위트 통과 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests`
Expected: 기존 462 + 신규(Task1 4·Task2 3·Task3 2·Task4 6 − 교체 3) 전부 passed, 0 failed. 깨지는 기존 테스트가 있으면 그 테스트가 리드 `text`/`direction`/`question_limit` 문장을 기대하는지 확인하고 새 동작으로 갱신한다.

---

### Task 5: "맞다" 판정을 확인 노트로 저장

**Files:**
- Modify: `backend/apps/engine/app/use_cases/intervention_interactor.py` (`ask`, Task 4 코드 뒤)
- Test: `backend/tests/engine/test_usecase_intervention.py`

**Interfaces:**
- Produces: `status == "supported"`이고 `evidence`가 있으면 `notes.upsert(kind="confirmed", text=<첫 근거 text>, source_key=f"confirmed-{observation_id}")`. 프런트 밤 화면의 `KIND_ORDER`에 이미 `confirmed`가 있다(`NightScreen.tsx:16-18`).

- [ ] **Step 1: 실패하는 테스트**

```python
def test_supported_fact_is_saved_as_confirmed_note(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    obs_id = publish_scene_action(inter, night, "배급을 남긴다")
    from apps.engine.app.use_cases.public_observations import public_observations
    observation = next(o for o in public_observations(EventLogRepository(db_session), attempt.id)
                       if o.observation_id == obs_id)
    inter._llm = FakeLLM([
        {"question_kind": "proposition", "answer": "채연은 쟁반을 남겼다.",
         "evidence": [{"id": obs_id, "quote": observation.text, "relation": "supported"}]}])
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert res["status"] == "supported"
    notes = NoteRepository(db_session).list(attempt.id)
    assert any(n.kind == "confirmed" and n.source_key == f"confirmed-{obs_id}" for n in notes)
```

- [ ] **Step 2: 실패 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests/engine/test_usecase_intervention.py -k confirmed_note`
Expected: FAIL — confirmed 노트 없음

- [ ] **Step 3: 구현**

Task 4의 `verdict` 계산 직후에:

```python
        if status == "supported" and evidence:
            head = evidence[0]
            self._notes.upsert(loop.attempt_id, kind="confirmed", text=head.text,
                               loop_n=loop.loop_n, source_key=f"confirmed-{head.observation_id}")
```

- [ ] **Step 4: 통과 확인**

Run: `cd backend && PYTHONPATH=. .venv/bin/pytest -q tests`
Expected: all passed

---

### Task 6: 프런트 — 안내 한 줄·판정 라벨·"새 단서" 제거

**Files:**
- Modify: `frontend/contracts/api.ts:230-241` (`GodQuestionRes`), `frontend/components/screens/GodScreen.tsx:23-27` (STATUS_LABEL), `:205-231` (QA 렌더), `:236-262` (질문 입력)
- Test: `frontend/tests/five-loop-flow.cjs`, `frontend/tests/connected-investigation.cjs`

**Interfaces:**
- Consumes: `GodQuestionRes.verdict: string`, `next_observation`, `status`
- Produces: 질문 입력 위 안내 `<p>`: "이 목소리는 오늘 일어난 일만 안다. 무엇을 했는지 물어라." + 네 형식 칩 `맞다 · 아니다 · 그런 일은 없었다 · 그건 알 수 없다`. 답변은 판정 접두를 강조색으로.

- [ ] **Step 1: 헤드리스 기대 갱신 (실패부터)**

`five-loop-flow.cjs`와 `connected-investigation.cjs`에서 신의 질문 모의 응답에 `verdict: "맞다."`를 추가하고, `unlocked_note` 기대(`새 단서` 텍스트)를 지운다. 안내 문장 기대를 추가:

```js
await page.getByText('이 목소리는 오늘 일어난 일만 안다. 무엇을 했는지 물어라.', { exact: true }).waitFor();
assert.equal(await page.getByText('새 단서 — 노트에 적혔다').count(), 0);
```

Run: `cd frontend && NODE_PATH=... node tests/five-loop-flow.cjs` → Expected: FAIL(안내 문장 없음)

- [ ] **Step 2: 계약과 화면 수정**

`api.ts` `GodQuestionRes`에 `verdict: string;` 추가(주석: "판정 접두 — 맞다. / 아니다. / 그건 알 수 없다. / 왜인지는…").

`GodScreen.tsx`:
- QA 타입(`:12-20` 근처)에 `verdict: string` 추가, `ask()`의 setQas에 `verdict: res.verdict` 전달.
- 답변 렌더 `<p className="text-lg">{qa.answer}</p>`를 다음으로 교체:

```tsx
<p className="text-lg">
  <span className="text-orange">{qa.verdict}</span>{" "}
  {qa.answer.startsWith(qa.verdict) ? qa.answer.slice(qa.verdict.length).trim() : qa.answer}
</p>
```

- `qa.unlockedNote` 박스(`{qa.unlockedNote && (...)}`) 삭제. `unlockedNote` 필드도 타입·setQas에서 제거.
- 질문 입력 블록의 `<span className="w-full text-base opacity-70">남은 질문 {remaining}</span>` 위에:

```tsx
<p className="w-full text-base opacity-80">이 목소리는 오늘 일어난 일만 안다. 무엇을 했는지 물어라.</p>
<p className="w-full text-sm tracking-wide opacity-60">맞다 · 아니다 · 그런 일은 없었다 · 그건 알 수 없다</p>
```

- [ ] **Step 3: 검증**

Run: `cd frontend && npx tsc --noEmit` → Expected: exit 0
Run (순차): `five-loop-flow.cjs`, `connected-investigation.cjs`, `gameplay-clarity.cjs` → Expected: 모두 exit 0

---

### Task 7: 문서 동기화

**Files:**
- Modify: `docs/spec/api_contract.md` (신의 질문 응답에 `verdict` 추가, `unlocked_note`는 항상 null로 표기)
- Modify: `docs/HANDOFF-26-09-16.md` "지금 바로 할 일" 1번에 F7 완료 표기

- [ ] **Step 1: 계약 문서에 `verdict` 필드와 답변 3부 형식 설명 추가**
- [ ] **Step 2: 인계 문서 갱신**
- [ ] **Step 3: 전체 재검증** — 백엔드 전체, tsc, 헤드리스 3종(위 Task 6) 재실행 후 결과를 세션 주인에게 보고. 커밋은 하지 않는다.
