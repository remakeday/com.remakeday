"""밤 채점 — 주장 매칭(인덱스 기반)·원인 체인 입력 필터 (FakeLLM 큐로 제어)."""

import uuid
from types import SimpleNamespace

import pytest

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.use_cases.night_interactor import (
    NightInteractor,
    chain_source_events,
)
from apps.engine.domain.value_objects.event_type import EventType


class _RecorderEvents:
    def __init__(self):
        self.recorded = []

    def record(self, session_id, event):
        self.recorded.append(event)


def make_night_judge(core_queue):
    events = _RecorderEvents()
    interactor = NightInteractor(
        attempts=None, loops=None, notes=None, rules=None, nights=None,
        event_log=events, scenario=None, core_llm=FakeLLM(core_queue),
        harness_on=True, cookie_ab_on=False, night_cls=None,
    )
    return interactor, events


_LOOP = SimpleNamespace(attempt_id=uuid.uuid4(), loop_n=1)
_TRUTH = [SimpleNamespace(
    code="cause-1", cell="cause", text="채연이 아프다", is_identity_word=False,
)]


def draft_answer(source, notes=()):
    loop = SimpleNamespace(
        id=uuid.uuid4(), attempt_id=uuid.uuid4(), loop_n=1, state="night_pending",
    )
    saved = []
    interactor = NightInteractor(
        attempts=None, loops=SimpleNamespace(get=lambda _: loop, save=lambda: None),
        notes=SimpleNamespace(by_ids=lambda *_: [SimpleNamespace(text=t) for t in notes]),
        rules=None, nights=SimpleNamespace(for_loop=lambda _: None, create=saved.append),
        event_log=_RecorderEvents(), scenario=None,
        core_llm=FakeLLM([{"claims": ["채연은 아픈 것을 숨겼다."]}]),
        harness_on=True, cookie_ab_on=False,
        night_cls=lambda **kw: SimpleNamespace(id=uuid.uuid4(), **kw),
    )
    result = interactor.draft(loop.id, list(range(len(notes))), source)
    return result["claims"], saved[0]


@pytest.mark.parametrize("source", [
    "채연은 열이 나서 아프다. 채연은 이송될까 봐 아픈 것을 숨겼다.",
    "채연은 열이 나서 아프다.\n채연은 이송될까 봐 아픈 것을 숨겼다.",
])
def test_draft_preserves_illness_and_motive_across_line_breaks(source):
    claims, _ = draft_answer(source)
    assert claims == ["채연은 열이 나서 아프다.", "채연은 이송될까 봐 아픈 것을 숨겼다."]


def test_draft_keeps_facts_after_eighth_sentence():
    source = "하나. 둘. 셋. 넷. 다섯. 여섯. 일곱. 여덟. 아홉. 우리는 돼지다."
    claims, _ = draft_answer(source)
    assert claims == ["하나.", "둘.", "셋.", "넷.", "다섯.", "여섯.", "일곱.", "여덟. 아홉. 우리는 돼지다."]


def test_draft_keeps_selected_notes_without_free_text():
    claims, _ = draft_answer("", ["소독약 냄새.", "트럭 소리."])
    assert claims == ["소독약 냄새.", "트럭 소리."]


def test_draft_keeps_selected_notes_after_long_free_text():
    claims, _ = draft_answer("하나. 둘. 셋. 넷. 다섯. 여섯. 일곱. 여덟.", ["관리자는 다른 종이다."])
    assert claims[-1] == "여덟. 관리자는 다른 종이다."


@pytest.mark.parametrize("source", [
    "우리는 돼지가 아니다. 아마 사람인 것 같다.",
    "체온은 38.5도다. 채연은 열이 없다고 했다.",
    "채연은 이송될까 봐 아픈 것을 숨겼고 그래서 검진에서 열을 발견하지 못했다",
    "나는 무서웠다! 왜 이럴까?",
])
def test_draft_does_not_rewrite_negation_uncertainty_numbers_or_causal_links(source):
    claims, night = draft_answer(source)
    assert " ".join(claims) == source
    assert night.fabricated_dropped == []


