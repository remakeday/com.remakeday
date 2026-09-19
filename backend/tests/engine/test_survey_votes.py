"""클리어 화면 플레이 평가 — 판당 한 표, 부분 응답, 건너뛰기 기록."""

import uuid

import pytest
import sqlalchemy.exc
from sqlalchemy import text

from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    SurveyVoteRepository,
)

FULL = {"fun": 5, "novelty": 4, "ai_agency": 5, "polish": 3, "recommend": 4}
EMPTY = {"fun": None, "novelty": None, "ai_agency": None, "polish": None, "recommend": None}


def _attempt(db_session, user_id=None):
    return AttemptRepository(db_session).create(None, user_id=user_id)


def test_first_vote_is_recorded(db_session):
    user_id = uuid.uuid4()
    attempt = _attempt(db_session, user_id)
    repo = SurveyVoteRepository(db_session)
    assert repo.record(attempt.id, user_id, skipped=False, scores=FULL) is True
    row = db_session.execute(
        text("select fun, recommend, skipped, user_id from survey_votes where attempt_id = :a"),
        {"a": attempt.id},
    ).one()
    assert (row.fun, row.recommend, row.skipped, row.user_id) == (5, 4, False, user_id)


def test_second_vote_on_same_attempt_is_ignored(db_session):
    attempt = _attempt(db_session)
    repo = SurveyVoteRepository(db_session)
    assert repo.record(attempt.id, None, skipped=False, scores=FULL) is True
    assert repo.record(attempt.id, None, skipped=False, scores={**FULL, "fun": 1}) is False
    kept = db_session.execute(
        text("select fun from survey_votes where attempt_id = :a"), {"a": attempt.id}
    ).scalar_one()
    assert kept == 5  # 첫 표가 유효하다


def test_partial_answer_keeps_blanks_as_null(db_session):
    attempt = _attempt(db_session)
    partial = {**EMPTY, "fun": 4, "recommend": 2}
    assert SurveyVoteRepository(db_session).record(attempt.id, None, skipped=False, scores=partial) is True
    row = db_session.execute(
        text("select fun, novelty, recommend from survey_votes where attempt_id = :a"),
        {"a": attempt.id},
    ).one()
    assert (row.fun, row.novelty, row.recommend) == (4, None, 2)


def test_skip_is_recorded_as_its_own_row(db_session):
    attempt = _attempt(db_session)
    assert SurveyVoteRepository(db_session).record(attempt.id, None, skipped=True, scores=EMPTY) is True
    row = db_session.execute(
        text("select skipped, fun from survey_votes where attempt_id = :a"), {"a": attempt.id}
    ).one()
    assert (row.skipped, row.fun) == (True, None)


@pytest.mark.parametrize("bad", [0, 6, -1])
def test_score_outside_one_to_five_is_rejected_by_the_database(db_session, bad):
    attempt = _attempt(db_session)
    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc:
        SurveyVoteRepository(db_session).record(
            attempt.id, None, skipped=False, scores={**EMPTY, "fun": bad}
        )
    assert "ck_survey_votes_fun" in str(exc.value)
    db_session.rollback()


def test_skipped_row_may_not_carry_scores(db_session):
    attempt = _attempt(db_session)
    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc:
        SurveyVoteRepository(db_session).record(
            attempt.id, None, skipped=True, scores={**EMPTY, "fun": 3}
        )
    assert "ck_survey_votes_skip_consistency" in str(exc.value)
    db_session.rollback()


def test_unskipped_row_needs_at_least_one_score(db_session):
    attempt = _attempt(db_session)
    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc:
        SurveyVoteRepository(db_session).record(attempt.id, None, skipped=False, scores=EMPTY)
    assert "ck_survey_votes_skip_consistency" in str(exc.value)
    db_session.rollback()
