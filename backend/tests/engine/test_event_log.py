"""부록 C 이벤트 17종 — 기록·조회 왕복 테스트 (P0 완료 조건)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.app.dtos import event_log_dto as e
from apps.engine.domain.value_objects.event_type import EventType

_CELLS = {"cause": 40.0, "motive": 0.0, "side_effect": 0.0, "identity": 0.0}

SAMPLES: dict[EventType, e.EventBase] = {
    EventType.SESSION_START: e.SessionStartEvent(
        session="s-1", attempt_n=1, prior_cell_results=None
    ),
    EventType.LOOP_START: e.LoopStartEvent(
        session="s-1", loop_n=1, cumulative_loop_n=1, budget=8, rule_count=0, damage=0
    ),
    EventType.UTTERANCE: e.UtteranceEvent(
        loop_n=1,
        beat=2,
        target="A",
        text="발화",
        budget_left=7,
        suspicion_delta=4,
        trust_delta=0,
        disclosure_level=0,
    ),
    EventType.TOOL_CALL: e.ToolCallEvent(
        loop_n=1,
        beat=2,
        caller="A",
        tool="ask_npc",
        args={"target": "B"},
        result="그런 말 한 적 없음",
        side_effect="B.suspicion +6",
    ),
    EventType.MANAGER_CHECK: e.ManagerCheckEvent(
        loop_n=1,
        beat=3,
        patches=[
            e.ManagerPatch(
                npc="A", kind="memory_delete", detail="기억 삭제", reason="확산 방지"
            )
        ],
        budget_left=1,
    ),
    EventType.MONKEY_PAW_OFFER: e.MonkeyPawOfferEvent(
        loop_n=1, beat=4, offer_index=1, rule_id="R1", reason_shown=None, accepted=True
    ),
    EventType.ANSWER_DRAFT: e.AnswerDraftEvent(
        loop_n=1, tapped_note_ids=["n1", "n2"], free_text="서술"
    ),
    EventType.ANSWER_NORMALIZED: e.AnswerNormalizedEvent(
        loop_n=1, claims=["주장1", "주장2"], user_edited=False, edit_diff=None
    ),
    EventType.ANSWER_SCORED: e.AnswerScoredEvent(
        loop_n=1,
        per_truth_claim=[
            e.TruthClaimVerdict(
                id="cause-1",
                verdict="confirmed",
                matched_user_claim="주장1",
                cited_chunks=["c1"],
            )
        ],
        cell_scores=e.CellScores(**_CELLS),
        total=15.0,
        passed=False,
    ),
    EventType.ANSWER_WRONG_CLAIMS: e.AnswerWrongClaimsEvent(
        loop_n=1, claims=["오답"]
    ),
    EventType.DEATH: e.DeathEvent(
        loop_n=1, cause_chain=["c1", "c2"], world_outcome="truck", ending_cell="cause"
    ),
    EventType.INTERVENTION_QUESTION: e.InterventionQuestionEvent(
        loop_n=1,
        q_index=1,
        question="질문",
        answer="맞다",
        hit_cause_chain=True,
        confirmed_note_id="n1",
    ),
    EventType.INTERVENTION_OPTIONS: e.InterventionOptionsEvent(
        loop_n=1, options=["o1", "o2", "o3"], chosen="1", custom_text=None
    ),
    EventType.RULE_APPLIED: e.RuleAppliedEvent(
        loop_n=2, rule_id="R1", source="user_choice", conflict=False
    ),
    EventType.LOOP_END: e.LoopEndEvent(
        loop_n=1, survived=True, anomaly_count=0, rumor_index=2
    ),
    EventType.COOKIE_SHOWN: e.CookieShownEvent(
        attempt_n=1, cell="cause", level=1, text_id="ck-cause-1"
    ),
    EventType.SESSION_END: e.SessionEndEvent(
        attempt_n=1,
        final_cells=e.CellScores(**_CELLS),
        closed_by="doom",
        identity_word_confirmed=False,
    ),
    EventType.OBSERVATION: e.ObservationEvent(loop_n=1, observation=e.ObservationDTO(
        observation_id="obs1", attempt_id="a", loop_id="l", loop_n=1, beat=1,
        scene_id="s", scene_title="morning", text="A recorded an action", source_kind="scene")),
    EventType.RULE_EXECUTION: e.RuleExecutionEvent(loop_n=1, beat=1, rule_id="R1",
        condition="action opportunity", actual_action=None, result="obeyed"),
    EventType.RULE_PREVIEW: e.RulePreviewEvent(loop_n=1, night_id="n", preview={"executable": False}),
    EventType.HARNESS_EVENT: e.HarnessEvent(
        loop_n=1, beat=2, role="agent", violations=["forbidden_word: x"],
        attempts=3, fallback_used=True,
    ),
    EventType.GUARD: e.GuardEvent(
        layer="ip", reason="요청이 너무 잦다", ip_hash="abc123def456", user_sub=None
    ),
}


def test_all_event_types_have_samples():
    # 부록 C 17종 + 모델정책 §9 harness_event + 과잉 사용 방지 guard = 22
    assert set(SAMPLES) == set(EventType)
    assert len(SAMPLES) == 22


@pytest.mark.parametrize("event_type", list(EventType))
def test_record_and_query_roundtrip(db_session, event_type):
    repo = EventLogRepository(db_session)
    session_id = uuid4()
    event = SAMPLES[event_type]

    repo.record(session_id, event)
    found = repo.query(session_id, type=event_type)

    assert len(found) == 1
    assert found[0] == event


def test_query_filters_by_type_and_loop(db_session):
    repo = EventLogRepository(db_session)
    session_id = uuid4()
    repo.record(session_id, SAMPLES[EventType.UTTERANCE])  # loop_n=1
    repo.record(session_id, SAMPLES[EventType.RULE_APPLIED])  # loop_n=2
    repo.record(uuid4(), SAMPLES[EventType.UTTERANCE])  # 다른 세션

    assert len(repo.query(session_id)) == 2
    assert len(repo.query(session_id, type=EventType.UTTERANCE)) == 1
    assert len(repo.query(session_id, loop_n=2)) == 1


def test_missing_required_field_is_rejected():
    with pytest.raises(ValidationError):
        e.UtteranceEvent(loop_n=1, beat=2, target="A", text="발화")  # 나머지 필드 누락


def test_unknown_extra_field_is_rejected():
    with pytest.raises(ValidationError):
        e.LoopEndEvent(
            loop_n=1, survived=True, anomaly_count=0, rumor_index=0, extra="x"
        )


def test_claims_over_8_rejected():
    with pytest.raises(ValidationError):
        e.AnswerNormalizedEvent(
            loop_n=1, claims=[f"c{i}" for i in range(9)], user_edited=False, edit_diff=None
        )
