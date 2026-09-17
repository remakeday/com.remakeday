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
    assert retried["beat"] == 3 and retried["budget_left"] == before  # F11: 원숭이손 예산 대가 폐기
    observations = [o for o in day.list_observations(loop.id)["observations"] if o["beat"] == 3]
    assert len({o["observation_id"] for o in observations}) == len(observations)
    sources = {source for note in day.list_notes(loop.id)["notes"] for source in note["observation_ids"]}
    assert all(o["observation_id"] in sources for o in observations)
    executions = [e for e in EventLogRepository(db_session).query(attempt.id)
                  if e.type == "rule_execution" and e.beat == 3 and e.rule_id == "R1"]
    assert len(executions) == 1


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
    assert scene["beat"] == 3 and scene["budget_left"] == before  # F11: 원숭이손 예산 대가 폐기
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


# 비용 동시성 후속(5b) — 밤 제출·회차 시작·낮 장면도 잠금을 기다리지 않는다(NOWAIT, opus 리뷰 C1과 같은 원칙).
# 실제 DB 세션 둘 + 컴포지션 루트 배선. 앞 요청을 잠금 안에 세워 두고 뒤 요청을 보낸다.
_HOLD_LIMIT = 10  # 안전 상한 — 정상 경로에서는 테스트가 곧바로 풀어 준다


class _HeldOnce:
    """첫 호출만 테스트가 풀어 줄 때까지 멈춘다. 나머지 호출은 곧바로 답한다(재생성·병렬 판정)."""
    def __init__(self, reply=None):
        import threading
        self.calls, self.entered, self.release = 0, threading.Event(), threading.Event()
        self._reply, self._lock = reply or {}, threading.Lock()

    def complete(self, *_args, **_kwargs):
        with self._lock:
            self.calls += 1
            first = self.calls == 1
        if first:
            self.entered.set()
            self.release.wait(_HOLD_LIMIT)
        return dict(self._reply)


def _own_session(db_session, factory, work):
    """요청 하나 = 실제 세션 하나. 예외도 결과로 돌려준다."""
    from sqlalchemy.orm import Session
    with Session(db_session.get_bind()) as session:
        try:
            return work(factory(session))
        except Exception as exc:  # 결과로 비교한다
            return exc


def _while_first_is_held(db_session, first, second, *, entered, release):
    """뒤 요청이 돌아온 순간 앞 요청이 아직 멈춰 있어야 "기다리지 않고" 답한 것이다."""
    import threading
    outcome = {}
    worker = threading.Thread(target=lambda: outcome.update(first=first()))
    worker.start()
    try:
        assert entered.wait(_HOLD_LIMIT)
        outcome["second"] = second()
        outcome["first_still_held"] = worker.is_alive()
    finally:
        release.set()
        worker.join(_HOLD_LIMIT * 2)
    db_session.expire_all()
    return outcome


def _events(db_session, attempt_id, kind):
    return [e for e in EventLogRepository(db_session).query(attempt_id) if e.type == kind]