def test_empty_draft_does_not_invent_claims():
    claims, _ = draft_answer(" \n ")
    assert claims == []


def test_matched_index_excludes_claim_from_wrong():
    interactor, _ = make_night_judge(
        [{"verdict": "confirmed", "matched_index": 0, "why": ""}]
    )
    claims = ["채연이 아픈 것 같다", "민석이 방송실 갔다"]
    per_truth, wrong = interactor._judge(_LOOP, _TRUTH, [], claims)
    assert per_truth[0]["verdict"] == "confirmed"
    assert per_truth[0]["matched_user_claim"] == "채연이 아픈 것 같다"
    assert wrong == ["민석이 방송실 갔다"]


def test_judge_renders_all_user_claims_as_candidates():
    # 유저 주장은 최대 8개 — top3로 자르지 않고 전부 후보로 넣는다
    interactor, _ = make_night_judge(
        [{"verdict": "confirmed", "matched_index": 4, "why": ""}]
    )
    claims = [
        "민석이 방송실 갔다", "은상이 소문을 냈다", "배급이 늦게 나왔다",
        "준이 손목띠를 봤다", "채연이 아픈 것 같다",
    ]
    per_truth, wrong = interactor._judge(_LOOP, _TRUTH, [], claims)
    assert per_truth[0]["verdict"] == "confirmed"
    assert per_truth[0]["matched_user_claim"] == "채연이 아픈 것 같다"
    assert per_truth[0]["cited"] == claims  # 후보 전수
    assert "채연이 아픈 것 같다" not in wrong


def test_out_of_range_index_regenerates_then_falls_back():
    bad = {"verdict": "confirmed", "matched_index": 7, "why": ""}
    interactor, events = make_night_judge([bad, bad, bad])
    claims = ["채연이 아픈 것 같다"]
    per_truth, wrong = interactor._judge(_LOOP, _TRUTH, [], claims)
    assert per_truth[0]["verdict"] == "none"
    assert per_truth[0]["matched_user_claim"] is None
    assert wrong == claims
    # 범위 밖 인덱스는 하네스에서 거부돼야 한다.
    assert any(
        "matched_index" in v for e in events.recorded for v in e.violations
    )


@pytest.mark.parametrize(("claims", "expected"), [
    (["채연이 아프다 채연이 숨겼다 우리는 돼지다"], [{"const": 0, "type": "integer"}, {"type": "null"}]),
    (["채연이 아프다", "채연이 숨겼다", "우리는 돼지다"], [{"enum": [0, 1, 2], "type": "integer"}, {"type": "null"}]),
])
def test_judge_exposes_only_existing_candidate_indices_to_model(claims, expected):
    interactor, _ = make_night_judge([{"verdict": "confirmed", "matched_index": 0}])
    interactor._judge(_LOOP, _TRUTH, [], claims)
    schema = interactor._llm.calls[0][1]
    # 후보 안의 절 번호(2, 5, 7)를 만들어 내던 실제 모델 응답 재현.
    choices = schema["properties"]["matched_index"]["anyOf"]
    assert choices == expected


def test_chain_source_events_excludes_user_claims_and_meta():
    events = [
        ev.UtteranceEvent(
            loop_n=1, beat=1, target="채연", text="왜 남겼어?", reply="그냥.",
            budget_left=5, suspicion_delta=0, trust_delta=0, disclosure_level=0,
        ),
        ev.AnswerNormalizedEvent(
            loop_n=1, claims=["채연이 아프다"], user_edited=False, edit_diff=None,
        ),
        ev.AnswerWrongClaimsEvent(loop_n=1, claims=["민석이 감염됐다"]),
        ev.InterventionQuestionEvent(
            loop_n=1, q_index=1, question="누가?", answer="맞다",
            hit_cause_chain=True, confirmed_note_id=None,
        ),
        ev.RuleAppliedEvent(loop_n=1, rule_id="R1", source="user_choice", conflict=False),
    ]
    kept = chain_source_events(events)
    assert [e.type for e in kept] == [EventType.UTTERANCE, EventType.RULE_APPLIED]
