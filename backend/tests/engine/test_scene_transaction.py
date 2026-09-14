"""Actual PostgreSQL fault injection for atomic scene disclosure and independent audit."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
from apps.engine.adapter.outbound.repositories.game_repository import LoopRepository, RuleRepository
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION
from tests.engine.test_usecase_day import make_day


def test_failed_note_write_rolls_back_scene_and_retry_returns_same_scene_once(db_session):
    day, _, attempt, info = make_day(db_session, [])
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="monkey_paw",
        target="채연", action=EXPLAIN_ACTION, effect="enforce", when_beat=3, created_loop=0))
    day.advance_beat(info["loop_id"])
    before = LoopRepository(db_session).get(info["loop_id"]).budget_left
    upsert = day._notes.upsert
    failed = False
    def failing_upsert(*args, **kwargs):
        nonlocal failed
        if not failed:
            failed = True
            db_session.execute(text("SELECT 1 / 0"))
        return upsert(*args, **kwargs)
    day._notes.upsert = failing_upsert

    with pytest.raises(DBAPIError):
        day.advance_beat(info["loop_id"])
    # The use-case boundary must have rolled back even PostgreSQL's aborted transaction.
    db_session.expire_all()
    loop = LoopRepository(db_session).get(info["loop_id"])
    assert (loop.beat, loop.budget_left) == (2, before)
    assert not any(o["beat"] == 3 for o in day.list_observations(loop.id)["observations"])
    retried = day.advance_beat(loop.id)
    assert retried["beat"] == 3 and retried["budget_left"] == before - 1
    observations = [o for o in day.list_observations(loop.id)["observations"] if o["beat"] == 3]
    assert len({o["observation_id"] for o in observations}) == len(observations)
    sources = {source for note in day.list_notes(loop.id)["notes"] for source in note["observation_ids"]}
    assert all(o["observation_id"] in sources for o in observations)
    costs = [e for e in EventLogRepository(db_session).query(attempt.id)
             if e.type == "rule_execution" and e.beat == 3 and e.side_effect]
    assert len(costs) == 1


def test_authored_ambient_survives_provider_outage_without_a_model_call(db_session):
    class DownProvider:
        def complete(self, *_args, **_kwargs):
            raise RuntimeError("provider unavailable")
    day, _, attempt, info = make_day(db_session, [])
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="monkey_paw",
        target="채연", action=EXPLAIN_ACTION, effect="enforce", when_beat=3, created_loop=0))
    day.advance_beat(info["loop_id"])
    before = LoopRepository(db_session).get(info["loop_id"]).budget_left
    day._npc_llm = DownProvider()
    scene = day.advance_beat(info["loop_id"])
    assert scene["beat"] == 3 and scene["budget_left"] == before - 1
    assert scene["ambient"] is not None  # Authored dialogue does not depend on the provider.
    failures = [e for e in EventLogRepository(db_session).query(attempt.id)
                if e.type == "harness_event" and e.role == "ambient" and e.beat == 3]
    assert failures == []


def test_first_scene_rollback_keeps_completed_planner_call_audit(db_session):
    day, _, attempt, info = make_day(db_session, [])
    first = LoopRepository(db_session).get(info["loop_id"])
    first.state = "closed"
    db_session.commit()
    def fail_note(*_args, **_kwargs):
        db_session.execute(text("SELECT 1 / 0"))
    day._notes.upsert = fail_note
    with pytest.raises(DBAPIError):
        day.start_loop(attempt.id)
    db_session.expire_all()
    assert LoopRepository(db_session).latest_for(attempt.id).loop_n == 1
    audit = [e for e in EventLogRepository(db_session).query(attempt.id)
             if e.type == "harness_event" and e.role == "planner" and e.loop_n == 2]
    assert len(audit) == 1 and len(audit[0].call_records) == 3
    assert not any(e.type == "observation" and e.loop_n == 2
                   for e in EventLogRepository(db_session).query(attempt.id))
