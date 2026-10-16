"""이어하기 화면 데이터 — 낮 장면 다시 그리기·회차 껍데기·밤 단계 데이터 (설계 2026-10-16 §2.2)."""

import json
import uuid

from sqlalchemy import func, select

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm, RuleOrm
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    RuleRepository,
)
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION
from apps.engine.dependencies.engine_dependency import get_loop_interactor, get_night_interactor


def _event_count(db_session) -> int:
    db_session.expire_all()
    return db_session.scalar(select(func.count()).select_from(EventLogOrm))


def _scene(lines: list[dict]) -> list[tuple]:
    """대사창 줄 비교용 — 되살리지 않는 지나가는 말(npc)·기록 알림(system)은 뺀다. 되살린 줄은 순서가 달라질 수 있어 정렬한다."""
    return sorted((l["kind"], l["text"], l["observation_id"] or "") for l in lines if l["kind"] not in ("npc", "system"))


def _started(db_session, rules=()):
    loops = get_loop_interactor(db_session)
    attempt = AttemptRepository(db_session).create(None)
    for rule in rules:
        RuleRepository(db_session).add(rule(attempt.id))
    started = loops.start_loop(attempt.id)
    return loops, started, uuid.UUID(started["loop_id"])


def _night_ready(db_session):
    loops, _, loop_id = _started(db_session)
    for _ in range(6):
        loops.advance_beat(loop_id)
    return get_night_interactor(db_session), LoopRepository(db_session).get(loop_id)


# ── 진행 중인 판 ──────────────────────────────────────────────


def test_latest_active_is_the_newest_attempt_only_while_it_is_active(db_session):
    """진행 중인 판 = 가장 최근 판이 active일 때만. 최신 판이 끝나거나 포기되면 오래된 active 판을 다시 잡지 않는다."""
    users, attempts = UserRepository(db_session), AttemptRepository(db_session)
    alice = users.upsert_from_google(GoogleProfileDTO(sub="alice", email="", name="a"))
    bob = users.upsert_from_google(GoogleProfileDTO(sub="bob", email="", name="b"))
    attempts.create(None, user_id=alice.id)  # 이 기능 전에 닫히지 않고 남은 오래된 active 판
    newer = attempts.create(None, user_id=alice.id)
    attempts.create(None, user_id=bob.id)  # 남의 판이 더 최근이어도 alice의 답은 그대로
    assert attempts.latest_active(alice.id).id == newer.id

    for status in ("closed", "abandoned"):
        newest = attempts.create(None, user_id=alice.id)
        newest.status = status
        attempts.save()
        assert attempts.latest_active(alice.id) is None, f"최신 판이 {status}인데 오래된 active 판이 다시 잡혔다"
    assert attempts.latest_active(uuid.uuid4()) is None


# ── 낮 ────────────────────────────────────────────────────────


def test_resume_shell_matches_start_loop_shape_without_scene(db_session):
    loops, started, loop_id = _started(db_session)
    shell = loops.resume_shell(LoopRepository(db_session).get(loop_id))
    assert set(shell) == set(started)
    assert (shell["loop_id"], shell["loop_n"], shell["morning_text"], shell["budget_left"], shell["active_rules"]) == (
        started["loop_id"], 1, started["morning_text"], started["budget_left"], started["active_rules"])
    assert (shell["lines"], shell["observations"], shell["illustrations"]) == ([], [], [])
    assert (shell["ambient"], shell["aftermath"], shell["note_found"], shell["broadcast"]) == (None, None, None, None)


def test_resume_day_redraws_first_scene_without_new_records(db_session):
    loops, started, loop_id = _started(db_session)
    before = _event_count(db_session)
    resumed = loops.resume_day(LoopRepository(db_session).get(loop_id))
    again = loops.resume_day(LoopRepository(db_session).get(loop_id))
    assert _event_count(db_session) == before
    assert resumed == again
    assert _scene(resumed["lines"]) == _scene(started["lines"])
    assert (resumed["beat"], resumed["beat_title"], resumed["budget_left"]) == (1, started["beat_title"], started["budget_left"])
    assert resumed["observations"] == started["observations"]
    assert (resumed["ambient"], resumed["aftermath"], resumed["note_found"]) == (None, None, None)


def test_resume_day_keeps_rule_explanation_lines(db_session):
    """Review Focus 1 — 3비트 설명 규칙이 실행된 뒤 다시 그려도 설명 줄이 남고 기록은 늘지 않는다."""
    explain = lambda attempt_id: RuleOrm(  # noqa: E731
        attempt_id=attempt_id, rule_id="R1", source="user_choice", target="민석", when_beat=3,
        effect="enforce", action=EXPLAIN_ACTION, created_loop=1)
    loops, _, loop_id = _started(db_session, rules=[explain])
    loops.advance_beat(loop_id)
    advanced = loops.advance_beat(loop_id)  # 3비트
    told = [l for l in advanced["lines"] if l["kind"] == "statement" and l["observation_id"].endswith(":rule-3-R1")]
    assert told, "R1 설명이 3비트에 나오지 않았다 — 시나리오 전제(민석 3비트 기회)를 확인한다"
    before = _event_count(db_session)
    resumed = loops.resume_day(LoopRepository(db_session).get(loop_id))
    assert _event_count(db_session) == before
    assert _scene(resumed["lines"]) == _scene(advanced["lines"])
    assert resumed["beat"] == 3


# ── 밤·채점·개입 ──────────────────────────────────────────────


def test_night_resume_view_follows_the_night(db_session):
    nights, loop = _night_ready(db_session)
    assert nights.resume_view(loop) == {
        "night_id": None, "claims": [], "is_question": [], "questions_left": 3, "submit": None}

    draft = nights.draft(loop.id, [], "채연이 밥을 남겼다. 왜 남겼을까?")
    view = nights.resume_view(loop)
    assert (view["night_id"], view["claims"], view["is_question"], view["submit"]) == (
        draft["night_id"], draft["claims"], draft["is_question"], None)

    submitted = nights.submit(uuid.UUID(draft["night_id"]))
    before = _event_count(db_session)
    view = nights.resume_view(loop)
    assert _event_count(db_session) == before  # 저장 응답을 읽기만 한다 — 채점·기록 없음
    assert json.loads(json.dumps(view["submit"])) == json.loads(json.dumps(submitted))

    night = NightRepository(db_session).get(uuid.UUID(draft["night_id"]))
    night.questions_left, night.questions = 1, ["채연이 밥 남겼어?", "누가 방송실에 갔어?"]
    NightRepository(db_session).save()
    view = nights.resume_view(loop)
    assert view["questions_left"] == 1
    assert not set(view["submit"]["suggested_questions"]) & set(night.questions)


def test_submitted_night_without_stored_response_still_resumes(db_session):
    """Review Focus 4 — 응답 저장(2026-09-18) 전 제출: answer_scored 응답이 없어도 개입 화면이 쓸 점수가 있다."""
    nights, loop = _night_ready(db_session)
    NightRepository(db_session).create(NightOrm(loop_id=loop.id, claims=["채연이 밥을 남겼다."],
                                                submitted=True, total=42.0, passed=False))
    loop.state = "intervention"
    LoopRepository(db_session).save()
    submit = nights.resume_view(loop)["submit"]
    assert (submit["total"], submit["loop_n"], submit["is_final"], submit["intervention_available"]) == (42.0, 1, False, True)
    assert isinstance(submit["suggested_questions"], list)