def test_second_submit_while_scoring_is_409_without_a_second_scoring(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm
    from apps.engine.adapter.outbound.repositories.game_repository import NightRepository
    from apps.engine.app.use_cases.night_interactor import GameStateError
    from apps.engine.dependencies.engine_dependency import get_night_interactor
    _, _, attempt, info = make_day(db_session, [])
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.state, loop.beat = "night_draft", 6
    night = NightRepository(db_session).create(NightOrm(
        loop_id=loop.id, free_text="채연이 밥을 남겼다.", claims=["채연이 밥을 남겼다."]))
    model = _HeldOnce()

    def submit():
        def work(inter):
            inter._llm = model
            return inter.submit(night.id)
        return _own_session(db_session, get_night_interactor, work)
    outcome = _while_first_is_held(db_session, submit, submit, entered=model.entered, release=model.release)
    assert outcome["first_still_held"]
    assert isinstance(outcome["second"], GameStateError) and "채점하는 중" in str(outcome["second"])
    assert isinstance(outcome["first"], dict)
    scored = _events(db_session, attempt.id, "answer_scored")
    assert len(scored) == 1
    verdict_calls = [e for e in _events(db_session, attempt.id, "harness_event") if e.role == "evaluator_verdict"]
    assert verdict_calls and len(verdict_calls) == len(scored[0].per_truth_claim)  # 채점 1벌
    assert NightRepository(db_session).get(night.id).submitted


def test_second_loop_start_while_planning_is_409_without_waiting(db_session):
    from apps.engine.app.use_cases.loop_interactor import GameStateError
    from apps.engine.dependencies.engine_dependency import get_loop_interactor
    _, _, attempt, info = make_day(db_session, [])
    LoopRepository(db_session).get(info["loop_id"]).state = "closed"
    db_session.commit()
    model = _HeldOnce()

    def start():
        def work(inter):
            inter._core_llm = model
            return inter.start_loop(attempt.id)
        return _own_session(db_session, get_loop_interactor, work)
    outcome = _while_first_is_held(db_session, start, start, entered=model.entered, release=model.release)
    assert outcome["first_still_held"]
    assert isinstance(outcome["second"], GameStateError) and "하루를 준비하는 중" in str(outcome["second"])
    assert isinstance(outcome["first"], dict) and outcome["first"]["loop_n"] == 2
    assert LoopRepository(db_session).latest_for(attempt.id).loop_n == 2
    planner = [e for e in _events(db_session, attempt.id, "harness_event") if e.role == "planner" and e.loop_n == 2]
    assert len(planner) == 1


def test_next_scene_while_the_scene_is_running_is_409_without_waiting(db_session):
    import threading
    from apps.engine.app.use_cases.loop_interactor import GameStateError
    from apps.engine.dependencies.engine_dependency import get_loop_interactor
    _, _, attempt, info = make_day(db_session, [])
    entered, release = threading.Event(), threading.Event()

    def advance(*, hold):
        def work(inter):
            if hold:
                listed = inter._rules.list

                def held(*args):  # 장면 실행이 규칙을 읽는 순간(잠금 안)에서 멈춘다
                    entered.set()
                    release.wait(_HOLD_LIMIT)
                    return listed(*args)
                inter._rules.list = held
            return inter.advance_beat(info["loop_id"])
        return lambda: _own_session(db_session, get_loop_interactor, work)
    outcome = _while_first_is_held(db_session, advance(hold=True), advance(hold=False),
                                   entered=entered, release=release)
    assert outcome["first_still_held"]
    assert isinstance(outcome["second"], GameStateError) and type(outcome["second"]).__name__ == "RequestInFlight"
    assert outcome["first"]["beat"] == 2
    assert LoopRepository(db_session).get(info["loop_id"]).beat == 2  # 한 칸만


def test_request_in_flight_maps_to_409_with_a_retry_code():
    import json
    from apps.engine.adapter.inbound.api.v1.game_router import _run
    from apps.engine.app.use_cases.loop_interactor import RequestInFlight

    def busy():
        raise RequestInFlight("앞 대화를 처리하는 중이다.")
    response = _run(busy)
    assert response.status_code == 409
    assert json.loads(response.body) == {"code": "request_in_flight", "detail": "앞 대화를 처리하는 중이다."}


# opus 최종 리뷰 반영(수정 1회) — I1·I2·M1·M3·M4.

def _scoring_night(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm
    from apps.engine.adapter.outbound.repositories.game_repository import NightRepository
    _, _, attempt, info = make_day(db_session, [])
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.state, loop.beat = "night_draft", 6
    night = NightRepository(db_session).create(NightOrm(
        loop_id=loop.id, free_text="채연이 밥을 남겼다.", claims=["채연이 밥을 남겼다."]))
    return attempt, loop, night


def _submitter(db_session, night_id, model):
    from apps.engine.dependencies.engine_dependency import get_night_interactor

    def submit():
        def work(inter):
            inter._llm = model
            return inter.submit(night_id)
        return _own_session(db_session, get_night_interactor, work)
    return submit


def test_submit_in_flight_carries_the_retry_code(db_session):
    """채점 중 재제출은 request_in_flight — 프론트가 잠시 뒤 다시 보내면 저장된 결과를 받는다 (I2·M3)."""
    from apps.engine.app.ports.output.scene_transaction_port import RequestInFlight
    from apps.engine.app.use_cases.night_interactor import GameStateError
    _, _, night = _scoring_night(db_session)
    model = _HeldOnce()
    submit = _submitter(db_session, night.id, model)
    outcome = _while_first_is_held(db_session, submit, submit, entered=model.entered, release=model.release)
    assert outcome["first_still_held"]
    assert isinstance(outcome["second"], GameStateError) and isinstance(outcome["second"], RequestInFlight)


def test_resubmit_after_commit_returns_the_stored_result_without_scoring_again(db_session):
    """연결이 끊긴 뒤 재제출 — 커밋된 제출 응답을 그대로 돌려주고 채점 모델을 다시 부르지 않는다 (I2)."""
    import json
    attempt, _, night = _scoring_night(db_session)
    model = _HeldOnce()
    model.release.set()
    submit = _submitter(db_session, night.id, model)
    first = submit()
    assert isinstance(first, dict)
    calls = model.calls
    audits = len([e for e in _events(db_session, attempt.id, "harness_event") if e.role == "evaluator_verdict"])
    again = submit()
    assert again == json.loads(json.dumps(first))
    assert again["night_clue"] == first["night_clue"] and again["intervention_available"]
    db_session.expire_all()
    assert model.calls == calls
    assert len([e for e in _events(db_session, attempt.id, "harness_event") if e.role == "evaluator_verdict"]) == audits
    assert len(_events(db_session, attempt.id, "answer_scored")) == 1
    assert len(_events(db_session, attempt.id, "death")) == 1


def test_submitted_night_without_a_stored_result_stays_409(db_session):
    """과거 데이터 — 저장 응답 없이 제출 완료된 밤은 기존대로 "이미 제출했다" 409, 모델 호출 없음."""
    from apps.engine.app.use_cases.night_interactor import GameStateError
    _, _, night = _scoring_night(db_session)
    night.submitted = True
    db_session.commit()
    model = _HeldOnce()
    model.release.set()
    again = _submitter(db_session, night.id, model)()
    assert isinstance(again, GameStateError) and "이미 제출" in str(again)
    assert model.calls == 0


def test_edit_claims_while_scoring_is_409_and_keeps_the_submitted_claims(db_session):
    """채점 중 청구문 수정 — 밤 행을 기다리다 채점 커밋 뒤 옛 submitted=False로 통과해 답을 덮어쓰지 않는다 (I1·M4)."""
    from apps.engine.adapter.outbound.repositories.game_repository import NightRepository
    from apps.engine.app.ports.output.scene_transaction_port import RequestInFlight
    from apps.engine.dependencies.engine_dependency import get_night_interactor
    _, _, night = _scoring_night(db_session)
    model = _HeldOnce()

    def edit():
        return _own_session(db_session, get_night_interactor, lambda inter: inter.edit_claims(night.id, ["바꾼 문장."]))
    outcome = _while_first_is_held(db_session, _submitter(db_session, night.id, model), edit,
                                   entered=model.entered, release=model.release)
    assert outcome["first_still_held"]
    assert isinstance(outcome["second"], RequestInFlight)
    assert isinstance(outcome["first"], dict)
    stored = NightRepository(db_session).get(night.id)
    assert stored.claims == ["채연이 밥을 남겼다."] and stored.edit_count == 0 and stored.submitted
    late = edit()  # 채점이 끝난 뒤의 수정은 기존대로 거절
    assert "수정은 1회만" in str(late)


def _insert_without_waiting(db_session, row):
    """다른 세션의 외래 키 INSERT — 기다리면 lock_timeout으로 곧바로 실패한다."""
    from sqlalchemy.orm import Session

    def insert():
        with Session(db_session.get_bind()) as session:
            try:
                session.execute(text("SET LOCAL lock_timeout = '2s'"))
                session.add(row())
                session.commit()
                return "inserted"
            except Exception as exc:  # 결과로 비교한다
                session.rollback()
                return exc
    return insert


def test_day_scene_loop_lock_does_not_block_foreign_key_inserts(db_session):
    """낮 장면이 회차 행을 쥔 동안 그 회차를 참조하는 INSERT(밤 정리 등)는 기다리지 않는다 — FOR NO KEY UPDATE (M1)."""
    import threading
    from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm
    from apps.engine.dependencies.engine_dependency import get_loop_interactor
    _, _, _, info = make_day(db_session, [])
    entered, release = threading.Event(), threading.Event()

    def advance():
        def work(inter):
            listed = inter._rules.list

            def held(*args):
                entered.set()
                release.wait(_HOLD_LIMIT)
                return listed(*args)
            inter._rules.list = held
            return inter.advance_beat(info["loop_id"])
        return _own_session(db_session, get_loop_interactor, work)
    insert = _insert_without_waiting(db_session, lambda: NightOrm(loop_id=info["loop_id"], free_text="", claims=[]))
    outcome = _while_first_is_held(db_session, advance, insert, entered=entered, release=release)
    assert outcome["second"] == "inserted" and outcome["first_still_held"]
    assert isinstance(outcome["first"], dict) and outcome["first"]["beat"] == 2


def test_loop_start_attempt_lock_does_not_block_note_inserts(db_session):
    """회차 시작이 판 행을 쥔 동안 다른 세션의 노트 INSERT는 기다리지 않는다 (M4)."""
    from apps.engine.adapter.outbound.orms.game_state_orm import NoteOrm
    from apps.engine.dependencies.engine_dependency import get_loop_interactor
    _, _, attempt, info = make_day(db_session, [])
    LoopRepository(db_session).get(info["loop_id"]).state = "closed"
    db_session.commit()
    model = _HeldOnce()

    def start():
        def work(inter):
            inter._core_llm = model
            return inter.start_loop(attempt.id)
        return _own_session(db_session, get_loop_interactor, work)
    insert = _insert_without_waiting(db_session, lambda: NoteOrm(
        attempt_id=attempt.id, kind="fragment", text="동시 노트", loop_n=1, source_key="probe-concurrent-note"))
    outcome = _while_first_is_held(db_session, start, insert, entered=model.entered, release=model.release)
    assert outcome["second"] == "inserted" and outcome["first_still_held"]
    assert isinstance(outcome["first"], dict) and outcome["first"]["loop_n"] == 2


@pytest.mark.parametrize("module", ["loop_interactor", "night_interactor", "intervention_interactor"])
def test_every_in_flight_error_maps_to_409_with_the_retry_code(module):
    """낮·밤·신의개입의 처리 중 409는 모두 request_in_flight 코드를 단다 (M3)."""
    import importlib
    import json
    from apps.engine.adapter.inbound.api.v1.game_router import _run
    in_flight = importlib.import_module(f"apps.engine.app.use_cases.{module}").RequestInFlight

    def busy():
        raise in_flight("앞 요청을 처리하는 중이다.")
    response = _run(busy)
    assert response.status_code == 409
    assert json.loads(response.body) == {"code": "request_in_flight", "detail": "앞 요청을 처리하는 중이다."}
